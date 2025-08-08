"""
Author: rahn
Datum: 06.08.2025
Version: 1.0
Beschreibung: Vereinfachter Progress Tracker - Phase 1.2 Rescue Plan
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

logger = logging.getLogger(__name__)

class SimpleProgressTracker:
    """
    PHASE 1.2 EMERGENCY SIMPLIFICATION: Ultra-simple progress tracking
    
    Eliminiert alle komplexen Zustandsmaschinen und Race Conditions.
    Verwendet nur einfache Zähler und defensive Programmierung.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, List] = {}
        self._lock = asyncio.Lock()
        logger.info("SimpleProgressTracker initialized - emergency simple mode")
    
    def create_session(self, total_operations: int, session_id: Optional[str] = None) -> str:
        """
        SIMPLIFIED: Creates session with just a total count
        
        Args:
            total_operations: Total number of operations expected
            session_id: Optional session ID
            
        Returns:
            session_id: Unique session ID
        """
        try:
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # ULTRA SIMPLE SESSION DATA
            session_data = {
                'session_id': session_id,
                'total': max(1, int(total_operations)),  # Defensive: at least 1
                'completed': 0,
                'failed': 0,
                'status': 'running',
                'current_operation': '',
                'started_at': datetime.now().isoformat(),
                'last_update': datetime.now().isoformat()
            }
            
            self.sessions[session_id] = session_data
            self.websocket_connections[session_id] = []
            
            logger.info(f"Simple session created: {session_id} - {total_operations} operations")
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating simple session: {e}")
            # DEFENSIVE: Return emergency session
            emergency_id = f"emergency_{int(datetime.now().timestamp())}"
            self.sessions[emergency_id] = {
                'session_id': emergency_id,
                'total': 1,
                'completed': 0,
                'failed': 0,
                'status': 'running',
                'current_operation': 'Emergency Session',
                'started_at': datetime.now().isoformat(),
                'last_update': datetime.now().isoformat()
            }
            return emergency_id
    
    async def increment_progress(self, session_id: str, operation_name: str = "", success: bool = True):
        """
        SIMPLIFIED: Just increment counters
        
        Args:
            session_id: Session ID
            operation_name: Name of current operation
            success: Whether operation was successful
        """
        try:
            async with self._lock:
                if session_id not in self.sessions:
                    logger.warning(f"Session {session_id} not found - creating emergency session")
                    # DEFENSIVE: Create emergency session
                    self.sessions[session_id] = {
                        'session_id': session_id,
                        'total': 100,  # Default assumption
                        'completed': 0,
                        'failed': 0,
                        'status': 'running',
                        'current_operation': operation_name,
                        'started_at': datetime.now().isoformat(),
                        'last_update': datetime.now().isoformat()
                    }
                
                session = self.sessions[session_id]
                
                # SIMPLE COUNTER INCREMENT
                if success:
                    session['completed'] += 1
                else:
                    session['failed'] += 1
                
                session['current_operation'] = operation_name[:100]  # Defensive: limit length
                session['last_update'] = datetime.now().isoformat()
                
                # Check if completed
                total_processed = session['completed'] + session['failed']
                if total_processed >= session['total']:
                    session['status'] = 'completed'
                
                logger.info(f"Progress updated: {session_id} - {session['completed']}/{session['total']}")
                
                # Send WebSocket update with error handling
                await self._safe_send_websocket_update(session_id)
                
        except Exception as e:
            logger.error(f"Error incrementing progress for {session_id}: {e}")
            # DEFENSIVE: Don't crash, just log
    
    def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        SIMPLIFIED: Get basic progress data
        
        Args:
            session_id: Session ID
            
        Returns:
            Simple progress dict or None
        """
        try:
            if session_id not in self.sessions:
                logger.warning(f"Session {session_id} not found for progress")
                return None
            
            session = self.sessions[session_id]
            
            # SIMPLE CALCULATION
            total = max(1, session['total'])  # Defensive: avoid division by zero
            completed = session['completed']
            percentage = min(100.0, (completed / total) * 100)  # Defensive: cap at 100%
            
            return {
                'session_id': session_id,
                'total': total,
                'completed': completed,
                'failed': session['failed'],
                'percentage': round(percentage, 1),
                'status': session['status'],
                'current_operation': session.get('current_operation', ''),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting progress for {session_id}: {e}")
            # DEFENSIVE: Return minimal progress
            return {
                'session_id': session_id,
                'total': 1,
                'completed': 0,
                'failed': 0,
                'percentage': 0.0,
                'status': 'error',
                'current_operation': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def add_websocket_connection(self, session_id: str, websocket):
        """
        SIMPLIFIED: Add WebSocket with defensive error handling
        
        Args:
            session_id: Session ID
            websocket: WebSocket connection
        """
        try:
            if session_id not in self.websocket_connections:
                self.websocket_connections[session_id] = []
            
            self.websocket_connections[session_id].append(websocket)
            logger.info(f"WebSocket added to simple session {session_id}")
            
            # Send initial progress immediately with error handling
            await self._safe_send_websocket_update(session_id)
            
        except Exception as e:
            logger.error(f"Error adding WebSocket to {session_id}: {e}")
            # DEFENSIVE: Don't crash, just log
    
    async def remove_websocket_connection(self, session_id: str, websocket):
        """
        SIMPLIFIED: Remove WebSocket with defensive error handling
        
        Args:
            session_id: Session ID
            websocket: WebSocket connection
        """
        try:
            if session_id in self.websocket_connections:
                try:
                    self.websocket_connections[session_id].remove(websocket)
                    logger.info(f"WebSocket removed from simple session {session_id}")
                except ValueError:
                    # WebSocket wasn't in list - that's fine
                    pass
                    
        except Exception as e:
            logger.error(f"Error removing WebSocket from {session_id}: {e}")
            # DEFENSIVE: Don't crash, just log
    
    async def _safe_send_websocket_update(self, session_id: str):
        """
        SIMPLIFIED: Send WebSocket update with maximum error protection
        
        Args:
            session_id: Session ID
        """
        try:
            if session_id not in self.websocket_connections:
                return
            
            progress = self.get_progress(session_id)
            if not progress:
                return
            
            # SIMPLE MESSAGE
            message = json.dumps({
                'type': 'progress_update',
                'data': progress
            })
            
            # Send to all connections with individual error handling
            connections = self.websocket_connections[session_id].copy()  # Safe copy
            failed_connections = []
            
            for websocket in connections:
                try:
                    # Check connection state if possible
                    if hasattr(websocket, 'client_state'):
                        if websocket.client_state.name != 'CONNECTED':
                            failed_connections.append(websocket)
                            continue
                    
                    # Try to send
                    await websocket.send_text(message)
                    
                except Exception as ws_error:
                    logger.debug(f"WebSocket send failed: {ws_error}")
                    failed_connections.append(websocket)
            
            # Clean up failed connections
            for failed_ws in failed_connections:
                await self.remove_websocket_connection(session_id, failed_ws)
            
            active_connections = len(self.websocket_connections.get(session_id, []))
            logger.debug(f"WebSocket update sent to {session_id}: {active_connections} active connections")
            
        except Exception as e:
            logger.error(f"Error in safe WebSocket send for {session_id}: {e}")
            # DEFENSIVE: Never crash on WebSocket errors
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """
        SIMPLIFIED: Clean old sessions with error handling
        
        Args:
            max_age_hours: Maximum age in hours
        """
        try:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in self.sessions.items():
                try:
                    started_str = session.get('started_at', '')
                    if not started_str:
                        continue
                    
                    started_time = datetime.fromisoformat(started_str.replace('Z', '+00:00'))
                    age_hours = (current_time - started_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        sessions_to_remove.append(session_id)
                        
                except Exception as parse_error:
                    logger.debug(f"Error parsing session time for {session_id}: {parse_error}")
                    # DEFENSIVE: Leave session if we can't parse time
            
            # Remove old sessions
            for session_id in sessions_to_remove:
                try:
                    del self.sessions[session_id]
                    if session_id in self.websocket_connections:
                        del self.websocket_connections[session_id]
                    logger.info(f"Cleaned up old simple session: {session_id}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning session {session_id}: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"Error in cleanup_old_sessions: {e}")
            # DEFENSIVE: Never crash on cleanup

# Global instance
simple_progress_tracker = SimpleProgressTracker()