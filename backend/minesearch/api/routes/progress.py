"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: FastAPI WebSocket Endpoints für Real-time Progress Updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import json
from typing import Optional, Dict, Any

# PROGRESS-FIX 29.08.2025: Verwende BatchProgressManager
try:
    from minesearch.batch_progress_manager import batch_progress_manager
except ImportError:
    # Fallback: Simple in-memory tracker
    class SimpleProgressTracker:
        def __init__(self):
            self.sessions = {}
            self.websocket_connections = {}
    
    batch_progress_manager = None
    
try:
    from simple_progress_tracker import simple_progress_tracker
except ImportError:
    # Fallback: Simple in-memory tracker
    import uuid
    from datetime import datetime, timedelta
    
    class SimpleProgressTracker:
        def __init__(self):
            self.sessions = {}
            self.websocket_connections = {}
            
        def create_session(self, total_operations):
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = {
                'total': total_operations,
                'completed': 0,
                'failed': 0,
                'status': 'running',
                'created_at': datetime.utcnow(),
                'mines': {}
            }
            return session_id
            
        def get_progress(self, session_id):
            return self.sessions.get(session_id, None)
            
        async def increment_progress(self, session_id, operation_key, success=True):
            if session_id in self.sessions:
                if success:
                    self.sessions[session_id]['completed'] += 1
                else:
                    self.sessions[session_id]['failed'] += 1
                    
        async def add_websocket_connection(self, session_id, websocket):
            if session_id not in self.websocket_connections:
                self.websocket_connections[session_id] = []
            self.websocket_connections[session_id].append(websocket)
            
        async def remove_websocket_connection(self, session_id, websocket):
            if session_id in self.websocket_connections:
                try:
                    self.websocket_connections[session_id].remove(websocket)
                    if not self.websocket_connections[session_id]:
                        del self.websocket_connections[session_id]
                except ValueError:
                    pass
                    
        def cleanup_old_sessions(self, max_age_hours=24):
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            old_sessions = [
                sid for sid, data in self.sessions.items()
                if data.get('created_at', datetime.utcnow()) < cutoff
            ]
            for sid in old_sessions:
                if sid in self.sessions:
                    del self.sessions[sid]
                if sid in self.websocket_connections:
                    del self.websocket_connections[sid]
            return len(old_sessions)
    
    simple_progress_tracker = SimpleProgressTracker()

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/progress/{session_id}")
async def websocket_progress_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket-Endpoint für Real-time Progress Updates
    
    Usage:
    - Frontend connectet zu: ws://localhost:8000/ws/search-progress/{session_id}
    - Empfängt Progress Updates in JSON Format
    - Automatisches Cleanup bei Disconnect
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session: {session_id}")
    
    try:
        # Füge WebSocket zu Session hinzu
        await simple_progress_tracker.add_websocket_connection(session_id, websocket)
        
        # Halte Verbindung aufrecht und warte auf Nachrichten
        while True:
            try:
                # Warte auf Client-Nachrichten (Ping, etc.)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    # Antworte mit Pong + aktueller Progress
                    progress = simple_progress_tracker.get_progress(session_id)
                    if progress:
                        pong_response = {
                            'type': 'pong',
                            'data': progress
                        }
                        await websocket.send_text(json.dumps(pong_response))
                    else:
                        await websocket.send_text(json.dumps({'type': 'pong', 'error': 'Session not found'}))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from WebSocket client: {session_id}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
    finally:
        # Cleanup WebSocket connection
        await simple_progress_tracker.remove_websocket_connection(session_id, websocket)
        logger.info(f"WebSocket cleanup completed for session: {session_id}")

class ProgressSessionRequest(BaseModel):
    mines: list[Dict[str, Any]]  # Frontend sendet mines als Dict-Array
    models: list[str]

@router.post("/progress/create-session")
async def create_progress_session(request: ProgressSessionRequest):
    """
    Erstelle neue Progress-Session
    
    Args:
        request: ProgressSessionRequest mit mines und models
        
    Returns:
        JSON mit session_id und Session-Informationen
    """
    try:
        if not request.mines or not request.models:
            raise HTTPException(status_code=400, detail="Mines and models are required")
        
        # Extrahiere Mine-Namen aus den Mine-Objekten
        mine_names = []
        for mine in request.mines:
            if isinstance(mine, dict):
                mine_name = mine.get('mine_name') or mine.get('name', f'Mine {len(mine_names)+1}')
            else:
                mine_name = str(mine)
            mine_names.append(mine_name)
        
        # PHASE 1.2 SIMPLIFIED: Create session with total operations count
        total_operations = len(mine_names) * len(request.models)
        session_id = simple_progress_tracker.create_session(total_operations)
        
        # Simple session info
        session_info = {
            'session_id': session_id,
            'mines_count': len(mine_names),
            'models_count': len(request.models),
            'total_operations': total_operations,
            'status': 'running'
        }
        
        return JSONResponse(content={
            'success': True,
            'session_id': session_id,
            'session_info': session_info,
            'total_operations': len(mine_names) * len(request.models),
            'mines_count': len(mine_names),
            'models_count': len(request.models),
            'websocket_url': f'/ws/search-progress/{session_id}'
        })
        
    except Exception as e:
        logger.error(f"Error creating progress session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{session_id}")
