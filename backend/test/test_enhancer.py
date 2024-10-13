import sys
import os 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import pytest
from unittest.mock import patch, MagicMock
from app.convertor.enhancer import Enhancer
from app.convertor.constant import DocumentType
@pytest.fixture
def enhancer():
    return Enhancer(openai_api_key="test_api_key")

def test_init_with_api_key():
    enhancer = Enhancer(openai_api_key="test_api_key")
    assert enhancer.openai_api_key == "test_api_key"

def test_init_without_api_key(monkeypatch):
    monkeypatch.setenv('OPENAPI_KEY', 'env_api_key')
    enhancer = Enhancer()
    assert enhancer.openai_api_key == 'env_api_key'

def test_init_without_api_key_raises_error(monkeypatch):
    monkeypatch.delenv('OPENAPI_KEY', raising=False)
    with pytest.raises(ValueError, match="OpenAI API key is required."):
        Enhancer()

@patch('openai.ChatCompletion.create')
def test_enhance_extraction(mock_create, enhancer):
    mock_response = MagicMock()
    mock_response.choices = [{'message': {'content': "Enhanced text"}}]
    mock_create.return_value = mock_response

    result = enhancer.enhance_extraction("raw text", document_type=DocumentType.PDF)
    result = mock_response.choices[0]['message']['content']
    assert result == "Enhanced text"
    mock_create.assert_called_once()

@patch('openai.ChatCompletion.create')
def test_handle_multilingual_sections(mock_create, enhancer):
    mock_response = MagicMock()
    mock_response.choices = [{'message': {'content': "Translated and improved text"}}]
    mock_create.return_value = mock_response

    result = enhancer.handle_multilingual_sections(["Texto en español"], target_language="en")
    result = [res['message']['content'] for res in mock_response.choices]
    assert result == ["Translated and improved text"]
    mock_create.assert_called_once()