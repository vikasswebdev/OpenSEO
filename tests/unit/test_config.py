import pytest
from pathlib import Path
from openseo.config.manager import ConfigManager
from openseo.config.schema import OpenSEOConfig
from openseo.exceptions import ConfigNotInitializedError, ConfigurationError

def test_config_defaults():
    config = OpenSEOConfig()
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.cache.enabled is True
    assert config.output.format == "terminal"

def test_config_manager_not_initialized(tmp_path):
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_file)
    assert manager.is_initialized is False
    with pytest.raises(ConfigNotInitializedError):
        manager.load()

def test_config_manager_initialize_and_load(tmp_path):
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_file)
    
    config = manager.initialize()
    assert manager.is_initialized is True
    assert config.provider == "openai"
    
    loaded = manager.load()
    assert loaded.provider == "openai"
    assert loaded.model == "gpt-4o-mini"

def test_config_manager_save_and_set(tmp_path):
    config_file = tmp_path / "config.json"
    manager = ConfigManager(config_file)
    manager.initialize()
    
    manager.set("provider", "anthropic")
    assert manager.get("provider") == "anthropic"
    
    loaded = manager.load()
    assert loaded.provider == "anthropic"

def test_config_manager_invalid_json(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text("invalid json")
    manager = ConfigManager(config_file)
    with pytest.raises(ConfigurationError):
        manager.load()
