"""
Simple test for Vapi integration.

Tests that Vapi API client can create assistants and make calls.
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch

from backend.integrations.vapi_api import VapiAPIClient
from backend.interviews.phone_screen_interviewer import PhoneScreenInterviewer


@pytest.mark.asyncio
async def test_vapi_client_initialization():
    """Test that Vapi client initializes correctly."""
    with patch.dict(os.environ, {
        'VAPI_PRIVATE_KEY': 'test_private_key',
        'VAPI_PHONE_NUMBER_ID': 'test_phone_id'
    }):
        client = VapiAPIClient()
        assert client.private_key == 'test_private_key'
        assert client.phone_number_id == 'test_phone_id'
        assert client.base_url == "https://api.vapi.ai"


@pytest.mark.asyncio
async def test_create_assistant():
    """Test assistant creation."""
    with patch.dict(os.environ, {
        'VAPI_PRIVATE_KEY': 'test_private_key',
        'VAPI_PHONE_NUMBER_ID': 'test_phone_id'
    }):
        client = VapiAPIClient()
        
        # Mock the API call
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "assistant_123"}
        mock_response.status_code = 200
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            position = {
                'id': 'position_1',
                'title': 'Software Engineer',
                'must_haves': ['Python', 'FastAPI'],
                'experience_level': 'Senior',
                'domains': ['Backend Development']
            }
            
            assistant_id = await client.create_or_get_assistant(position)
            
            assert assistant_id == "assistant_123"
            assert 'position_1' in client._assistant_cache
            assert client._assistant_cache['position_1'] == "assistant_123"


@pytest.mark.asyncio
async def test_create_call():
    """Test call creation."""
    with patch.dict(os.environ, {
        'VAPI_PRIVATE_KEY': 'test_private_key',
        'VAPI_PHONE_NUMBER_ID': 'test_phone_id'
    }):
        client = VapiAPIClient()
        
        # Mock the API call
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "call_123"}
        mock_response.status_code = 200
        
        with patch.object(client.client, 'post', new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            
            call_id = await client.create_call("assistant_123", "5103585699")
            
            assert call_id == "call_123"
            # Verify phone number was formatted correctly
            call_data = mock_post.call_args[1]['json']
            assert call_data['customer']['number'] == "+15103585699"


@pytest.mark.asyncio
async def test_phone_screen_interviewer_initialization():
    """Test phone screen interviewer initializes correctly."""
    interviewer = PhoneScreenInterviewer()
    assert interviewer.kg is not None
    assert interviewer.grok is not None
    assert interviewer.vapi is not None
    assert interviewer.decision_engine is not None

