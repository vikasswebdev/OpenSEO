import pytest
from openseo.providers.registry import create_provider, list_providers, is_known_provider
from openseo.exceptions import ProviderNotFoundError

def test_list_providers():
    providers = list_providers()
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers

def test_is_known_provider():
    assert is_known_provider("openai") is True
    assert is_known_provider("unknown_provider") is False

def test_create_provider_success():
    provider = create_provider("openai")
    assert provider.name == "openai"
    assert provider.model == "gpt-4o-mini"

def test_create_provider_not_found():
    with pytest.raises(ProviderNotFoundError):
        create_provider("nonexistent")
