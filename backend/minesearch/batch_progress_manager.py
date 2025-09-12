"""
Author: rahn
Datum: 29.08.2025
Version: 1.0
Beschreibung: Zentraler Progress Manager für detaillierte Batch-Suche Fortschrittsverfolgung
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class ProgressState(Enum):
    """Definierte Progress-States für Batch-Suche"""
    UPLOADING = "uploading"
    PROCESSING_CSV = "processing_csv"
    # 2-PHASEN WORKFLOW STATES (29.08.2025)
    COLLECTING_SOURCES = "collecting_sources"    # PHASE 1: Sammle Quellen von allen Modellen
    EXTRACTING_DATA = "extracting_data"          # PHASE 2: Extrahiere Daten mit allen Quellen
    # Legacy States (für Fallback-Kompatibilität)
    SOURCE_DISCOVERY = "source_discovery"
    MODEL_EXECUTION = "model_execution"
    SAVING_RESULTS = "saving_results"
    MINE_COMPLETE = "mine_complete"
    BATCH_COMPLETE = "batch_complete"
    ERROR = "error"

@dataclass
class ProgressUpdate:
    """Einzelnes Progress-Update"""
    state: ProgressState
    message: str
    mine_current: int = 0
    mine_total: int = 0
    model_current: int = 0
    model_total: int = 0
    sources_found: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        """__post_init__ - TODO: Dokumentation hinzufügen"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SessionProgress:
    """Vollständiger Progress-Status für eine Session"""
    session_id: str
    started_at: datetime
    last_update: datetime
    current_state: ProgressState
    current_message: str

    # Gesamtfortschritt
    total_mines: int = 0
    completed_mines: int = 0
    current_mine_index: int = 0
    current_mine_name: str = ""

    # Modell-Fortschritt für aktuelle Mine
    total_models: int = 0
    completed_models: int = 0
    current_model: str = ""

    # Zusätzliche Metriken
    sources_found: int = 0
    successful_results: int = 0
    failed_results: int = 0

    # ERWEITERTE FEHLER-KLASSIFIKATION 06.09.2025
    quality_filtered: int = 0      # Durch Qualitäts-Filter abgelehnt
    api_timeouts: int = 0          # API-Timeouts oder Provider-Fehler
    database_errors: int = 0       # Database-Speicher-Fehler
    system_errors: int = 0         # Echte System-Fehler

    # Performance-Metriken für Zeitschätzung
    avg_time_per_mine: float = 0.0
    estimated_completion: Optional[datetime] = None

    # Updates-Historie (letzte 10)
    updates_history: List[ProgressUpdate] = None

    def __post_init__(self):
        """__post_init__ - TODO: Dokumentation hinzufügen"""
        if self.updates_history is None:
            self.updates_history = []

