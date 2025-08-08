"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Progress Tracking Service für MineSearch v2 - Real-time Fortschrittsanzeige
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class SearchStatus(Enum):
    """Status-Enumeration für Suchvorgänge"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SearchOperation:
    """Einzelner Suchvorgang (Mine + Modell Kombination)"""
    id: str
    mine_name: str
    model: str
    status: SearchStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None

@dataclass
class ProgressUpdate:
    """Progress Update für WebSocket-Übertragung"""
    session_id: str
    current: int
    total: int
    percentage: float
    current_mine: Optional[str]
    current_model: Optional[str]
    eta_seconds: Optional[int]
    completed_operations: List[str]
    failed_operations: List[str]
    status: str
    timestamp: datetime
    total_duration_seconds: Optional[float] = None
    average_duration_per_operation: Optional[float] = None

class ProgressTracker:
    """
    Progress Tracking Service für MineSearch v2
    
    Mathematik-Grundlage (wie vom User spezifiziert):
    - 10 Minen × 10 Modelle = 100 Suchvorgänge = 100%
    - 1 Mine × 1 Modell = 1 Suchvorgang = 1%
    - 1 Mine × 10 Modelle = 10 Suchvorgänge = 10%
    - Progress = (completed_searches / total_searches) * 100
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, List] = {}
        self._lock = asyncio.Lock()
    
    def create_session(self, mines: List[str], models: List[str], session_id: Optional[str] = None) -> str:
        """
        Erstelle neue Progress-Session
        
        Args:
            mines: Liste der zu suchenden Minen
            models: Liste der zu verwendenden Modelle
            session_id: Optional - spezifische Session-ID
            
        Returns:
            session_id: Eindeutige Session-ID
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Erstelle alle Suchoperationen (Mine × Modell Kombinationen)
        operations = []
        for mine in mines:
            for model in models:
                operation = SearchOperation(
                    id=f"{mine}_{model}_{len(operations)}",
                    mine_name=mine,
                    model=model,
                    status=SearchStatus.PENDING
                )
                operations.append(operation)
        
        session_data = {
            'session_id': session_id,
            'mines': mines,
            'models': models,
            'operations': operations,
            'total_operations': len(operations),
            'completed_operations': 0,
            'failed_operations': 0,
            'started_at': datetime.now(),
            'completed_at': None,
            'status': 'initialized'
        }
        
        self.sessions[session_id] = session_data
        self.websocket_connections[session_id] = []
        
        logger.info(f"Progress session created: {session_id} - {len(mines)} mines × {len(models)} models = {len(operations)} operations")
        
        return session_id
    
    async def start_operation(self, session_id: str, mine_name: str, model: str):
        """Starte eine spezifische Suchoperation"""
        async with self._lock:
            if session_id not in self.sessions:
                logger.error(f"Session {session_id} not found")
                return
            
            session = self.sessions[session_id]
            
            # Finde die entsprechende Operation
            operation = None
            for op in session['operations']:
                if op.mine_name == mine_name and op.model == model and op.status == SearchStatus.PENDING:
                    operation = op
                    break
            
            if not operation:
                logger.error(f"Operation not found: {mine_name} + {model} in session {session_id}")
                return
            
            # Markiere als laufend
            operation.status = SearchStatus.RUNNING
            operation.started_at = datetime.now()
            
            # Update Session-Status
            if session['status'] == 'initialized':
                session['status'] = 'running'
            
            logger.info(f"Started operation: {mine_name} + {model} (Session: {session_id})")
            
            # Sende Progress Update
            await self._send_progress_update(session_id)
    
    async def complete_operation(self, session_id: str, mine_name: str, model: str, success: bool = True, error_message: Optional[str] = None):
        """Markiere eine Suchoperation als abgeschlossen"""
        async with self._lock:
            if session_id not in self.sessions:
                logger.error(f"Session {session_id} not found")
                return
            
            session = self.sessions[session_id]
            
            # CRITICAL FIX: Find operation with flexible status matching
            # Try RUNNING first, then PENDING as fallback (race condition fix)
            operation = None
            for op in session['operations']:
                if op.mine_name == mine_name and op.model == model:
                    if op.status == SearchStatus.RUNNING:
                        operation = op
                        break
                    elif op.status == SearchStatus.PENDING and operation is None:
                        # Fallback for race condition - operation completed before start_operation was called
                        operation = op
                        logger.warning(f"Found PENDING operation instead of RUNNING: {mine_name} + {model} (race condition)")
            
            if not operation:
                logger.error(f"No operation found for completion: {mine_name} + {model} in session {session_id}")
                # Don't return - this is not critical enough to break the whole batch
                logger.info(f"Available operations in session {session_id}: {[(op.mine_name, op.model, op.status.value) for op in session['operations']]}")
                return
            
            # Markiere als abgeschlossen
            operation.status = SearchStatus.COMPLETED if success else SearchStatus.FAILED
            operation.completed_at = datetime.now()
            operation.error_message = error_message
            
            # Berechne Dauer
            if operation.started_at:
                operation.duration_seconds = (operation.completed_at - operation.started_at).total_seconds()
            
            # Update Session-Counters
            if success:
                session['completed_operations'] += 1
            else:
                session['failed_operations'] += 1
            
            logger.info(f"Completed operation: {mine_name} + {model} (Success: {success}, Session: {session_id})")
            
            # Prüfe ob alle Operationen abgeschlossen
            total_finished = session['completed_operations'] + session['failed_operations']
            if total_finished >= session['total_operations']:
                session['status'] = 'completed'
                session['completed_at'] = datetime.now()
                logger.info(f"Session {session_id} completed - {session['completed_operations']} successful, {session['failed_operations']} failed")
            
            # Sende Progress Update
            await self._send_progress_update(session_id)
    
    def get_progress(self, session_id: str) -> Optional[ProgressUpdate]:
        """Hole aktuellen Progress für Session"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # KRITISCHE MATHEMATIK (wie vom User spezifiziert):
        # Progress = (completed_searches / total_searches) * 100
        completed = session['completed_operations']
        total = session['total_operations']
        percentage = (completed / total * 100) if total > 0 else 0
        
        # Aktuell laufende Operation finden
        current_mine = None
        current_model = None
        for op in session['operations']:
            if op.status == SearchStatus.RUNNING:
                current_mine = op.mine_name
                current_model = op.model
                break
        
        # ETA-Berechnung basierend auf durchschnittlicher Operationsdauer
        eta_seconds = None
        avg_duration = None
        if completed > 0:
            # Berechne durchschnittliche Dauer abgeschlossener Operationen
            completed_ops = [op for op in session['operations'] if op.status in [SearchStatus.COMPLETED, SearchStatus.FAILED] and op.duration_seconds]
            if completed_ops:
                avg_duration = sum(op.duration_seconds for op in completed_ops) / len(completed_ops)
                remaining_operations = total - completed - session['failed_operations']
                eta_seconds = int(avg_duration * remaining_operations) if remaining_operations > 0 else 0
        
        # Completed/Failed Operation IDs
        completed_operations = [f"{op.mine_name}+{op.model}" for op in session['operations'] if op.status == SearchStatus.COMPLETED]
        failed_operations = [f"{op.mine_name}+{op.model}" for op in session['operations'] if op.status == SearchStatus.FAILED]
        
        # Total Session Duration
        total_duration = None
        if session['completed_at']:
            total_duration = (session['completed_at'] - session['started_at']).total_seconds()
        
        return ProgressUpdate(
            session_id=session_id,
            current=completed,
            total=total,
            percentage=round(percentage, 1),
            current_mine=current_mine,
            current_model=current_model,
            eta_seconds=eta_seconds,
            completed_operations=completed_operations,
            failed_operations=failed_operations,
            status=session['status'],
            timestamp=datetime.now(),
            total_duration_seconds=total_duration,
            average_duration_per_operation=avg_duration
        )
    
    async def add_websocket_connection(self, session_id: str, websocket):
        """Füge WebSocket-Verbindung für Session hinzu"""
        if session_id not in self.websocket_connections:
            self.websocket_connections[session_id] = []
        
        self.websocket_connections[session_id].append(websocket)
        logger.info(f"WebSocket connected to session {session_id}")
        
        # CRITICAL FIX: Warte kurz bevor Progress Update gesendet wird
        # Das verhindert Race Condition zwischen Connection und Progress Send
        await asyncio.sleep(0.1)
        
        # Sende aktuellen Progress sofort - mit Exception Handling
        try:
            await self._send_progress_update(session_id)
        except Exception as e:
            logger.error(f"Failed to send initial progress update: {e}")
    
    async def remove_websocket_connection(self, session_id: str, websocket):
        """Entferne WebSocket-Verbindung"""
        if session_id in self.websocket_connections:
            try:
                self.websocket_connections[session_id].remove(websocket)
                logger.info(f"WebSocket disconnected from session {session_id}")
            except ValueError:
                pass  # WebSocket war nicht in der Liste
    
    async def _send_progress_update(self, session_id: str):
        """Sende Progress Update an alle verbundenen WebSockets"""
        if session_id not in self.websocket_connections:
            logger.debug(f"No WebSocket connections for session {session_id}")
            return
        
        progress = self.get_progress(session_id)
        if not progress:
            logger.debug(f"No progress data for session {session_id}")
            return
        
        # Konvertiere zu JSON-serialisierbarem Format
        progress_data = asdict(progress)
        progress_data['timestamp'] = progress.timestamp.isoformat()
        
        message = json.dumps({
            'type': 'progress_update',
            'data': progress_data
        })
        
        # Sende an alle verbundenen WebSockets (mit detailliertem Error Handling)
        connections_to_remove = []
        websockets = self.websocket_connections[session_id].copy()  # Kopie für sichere Iteration
        
        for i, websocket in enumerate(websockets):
            try:
                # Prüfe WebSocket-Status vor Send
                if hasattr(websocket, 'client_state') and websocket.client_state.name != 'CONNECTED':
                    logger.warning(f"WebSocket {i} not connected (state: {websocket.client_state.name})")
                    connections_to_remove.append(websocket)
                    continue
                
                await websocket.send_text(message)
                logger.debug(f"Progress update sent to WebSocket {i} for session {session_id}")
                
            except Exception as e:
                error_type = type(e).__name__
                logger.error(f"Failed to send progress update to WebSocket {i}: {error_type} - {e}")
                connections_to_remove.append(websocket)
        
        # Entferne fehlerhafte Verbindungen
        for websocket in connections_to_remove:
            await self.remove_websocket_connection(session_id, websocket)
            
        # Log final status
        remaining_connections = len(self.websocket_connections.get(session_id, []))
        logger.info(f"Progress update completed: {session_id} - {remaining_connections} active connections")
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Bereinige alte Sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            session_age = current_time - session['started_at']
            if session_age > timedelta(hours=max_age_hours):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Hole Session-Informationen"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'mines_count': len(session['mines']),
            'models_count': len(session['models']),
            'total_operations': session['total_operations'],
            'completed_operations': session['completed_operations'],
            'failed_operations': session['failed_operations'],
            'status': session['status'],
            'started_at': session['started_at'].isoformat(),
            'completed_at': session['completed_at'].isoformat() if session['completed_at'] else None
        }
    
    # COMPATIBILITY METHODS: Legacy API support for batch.py
    async def update_progress(self, session_id: str, current: int, message: str, mine_name: str, models: str):
        """Legacy method for batch.py compatibility - updates progress manually"""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found for update_progress")
            return
        
        async with self._lock:
            session = self.sessions[session_id]
            
            # Update counters manually
            session['completed_operations'] = current
            session['status'] = 'running'
            
            logger.info(f"Progress updated: {session_id} - {current}/{session['total_operations']} - {message}")
            
            # Send WebSocket update
            await self._send_progress_update(session_id)
    
    async def complete_search(self, session_id: str, mine_name: str, success_count: int):
        """Legacy method for batch.py compatibility - marks search as completed"""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found for complete_search")
            return
        
        async with self._lock:
            session = self.sessions[session_id]
            session['status'] = 'completed'
            session['completed_at'] = datetime.now()
            session['completed_operations'] = success_count
            
            logger.info(f"Search completed: {session_id} - {mine_name} - {success_count} successes")
            
            # Send final WebSocket update
            await self._send_progress_update(session_id)
    
    async def error_search(self, session_id: str, error_message: str, mine_name: str):
        """Legacy method for batch.py compatibility - marks search as failed"""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found for error_search")
            return
        
        async with self._lock:
            session = self.sessions[session_id]
            session['status'] = 'failed'
            session['completed_at'] = datetime.now()
            session['failed_operations'] += 1
            
            logger.error(f"Search failed: {session_id} - {mine_name} - {error_message}")
            
            # Send error WebSocket update
            await self._send_progress_update(session_id)
    
    def create_session_legacy(self, mine_name: str, total_steps: int) -> str:
        """Legacy create_session method for batch.py compatibility"""
        # Convert single mine_name to list, create dummy models
        mines = [mine_name] if mine_name else ["Batch Operation"]
        models = ["batch:operation"] * max(1, total_steps // len(mines) if mines else 1)
        
        logger.info(f"Legacy create_session: {mine_name} -> {len(mines)} mines, {len(models)} models")
        return self.create_session(mines, models)

# Global Progress Tracker Instance
progress_tracker = ProgressTracker()