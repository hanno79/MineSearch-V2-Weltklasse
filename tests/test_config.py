import pytest
from pathlib import Path
import tempfile
import os
from src.core.config import Config, get_config


def test_config_loading():
    """Test Konfiguration laden"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("OPENROUTER_API_KEY=test_key_123\n")
        f.write("DATABASE_PATH=./test.db\n")
        
    try:
        # Save current env var if exists
        original_key = os.environ.get("OPENROUTER_API_KEY")
        
        # Clear env var to ensure we load from file
        if "OPENROUTER_API_KEY" in os.environ:
            del os.environ["OPENROUTER_API_KEY"]
        
        config = Config(f.name)
        
        assert config.api.openrouter_key == "test_key_123"
        assert str(config.database.path) == "test.db"
    finally:
        # Restore original env var if existed
        if original_key:
            os.environ["OPENROUTER_API_KEY"] = original_key
        
        os.unlink(f.name)


def test_config_validation():
    """Test Konfigurationsvalidierung"""
    config = Config()
    validation = config.validate()
    
    assert "api_status" in validation
    assert "warnings" in validation
    assert isinstance(validation["warnings"], list)


def test_active_agents():
    """Test verfügbare Agenten"""
    config = Config()
    agents = config.get_active_agents()
    
    assert "scraper" in agents  # Immer verfügbar
    assert isinstance(agents, list)