class BatchProgressManager:
    """Zentraler Manager für Batch-Fortschritt"""

    def __init__(self):
        """__init__ - TODO: Dokumentation hinzufügen"""
        self.sessions: Dict[str, SessionProgress] = {}
        self.lock = threading.RLock()
        self._websocket_connections: Dict[str, List] = {}

    def create_session(self, session_id: str, total_mines: int, total_models: int) -> SessionProgress:
        """Erstelle neue Progress-Session"""
        with self.lock:
            session = SessionProgress(
                session_id=session_id,
                started_at=datetime.now(),
                last_update=datetime.now(),
                current_state=ProgressState.PROCESSING_CSV,
                current_message="Verarbeite CSV-Daten...",
                total_mines=total_mines,
                total_models=total_models,
                updates_history=[]
            )

            self.sessions[session_id] = session
            logger.info(f"[PROGRESS] Session {session_id} erstellt: {total_mines} Minen, {total_models} Modelle")
            return session

    def update_progress(self, session_id: str, state: ProgressState, message: str, **kwargs) -> None:
        """Aktualisiere Progress für Session"""
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(f"[PROGRESS] Session {session_id} nicht gefunden - erstelle Fallback")
                self.sessions[session_id] = SessionProgress(
                    session_id=session_id,
                    started_at=datetime.now(),
                    last_update=datetime.now(),
                    current_state=state,
                    current_message=message
                )

            session = self.sessions[session_id]

            # Update Session-Daten
            session.last_update = datetime.now()
            session.current_state = state
            session.current_message = message

            # Update spezifische Felder wenn übergeben
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            # Berechne Performance-Metriken
            self._calculate_performance_metrics(session)

            # Erstelle ProgressUpdate für Historie
            update = ProgressUpdate(
                state=state,
                message=message,
                mine_current=session.completed_mines,
                mine_total=session.total_mines,
                model_current=session.completed_models,
                model_total=session.total_models,
                sources_found=session.sources_found
            )

            # Füge zu Historie hinzu (max 10 Einträge)
            session.updates_history.append(update)
            if len(session.updates_history) > 10:
                session.updates_history.pop(0)

            logger.info(f"[PROGRESS] {session_id}: {state.value} - {message}")

            # Sende WebSocket-Updates wenn verfügbar
            self._send_websocket_update(session_id, session)

    def _calculate_performance_metrics(self, session: SessionProgress) -> None:
        """Berechne Performance-Metriken für Zeitschätzung"""
        if session.completed_mines > 0:
            elapsed = (session.last_update - session.started_at).total_seconds()
            session.avg_time_per_mine = elapsed / session.completed_mines

            # Schätze verbleibende Zeit
            remaining_mines = session.total_mines - session.completed_mines
            if remaining_mines > 0 and session.avg_time_per_mine > 0:
                estimated_seconds = remaining_mines * session.avg_time_per_mine
                session.estimated_completion = session.last_update + timedelta(seconds=estimated_seconds)

    def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Hole aktuellen Progress-Status"""
        with self.lock:
            if session_id not in self.sessions:
                return None

            session = self.sessions[session_id]

            # Berechne Gesamtfortschritt in %
            if session.total_mines > 0:
                overall_progress = (session.completed_mines / session.total_mines) * 100
            else:
                overall_progress = 0

            # Berechne aktuellen Mine-Fortschritt in %
            if session.total_models > 0:
                mine_progress = (session.completed_models / session.total_models) * 100
            else:
                mine_progress = 0

            # Formatiere Zeitschätzung
            eta_text = "Berechne..."
            if session.estimated_completion:
                remaining_seconds = (session.estimated_completion - datetime.now()).total_seconds()
                if remaining_seconds > 0:
                    if remaining_seconds < 60:
                        eta_text = f"~{int(remaining_seconds)}s"
                    elif remaining_seconds < 3600:
                        eta_text = f"~{int(remaining_seconds/60)} Min"
                    else:
                        eta_text = f"~{int(remaining_seconds/3600)}h {int((remaining_seconds%3600)/60)}m"
                else:
                    eta_text = "Fast fertig!"

            return {
                "session_id": session_id,
                "state": session.current_state.value,
                "message": session.current_message,
                "overall_progress": round(overall_progress, 1),
                "mine_progress": round(mine_progress, 1),
                "current_mine": f"{session.completed_mines + 1}/{session.total_mines}",
                "current_mine_name": session.current_mine_name,
                "current_model": f"{session.completed_models + 1}/{session.total_models}",
                "current_model_name": session.current_model,
                "sources_found": session.sources_found,
                "successful_results": session.successful_results,
                "failed_results": session.failed_results,
                # ERWEITERTE FEHLER-KLASSIFIKATION 06.09.2025
                "quality_filtered": session.quality_filtered,
                "api_timeouts": session.api_timeouts,
                "database_errors": session.database_errors,
                "system_errors": session.system_errors,
                "eta": eta_text,
                "started_at": session.started_at.isoformat(),
                "last_update": session.last_update.isoformat(),
                "updates_history": [
                    {
                        "state": update.state.value,
                        "message": update.message,
                        "timestamp": update.timestamp.isoformat()
                    }
                    for update in session.updates_history[-5:]  # Letzte 5 Updates
                ]
            }

    def mark_mine_started(self, session_id: str, mine_index: int, mine_name: str) -> None:
        """Markiere Start einer neuen Mine"""
        self.update_progress(
            session_id=session_id,
            state=ProgressState.SOURCE_DISCOVERY,
            message=f"Verarbeite Mine {mine_index + 1}/{self.sessions.get(session_id, SessionProgress('', datetime.now(), datetime.now(), ProgressState.PROCESSING_CSV, '')).total_mines}: {mine_name}",
            current_mine_index=mine_index,
            current_mine_name=mine_name,
            completed_models=0  # Reset model counter for new mine
        )

    def mark_source_discovery_complete(self, session_id: str, sources_found: int) -> None:
        """Markiere Source Discovery als abgeschlossen"""
        session = self.sessions.get(session_id)
        if session:
            self.update_progress(
                session_id=session_id,
                state=ProgressState.MODEL_EXECUTION,
                message=f"Quellen gefunden: {sources_found} - starte Modell-Suchen...",
                sources_found=sources_found
            )

    def mark_model_started(self, session_id: str, model_name: str, model_index: int) -> None:
        """Markiere Start eines Modells"""
        session = self.sessions.get(session_id)
        if session:
            self.update_progress(
                session_id=session_id,
                state=ProgressState.MODEL_EXECUTION,
                message=f"Führe Modell {model_index + 1}/{session.total_models} aus: {model_name}",
                current_model=model_name
            )

    def mark_model_complete(self, session_id: str, model_name: str, success: bool, error_message: str = None) -> None:
        """Markiere Modell als abgeschlossen mit erweiterten Fehler-Klassifikation"""
        session = self.sessions.get(session_id)
        if session:
            session.completed_models += 1
            if success:
                session.successful_results += 1
            else:
                session.failed_results += 1
                # ERWEITERTE FEHLER-KLASSIFIKATION 06.09.2025
                self._classify_error(session, error_message)

            self.update_progress(
                session_id=session_id,
                state=ProgressState.MODEL_EXECUTION,
                message=f"Modell {model_name} {'erfolgreich' if success else 'fehlgeschlagen'} - {session.completed_models}/{session.total_models} abgeschlossen",
                completed_models=session.completed_models,
                successful_results=session.successful_results,
                failed_results=session.failed_results
            )

    def _classify_error(self, session: SessionProgress, error_message: str) -> None:
        """Klassifiziert Fehler nach Typ"""
        if not error_message:
            session.system_errors += 1
            return

        error_lower = error_message.lower()

        if any(keyword in error_lower for keyword in [
            'unzureichende suchergebnisse',
            'niedrige qualität',
            'confidence',
            'relevanz',
            'validation failed'
        ]):
            session.quality_filtered += 1
        elif any(keyword in error_lower for keyword in [
            'timeout',
            'rate limit',
            'api error',
            'connection',
            'provider',
            'network'
        ]):
            session.api_timeouts += 1
        elif any(keyword in error_lower for keyword in [
            'no such column',
            'database',
            'sqlite',
            'operational error',
            'constraint'
        ]):
            session.database_errors += 1
        else:
            session.system_errors += 1

    def mark_mine_complete(self, session_id: str, mine_name: str) -> None:
        """Markiere Mine als abgeschlossen"""
        session = self.sessions.get(session_id)
        if session:
            session.completed_mines += 1
            session.completed_models = 0  # Reset for next mine

            self.update_progress(
                session_id=session_id,
                state=ProgressState.MINE_COMPLETE,
                message=f"Mine '{mine_name}' abgeschlossen - {session.completed_mines}/{session.total_mines} Minen fertig",
                completed_mines=session.completed_mines
            )

    def mark_batch_complete(self, session_id: str) -> None:
        """Markiere gesamte Batch-Suche als abgeschlossen"""
        session = self.sessions.get(session_id)
        if session:
            self.update_progress(
                session_id=session_id,
                state=ProgressState.BATCH_COMPLETE,
                message=f"Batch-Suche abgeschlossen! {session.successful_results} erfolgreiche, {session.failed_results} fehlgeschlagene Ergebnisse"
            )

    def mark_error(self, session_id: str, error_message: str) -> None:
        """Markiere Fehler"""
        self.update_progress(
            session_id=session_id,
            state=ProgressState.ERROR,
            message=f"Fehler: {error_message}"
        )

    def _send_websocket_update(self, session_id: str, session: SessionProgress) -> None:
        """Sende Update über WebSocket (falls Verbindungen vorhanden)"""
        # UX-IMPROVEMENT 30.08.2025: Detailliertere Progress-Logs für bessere User Experience
        progress_data = self.get_progress(session_id)
        if progress_data:
            percent = progress_data.get("progress_percent", 0)
            state = session.current_state.value
            message = session.current_message

            # Erweiterte Logs für Frontend-JavaScript-Polling
            logger.info(f"[BATCH-PROGRESS] {session_id} | {state.upper()} | {percent:.1f}% | {message}")
            logger.info(f"[BATCH-PROGRESS-DETAIL] Mines: {session.completed_mines}/{session.total_mines}, Models: {session.completed_models}/{session.total_models}, Sources: {session.sources_found}")

        if session_id in self._websocket_connections:
            # WebSocket-Implementation würde hier stehen
            # Für jetzt erweiterte detaillierte logging
            logger.debug(f"[PROGRESS] WebSocket update for {session_id}: {session.current_state.value}")

    def cleanup_session(self, session_id: str) -> None:
        """Bereinige Session nach Abschluss"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"[PROGRESS] Session {session_id} bereinigt")

# Global instance
batch_progress_manager = BatchProgressManager()
