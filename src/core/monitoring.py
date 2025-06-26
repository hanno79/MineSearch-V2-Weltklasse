"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Monitoring und Diagnose System für MineSearch
"""

import time
import asyncio
import psutil
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json

from .logger import get_logger

logger = get_logger("monitoring")


@dataclass
class APIMetric:
    """Metriken für API Aufrufe"""
    agent_name: str
    endpoint: str
    status_code: int
    response_time: float
    timestamp: datetime
    error: Optional[str] = None
    
    
@dataclass
class SystemMetric:
    """System Performance Metriken"""
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    active_threads: int
    open_files: int
    timestamp: datetime


@dataclass
class AgentMetric:
    """Agent Performance Metriken"""
    agent_name: str
    request_count: int
    success_count: int
    error_count: int
    avg_response_time: float
    rate_limit_hits: int
    cache_hits: int
    cache_misses: int
    timestamp: datetime


class MonitoringService:
    """Zentraler Monitoring Service"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.api_metrics: deque = deque(maxlen=max_history)
        self.system_metrics: deque = deque(maxlen=max_history)
        self.agent_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.error_log: deque = deque(maxlen=max_history)
        self._start_time = time.time()
        self._process = psutil.Process(os.getpid())
        
    def record_api_call(self, agent_name: str, endpoint: str, status_code: int, 
                       response_time: float, error: Optional[str] = None):
        """Zeichnet API Aufruf auf"""
        metric = APIMetric(
            agent_name=agent_name,
            endpoint=endpoint,
            status_code=status_code,
            response_time=response_time,
            timestamp=datetime.now(),
            error=error
        )
        self.api_metrics.append(metric)
        
        # Log errors
        if error or status_code >= 400:
            self.error_log.append({
                'timestamp': datetime.now(),
                'agent': agent_name,
                'endpoint': endpoint,
                'status': status_code,
                'error': error or f"HTTP {status_code}"
            })
            
    def record_system_metrics(self):
        """Zeichnet aktuelle System-Metriken auf"""
        try:
            cpu_percent = self._process.cpu_percent(interval=0.1)
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Count threads and open files
            num_threads = self._process.num_threads()
            try:
                num_fds = len(self._process.open_files())
            except:
                num_fds = 0
            
            metric = SystemMetric(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_mb=memory_mb,
                active_threads=num_threads,
                open_files=num_fds,
                timestamp=datetime.now()
            )
            self.system_metrics.append(metric)
            
        except Exception as e:
            logger.error(f"Error recording system metrics: {e}")
            
    def record_agent_performance(self, agent_name: str, metrics: Dict[str, Any]):
        """Zeichnet Agent-Performance auf"""
        metric = AgentMetric(
            agent_name=agent_name,
            request_count=metrics.get('request_count', 0),
            success_count=metrics.get('success_count', 0),
            error_count=metrics.get('error_count', 0),
            avg_response_time=metrics.get('avg_response_time', 0),
            rate_limit_hits=metrics.get('rate_limit_hits', 0),
            cache_hits=metrics.get('cache_hits', 0),
            cache_misses=metrics.get('cache_misses', 0),
            timestamp=datetime.now()
        )
        self.agent_metrics[agent_name].append(metric)
        
    def get_api_statistics(self, agent_name: Optional[str] = None, 
                          minutes: int = 60) -> Dict[str, Any]:
        """Holt API Statistiken"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Filter metrics
        metrics = [m for m in self.api_metrics if m.timestamp > cutoff_time]
        if agent_name:
            metrics = [m for m in metrics if m.agent_name == agent_name]
            
        if not metrics:
            return {}
            
        # Calculate statistics
        total_calls = len(metrics)
        successful_calls = sum(1 for m in metrics if 200 <= m.status_code < 300)
        failed_calls = sum(1 for m in metrics if m.status_code >= 400)
        avg_response_time = sum(m.response_time for m in metrics) / total_calls
        
        # Error breakdown
        error_counts = defaultdict(int)
        for m in metrics:
            if m.status_code >= 400:
                error_counts[m.status_code] += 1
                
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': failed_calls,
            'success_rate': successful_calls / total_calls if total_calls > 0 else 0,
            'avg_response_time': avg_response_time,
            'error_breakdown': dict(error_counts),
            'time_window_minutes': minutes
        }
        
    def get_system_health(self) -> Dict[str, Any]:
        """Holt System Health Status"""
        if not self.system_metrics:
            self.record_system_metrics()
            
        # Get latest metric
        latest = self.system_metrics[-1] if self.system_metrics else None
        if not latest:
            return {'status': 'unknown'}
            
        # Calculate averages over last 5 minutes
        cutoff_time = datetime.now() - timedelta(minutes=5)
        recent_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            max_memory_mb = max(m.memory_mb for m in recent_metrics)
        else:
            avg_cpu = latest.cpu_percent
            avg_memory = latest.memory_percent
            max_memory_mb = latest.memory_mb
            
        # Determine health status
        if avg_cpu > 80 or avg_memory > 80:
            status = 'critical'
        elif avg_cpu > 60 or avg_memory > 60:
            status = 'warning'
        else:
            status = 'healthy'
            
        return {
            'status': status,
            'current_cpu_percent': latest.cpu_percent,
            'current_memory_percent': latest.memory_percent,
            'current_memory_mb': latest.memory_mb,
            'avg_cpu_5min': avg_cpu,
            'avg_memory_5min': avg_memory,
            'max_memory_mb_5min': max_memory_mb,
            'active_threads': latest.active_threads,
            'open_files': latest.open_files,
            'uptime_seconds': time.time() - self._start_time
        }
        
    def get_agent_report(self, agent_name: str) -> Dict[str, Any]:
        """Erstellt Agent Performance Report"""
        if agent_name not in self.agent_metrics:
            return {'error': f'No metrics for agent {agent_name}'}
            
        metrics = list(self.agent_metrics[agent_name])
        if not metrics:
            return {'error': 'No metrics available'}
            
        latest = metrics[-1]
        
        # Calculate trends
        if len(metrics) >= 2:
            prev = metrics[-2]
            request_trend = latest.request_count - prev.request_count
            error_trend = latest.error_count - prev.error_count
        else:
            request_trend = 0
            error_trend = 0
            
        return {
            'agent_name': agent_name,
            'total_requests': latest.request_count,
            'total_successes': latest.success_count,
            'total_errors': latest.error_count,
            'success_rate': latest.success_count / latest.request_count if latest.request_count > 0 else 0,
            'avg_response_time': latest.avg_response_time,
            'rate_limit_hits': latest.rate_limit_hits,
            'cache_hit_rate': latest.cache_hits / (latest.cache_hits + latest.cache_misses) if (latest.cache_hits + latest.cache_misses) > 0 else 0,
            'request_trend': request_trend,
            'error_trend': error_trend,
            'last_update': latest.timestamp.isoformat()
        }
        
    def get_error_summary(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Holt Fehler-Zusammenfassung"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_errors = [e for e in self.error_log if e['timestamp'] > cutoff_time]
        
        # Group by agent and error type
        error_summary = defaultdict(lambda: defaultdict(int))
        for error in recent_errors:
            error_summary[error['agent']][error['error']] += 1
            
        # Convert to list format
        summary = []
        for agent, errors in error_summary.items():
            for error_type, count in errors.items():
                summary.append({
                    'agent': agent,
                    'error': error_type,
                    'count': count
                })
                
        # Sort by count
        summary.sort(key=lambda x: x['count'], reverse=True)
        
        return summary
        
    def export_metrics(self, filepath: str):
        """Exportiert alle Metriken in JSON"""
        data = {
            'export_time': datetime.now().isoformat(),
            'uptime_seconds': time.time() - self._start_time,
            'api_metrics': [
                {
                    'agent': m.agent_name,
                    'endpoint': m.endpoint,
                    'status': m.status_code,
                    'response_time': m.response_time,
                    'timestamp': m.timestamp.isoformat(),
                    'error': m.error
                }
                for m in self.api_metrics
            ],
            'system_health': self.get_system_health(),
            'agent_reports': {
                agent: self.get_agent_report(agent)
                for agent in self.agent_metrics.keys()
            },
            'error_summary': self.get_error_summary()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Metrics exported to {filepath}")


# Global monitoring instance
_monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get global monitoring service"""
    return _monitoring_service


# Convenience functions
def record_api_call(agent_name: str, endpoint: str, status_code: int, 
                   response_time: float, error: Optional[str] = None):
    """Record API call"""
    _monitoring_service.record_api_call(agent_name, endpoint, status_code, response_time, error)
    

def record_system_metrics():
    """Record system metrics"""
    _monitoring_service.record_system_metrics()
    

def get_system_health() -> Dict[str, Any]:
    """Get system health"""
    return _monitoring_service.get_system_health()