async def get_progress_status(session_id: str):
    """
    Hole aktuellen Progress-Status für Session (REST API)
    
    Args:
        session_id: Session-Identifier
        
    Returns:
        JSON mit aktuellem Progress-Status
    """
    try:
        # PROGRESS-FIX 29.08.2025: Versuche beide Progress Manager
        progress = None
        
        # Versuche zuerst batch_progress_manager
        if batch_progress_manager:
            try:
                progress = batch_progress_manager.get_progress(session_id)
                if progress:
                    logger.debug(f"Found session in batch_progress_manager: {session_id}")
            except Exception as e:
                logger.debug(f"Error in batch_progress_manager: {e}")
        
        # Falls nicht gefunden, versuche simple_progress_tracker
        if not progress:
            progress = simple_progress_tracker.get_progress(session_id)
            if progress:
                logger.debug(f"Found session in simple_progress_tracker: {session_id}")
        
        # IMMER fallback verwenden, wenn keine Session gefunden
        if not progress:
            logger.info(f"Session {session_id} not found in any tracker, returning completed fallback")
            # Fallback-Progress für unbekannte Sessions - als "completed" markiert
            progress = {
                'total': 1,
                'completed': 1,  # Als "abgeschlossen" markieren, damit Frontend stoppt
                'failed': 0,
                'status': 'completed',  # Status auf completed setzen
                'mines': {},
                'session_id': session_id,
                'message': 'Session not found - batch likely completed'
            }
        
        return JSONResponse(content={
            'success': True,
            'data': progress
        })
        
    except Exception as e:
        logger.error(f"Error getting progress status: {e}")
        # Auch bei Exceptions einen Fallback zurückgeben
        return JSONResponse(content={
            'success': True,
            'data': {
                'total': 1,
                'completed': 1,
                'failed': 0,
                'status': 'completed',
                'mines': {},
                'session_id': session_id,
                'message': f'Error occurred, returning fallback: {str(e)}'
            }
        })

@router.get("/progress/{session_id}/info")
async def get_session_info(session_id: str):
    """
    Hole Session-Informationen
    
    Args:
        session_id: Session-Identifier
        
    Returns:
        JSON mit Session-Metadaten
    """
    try:
        # PHASE 1.2 SIMPLIFIED: Check if session exists
        progress = simple_progress_tracker.get_progress(session_id)
        if not progress:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Return minimal session info
        session_info = {
            'session_id': session_id,
            'total': progress.get('total', 0),
            'completed': progress.get('completed', 0),
            'failed': progress.get('failed', 0),
            'status': progress.get('status', 'unknown')
        }
        
        return JSONResponse(content={
            'success': True,
            'data': session_info
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/progress/{session_id}/start-operation")
async def start_operation(session_id: str, mine_name: str, model: str):
    """
    PHASE 1.2 SIMPLIFIED: Start operation (no-op, just log)
    
    Args:
        session_id: Session-Identifier
        mine_name: Name der Mine
        model: Modell-Identifier
    """
    try:
        logger.info(f"Operation start (simplified): {mine_name} + {model}")
        
        return JSONResponse(content={
            'success': True,
            'message': f'Operation logged: {mine_name} + {model}'
        })
        
    except Exception as e:
        logger.error(f"Error starting operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/progress/{session_id}/complete-operation")
async def complete_operation(
    session_id: str, 
    mine_name: str, 
    model: str, 
    success: bool = True, 
    error_message: Optional[str] = None
):
    """
    PHASE 1.2 SIMPLIFIED: Complete operation using simplified progress tracker
    
    Args:
        session_id: Session-Identifier
        mine_name: Name der Mine
        model: Modell-Identifier
        success: Ob die Operation erfolgreich war
        error_message: Optional - Fehlermeldung bei Fehlschlag
    """
    try:
        await simple_progress_tracker.increment_progress(
            session_id, f"{mine_name} + {model}", success
        )
        
        return JSONResponse(content={
            'success': True,
            'message': f'Operation completed: {mine_name} + {model} (Success: {success})'
        })
        
    except Exception as e:
        logger.error(f"Error completing operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/progress/{session_id}")
async def cleanup_session(session_id: str):
    """
    Bereinige Progress-Session
    
    Args:
        session_id: Session-Identifier
    """
    try:
        # PHASE 1.2 SIMPLIFIED: Clean up session from simple tracker
        if session_id in simple_progress_tracker.sessions:
            del simple_progress_tracker.sessions[session_id]
        
        if session_id in simple_progress_tracker.websocket_connections:
            # Schließe alle WebSocket-Verbindungen
            for websocket in simple_progress_tracker.websocket_connections[session_id]:
                try:
                    await websocket.close()
                except ConnectionError as e:
                    logger.debug(f"[PROGRESS] WebSocket bereits geschlossen: {e}")
                except RuntimeError as e:
                    logger.debug(f"[PROGRESS] WebSocket Runtime-Error beim Schließen: {e}")
                except Exception as e:
                    logger.warning(f"[PROGRESS] Unerwarteter Fehler beim Schließen der WebSocket: {e}")
            del simple_progress_tracker.websocket_connections[session_id]
        
        return JSONResponse(content={
            'success': True,
            'message': f'Session {session_id} cleaned up'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/progress/cleanup-old-sessions")
async def cleanup_old_sessions(max_age_hours: int = Query(24, ge=1, le=168)):
    """
    Bereinige alte Sessions
    
    Args:
        max_age_hours: Maximales Alter der Sessions in Stunden (1-168)
    """
    try:
        simple_progress_tracker.cleanup_old_sessions(max_age_hours)
        
        return JSONResponse(content={
            'success': True,
            'message': f'Old sessions cleaned up (older than {max_age_hours} hours)'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up old sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))