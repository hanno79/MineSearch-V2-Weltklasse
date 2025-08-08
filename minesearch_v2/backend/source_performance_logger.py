"""
Author: rahn
Datum: 23.07.2025
Version: 1.0
Beschreibung: Comprehensive Logging und Monitoring für Source Performance System
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import os

from config.base import config

# Konfiguriere speziellen Logger für Source Performance
performance_logger = logging.getLogger('source_performance')
performance_logger.setLevel(logging.INFO)

# File Handler für Performance Logs
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

performance_log_file = os.path.join(log_dir, 'source_performance.log')
performance_handler = logging.FileHandler(performance_log_file)
performance_handler.setLevel(logging.INFO)

# JSON Formatter für strukturierte Logs
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # CRITICAL FIX: Safe serialization of extra_data with datetime handling
        if hasattr(record, 'extra_data'):
            extra_data = record.extra_data
            if isinstance(extra_data, dict):
                for key, value in extra_data.items():
                    try:
                        if hasattr(value, 'isoformat'):  # datetime objects
                            log_entry[key] = value.isoformat()
                        elif isinstance(value, (str, int, float, bool, type(None))):
                            log_entry[key] = value
                        else:
                            log_entry[key] = str(value)  # Fallback to string
                    except Exception:
                        log_entry[key] = f"<serialization-error:{type(value).__name__}>"
        
        # Safe JSON serialization with error handling
        try:
            return json.dumps(log_entry, ensure_ascii=False)
        except Exception as e:
            # Fallback to basic logging if JSON serialization fails
            return f"LOG_ERROR: {record.levelname} - {record.getMessage()} - JSON_ERROR: {str(e)}"

performance_handler.setFormatter(JSONFormatter())
performance_logger.addHandler(performance_handler)


@dataclass
class PerformanceEvent:
    """Einzelnes Performance-Event"""
    event_type: str  # 'source_update', 'batch_update', 'reset', 'error'
    timestamp: datetime
    url: Optional[str] = None
    domain: Optional[str] = None
    success: Optional[bool] = None
    duration: Optional[float] = None
    fields_found: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'url': self.url,
            'domain': self.domain,
            'success': self.success,
            'duration': self.duration,
            'fields_found': self.fields_found,
            'error_message': self.error_message,
            'metadata': self.metadata or {}
        }


@dataclass
class PerformanceMetrics:
    """Performance-Metriken für Monitoring"""
    total_events: int = 0
    successful_events: int = 0
    failed_events: int = 0
    avg_response_time: float = 0.0
    events_per_minute: float = 0.0
    unique_sources_accessed: int = 0
    batch_updates_performed: int = 0
    resets_performed: int = 0
    errors_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SourcePerformanceLogger:
    """
    Comprehensive Logging und Monitoring System für Source Performance
    
    Features:
    - Strukturierte JSON-Logs
    - Real-time Event-Tracking
    - Performance-Metriken
    - Error-Monitoring
    - Alert-System
    - Dashboard-Daten
    """
    
    def __init__(self, max_events_memory: int = 10000):
        self.logger = performance_logger
        self.max_events_memory = max_events_memory
        
        # In-Memory Event Storage für Real-Time Monitoring
        self.recent_events: deque = deque(maxlen=max_events_memory)
        self.event_counters = defaultdict(int)
        self.error_patterns = defaultdict(int)
        
        # Performance Tracking
        self.metrics = PerformanceMetrics()
        self.hourly_metrics = defaultdict(lambda: PerformanceMetrics())
        
        # Alert Thresholds
        self.alert_thresholds = {
            'error_rate_threshold': 0.2,  # 20% Fehlerrate
            'response_time_threshold': 10.0,  # 10 Sekunden
            'consecutive_failures_threshold': 5,
            'batch_update_failures_threshold': 3
        }
        
        # Alert State
        self.active_alerts = {}
        self.alert_cooldown = timedelta(minutes=15)  # 15 Minuten zwischen gleichartigen Alerts
        
        self.logger.info("SourcePerformanceLogger initialisiert", 
                        extra={'extra_data': {'max_events_memory': max_events_memory}})
    
    def log_source_update(self, url: str, domain: str, success: bool, 
                         duration: Optional[float] = None, fields_found: int = 0,
                         content_type: Optional[str] = None, error: Optional[str] = None):
        """
        Loggt Source-Update Event
        
        Args:
            url: URL der Quelle
            domain: Domain der Quelle  
            success: Erfolg des Updates
            duration: Dauer in Sekunden
            fields_found: Anzahl gefundener Felder
            content_type: Art des Inhalts
            error: Fehlermeldung falls vorhanden
        """
        try:
            event = PerformanceEvent(
                event_type='source_update',
                timestamp=datetime.now(),
                url=url,
                domain=domain,
                success=success,
                duration=duration,
                fields_found=fields_found,
                error_message=error,
                metadata={
                    'content_type': content_type,
                    'fields_found': fields_found
                }
            )
            
            # Log to file
            self.logger.info(f"Source update: {domain} - {'SUCCESS' if success else 'FAILED'}",
                           extra={'extra_data': event.to_dict()})
            
            # Store in memory
            self.recent_events.append(event)
            
            # Update metrics
            self._update_metrics(event)
            
            # Check for alerts
            self._check_alerts(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Loggen des Source-Updates: {e}")
    
    def log_batch_update(self, processed_count: int, duration: float, 
                        errors: List[str] = None):
        """
        Loggt Batch-Update Event
        
        Args:
            processed_count: Anzahl verarbeiteter Sources
            duration: Dauer in Sekunden
            errors: Liste der Fehler
        """
        try:
            success = len(errors or []) == 0
            
            event = PerformanceEvent(
                event_type='batch_update',
                timestamp=datetime.now(),
                success=success,
                duration=duration,
                error_message='; '.join(errors) if errors else None,
                metadata={
                    'processed_count': processed_count,
                    'error_count': len(errors or [])
                }
            )
            
            self.logger.info(f"Batch update: {processed_count} sources in {duration:.2f}s",
                           extra={'extra_data': event.to_dict()})
            
            self.recent_events.append(event)
            self._update_metrics(event)
            self._check_alerts(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Loggen des Batch-Updates: {e}")
    
    def log_source_reset(self, url: str, reason: str, pre_reset_stats: Dict[str, Any]):
        """
        Loggt Source-Reset Event
        
        Args:
            url: URL der Quelle
            reason: Grund für Reset
            pre_reset_stats: Statistiken vor dem Reset
        """
        try:
            event = PerformanceEvent(
                event_type='reset',
                timestamp=datetime.now(),
                url=url,
                success=True,
                metadata={
                    'reason': reason,
                    'pre_reset_stats': pre_reset_stats
                }
            )
            
            self.logger.warning(f"Source reset: {url} - {reason}",
                              extra={'extra_data': event.to_dict()})
            
            self.recent_events.append(event)
            self._update_metrics(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Loggen des Source-Resets: {e}")
    
    def log_error(self, error_type: str, message: str, url: Optional[str] = None,
                 exception: Optional[Exception] = None):
        """
        Loggt Error Event
        
        Args:
            error_type: Art des Fehlers
            message: Fehlermeldung
            url: Betroffene URL (optional)
            exception: Exception-Objekt (optional)
        """
        try:
            metadata = {
                'error_type': error_type,
                'exception_type': type(exception).__name__ if exception else None,
                'exception_details': str(exception) if exception else None
            }
            
            event = PerformanceEvent(
                event_type='error',
                timestamp=datetime.now(),
                url=url,
                success=False,
                error_message=message,
                metadata=metadata
            )
            
            self.logger.error(f"Performance Error [{error_type}]: {message}",
                            extra={'extra_data': event.to_dict()})
            
            self.recent_events.append(event)
            self._update_metrics(event)
            
            # Track error patterns
            self.error_patterns[error_type] += 1
            
            self._check_alerts(event)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Loggen des Errors: {e}")
    
    def get_real_time_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        Holt Real-Time Metriken für die letzten N Minuten
        
        Args:
            time_window_minutes: Zeitfenster in Minuten
            
        Returns:
            Dictionary mit Metriken
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            
            # Filter events im Zeitfenster
            recent_events = [
                event for event in self.recent_events 
                if event.timestamp >= cutoff_time
            ]
            
            if not recent_events:
                return {
                    'time_window_minutes': time_window_minutes,
                    'total_events': 0,
                    'metrics': {}
                }
            
            # Berechne Metriken
            total_events = len(recent_events)
            successful_events = sum(1 for e in recent_events if e.success)
            failed_events = total_events - successful_events
            
            # Response Time Metriken
            response_times = [e.duration for e in recent_events if e.duration is not None]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            # Event Types
            event_types = defaultdict(int)
            for event in recent_events:
                event_types[event.event_type] += 1
            
            # Unique sources
            unique_sources = len(set(e.url for e in recent_events if e.url))
            
            # Error Analysis
            errors = [e for e in recent_events if e.event_type == 'error']
            error_types = defaultdict(int)
            for error in errors:
                error_type = error.metadata.get('error_type', 'unknown') if error.metadata else 'unknown'
                error_types[error_type] += 1
            
            return {
                'time_window_minutes': time_window_minutes,
                'timestamp': datetime.now().isoformat(),
                'total_events': total_events,
                'success_rate': successful_events / total_events if total_events > 0 else 0,
                'events_per_minute': total_events / time_window_minutes,
                'metrics': {
                    'successful_events': successful_events,
                    'failed_events': failed_events,
                    'avg_response_time': round(avg_response_time, 2),
                    'max_response_time': round(max_response_time, 2),
                    'unique_sources_accessed': unique_sources,
                    'event_types': dict(event_types),
                    'error_analysis': {
                        'total_errors': len(errors),
                        'error_types': dict(error_types)
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Berechnen der Real-Time Metriken: {e}")
            return {'error': str(e)}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Holt Dashboard-Daten für Monitoring UI
        
        Returns:
            Dictionary mit Dashboard-Daten
        """
        try:
            # Real-time metrics für verschiedene Zeitfenster
            metrics_5min = self.get_real_time_metrics(5)
            metrics_1hour = self.get_real_time_metrics(60)
            metrics_24hour = self.get_real_time_metrics(24 * 60)
            
            # Active alerts
            active_alerts_list = []
            for alert_type, alert_data in self.active_alerts.items():
                if datetime.now() - alert_data['timestamp'] < timedelta(hours=1):
                    active_alerts_list.append({
                        'type': alert_type,
                        'message': alert_data['message'],
                        'timestamp': alert_data['timestamp'].isoformat(),
                        'severity': alert_data.get('severity', 'warning')
                    })
            
            # Top error patterns (letzte 24h)
            recent_errors = [
                e for e in self.recent_events 
                if e.event_type == 'error' and 
                   e.timestamp >= datetime.now() - timedelta(hours=24)
            ]
            
            error_patterns = defaultdict(int)
            for error in recent_errors:
                error_type = error.metadata.get('error_type', 'unknown') if error.metadata else 'unknown'
                error_patterns[error_type] += 1
            
            # System health score
            health_score = self._calculate_health_score(metrics_1hour)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system_health': {
                    'score': health_score,
                    'status': 'healthy' if health_score >= 0.8 else 'warning' if health_score >= 0.6 else 'critical'
                },
                'metrics': {
                    '5_minutes': metrics_5min,
                    '1_hour': metrics_1hour,
                    '24_hours': metrics_24hour
                },
                'alerts': {
                    'active_count': len(active_alerts_list),
                    'active_alerts': active_alerts_list
                },
                'error_analysis': {
                    'top_error_patterns': dict(error_patterns),
                    'total_errors_24h': len(recent_errors)
                },
                'system_info': {
                    'total_events_in_memory': len(self.recent_events),
                    'memory_utilization': len(self.recent_events) / self.max_events_memory,
                    'uptime_hours': self._get_uptime_hours()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Dashboard-Daten: {e}")
            return {'error': str(e)}
    
    def _update_metrics(self, event: PerformanceEvent):
        """Aktualisiert interne Metriken"""
        try:
            self.metrics.total_events += 1
            
            if event.success:
                self.metrics.successful_events += 1
            else:
                self.metrics.failed_events += 1
            
            if event.event_type == 'source_update' and event.url:
                # Vereinfachtes Tracking der unique sources
                pass
            
            if event.event_type == 'batch_update':
                self.metrics.batch_updates_performed += 1
            
            if event.event_type == 'reset':
                self.metrics.resets_performed += 1
            
            if event.event_type == 'error':
                self.metrics.errors_count += 1
            
            # Update response time
            if event.duration is not None:
                current_avg = self.metrics.avg_response_time
                total_events = self.metrics.total_events
                self.metrics.avg_response_time = (
                    (current_avg * (total_events - 1) + event.duration) / total_events
                )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Aktualisieren der Metriken: {e}")
    
    def _check_alerts(self, event: PerformanceEvent):
        """Prüft und triggert Alerts basierend auf Events"""
        try:
            now = datetime.now()
            
            # Error Rate Alert
            if event.event_type in ['source_update', 'batch_update']:
                recent_events = [
                    e for e in self.recent_events 
                    if e.event_type in ['source_update', 'batch_update'] and
                       e.timestamp >= now - timedelta(minutes=15)
                ]
                
                if len(recent_events) >= 10:  # Mindestens 10 Events für Statistik
                    failed_events = sum(1 for e in recent_events if not e.success)
                    error_rate = failed_events / len(recent_events)
                    
                    if error_rate >= self.alert_thresholds['error_rate_threshold']:
                        self._trigger_alert(
                            'high_error_rate',
                            f"Hohe Fehlerrate: {error_rate:.1%} in den letzten 15 Minuten",
                            'warning'
                        )
            
            # Response Time Alert
            if event.duration and event.duration >= self.alert_thresholds['response_time_threshold']:
                self._trigger_alert(
                    'slow_response',
                    f"Langsame Response-Zeit: {event.duration:.2f}s für {event.url or 'unknown'}",
                    'warning'
                )
            
            # Consecutive Failures Alert
            if event.event_type == 'source_update' and not event.success and event.url:
                recent_failures = [
                    e for e in reversed(self.recent_events)
                    if e.url == event.url and e.event_type == 'source_update'
                ][:5]  # Letzte 5 Events für diese URL
                
                consecutive_failures = 0
                for e in recent_failures:
                    if not e.success:
                        consecutive_failures += 1
                    else:
                        break
                
                if consecutive_failures >= self.alert_thresholds['consecutive_failures_threshold']:
                    self._trigger_alert(
                        'consecutive_failures',
                        f"Quelle {event.url} hat {consecutive_failures} aufeinanderfolgende Fehler",
                        'critical'
                    )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Prüfen der Alerts: {e}")
    
    def _trigger_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Triggert einen Alert"""
        try:
            now = datetime.now()
            
            # Check cooldown
            if alert_type in self.active_alerts:
                last_alert = self.active_alerts[alert_type]['timestamp']
                if now - last_alert < self.alert_cooldown:
                    return  # Still in cooldown
            
            # Create alert
            alert_data = {
                'message': message,
                'severity': severity,
                'timestamp': now
            }
            
            self.active_alerts[alert_type] = alert_data
            
            # Log alert
            self.logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}",
                              extra={'extra_data': alert_data})
            
            # TODO: Implementiere externe Alert-Mechanismen (Email, Slack, etc.)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Triggern des Alerts: {e}")
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """Berechnet System-Health-Score basierend auf Metriken"""
        try:
            if metrics.get('total_events', 0) == 0:
                return 1.0  # Kein Traffic = Gesund
            
            success_rate = metrics.get('success_rate', 0)
            avg_response_time = metrics.get('metrics', {}).get('avg_response_time', 0)
            error_count = metrics.get('metrics', {}).get('error_analysis', {}).get('total_errors', 0)
            
            # Gewichtete Health-Score Berechnung
            health_score = (
                success_rate * 0.5 +  # 50% Gewichtung für Success Rate
                max(0, (10 - avg_response_time) / 10) * 0.3 +  # 30% für Response Time
                max(0, (10 - error_count) / 10) * 0.2  # 20% für Error Count
            )
            
            return max(0, min(1, health_score))
            
        except Exception as e:
            self.logger.error(f"Fehler beim Berechnen des Health-Scores: {e}")
            return 0.5  # Neutral bei Fehler
    
    def _get_uptime_hours(self) -> float:
        """Berechnet Uptime in Stunden seit dem ersten Event"""
        if not self.recent_events:
            return 0.0
        
        first_event_time = min(event.timestamp for event in self.recent_events)
        uptime = datetime.now() - first_event_time
        return uptime.total_seconds() / 3600


# Global Logger Instance
source_performance_logger = SourcePerformanceLogger()