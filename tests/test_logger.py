import pytest
import logging
from pathlib import Path
import tempfile
import json
from src.core.logger import (
    get_logger, StructuredLogger, PerformanceLogger,
    log_exception, log_api_call
)


def test_structured_logger():
    """Test strukturiertes Logging"""
    logger = get_logger("test_logger", env="test", version="1.0")
    
    # Test Kontext
    assert logger.context["env"] == "test"
    assert logger.context["version"] == "1.0"
    
    # Test with_context
    child_logger = logger.with_context(request_id="123")
    assert child_logger.context["request_id"] == "123"
    assert child_logger.context["env"] == "test"


def test_performance_logger():
    """Test Performance-Logging"""
    logger = get_logger("perf_test")
    perf_logger = PerformanceLogger(logger)
    
    # Start timer
    perf_logger.start_timer("test_operation")
    assert "test_operation" in perf_logger.timers
    
    # End timer
    import time
    time.sleep(0.1)
    perf_logger.end_timer("test_operation", status="success")
    assert "test_operation" not in perf_logger.timers


def test_log_exception():
    """Test Exception-Logging"""
    logger = get_logger("exception_test")
    
    try:
        raise ValueError("Test exception")
    except ValueError as e:
        log_exception(logger, e, operation="test_op")


def test_log_api_call():
    """Test API-Call-Logging"""
    logger = get_logger("api_test")
    
    log_api_call(
        logger,
        method="GET",
        url="https://api.example.com/data",
        status_code=200,
        duration_ms=123.45,
        agent="test_agent"
    )


def test_logger_levels():
    """Test verschiedene Log-Level"""
    logger = get_logger("level_test")
    
    # Diese sollten keine Exceptions werfen
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")