# hubspot.py

import json
import secrets
import os
import urllib.parse
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
from datetime import datetime
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# HubSpot OAuth credentials
# Option 1: Set environment variables (recommended)
# CLIENT_ID = os.environ.get('HUBSPOT_CLIENT_ID', 'XXX')
# CLIENT_SECRET = os.environ.get('HUBSPOT_CLIENT_SECRET', 'XXX')

# Option 2: Direct assignment (for development only)
CLIENT_ID = 'e830baa8-6e8e-46eb-b341-e5df80924107' 
CLIENT_SECRET = '8df061ef-db1f-4fbb-ac08-76420a14baef'  # Replace with your HubSpot Client Secret

# Redirect URL - using the standard oauth2callback endpoint
# This should match exactly what's configured in your HubSpot app
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

# Updated scopes - using only the scopes that are configured in your HubSpot app
SCOPES = [
    'crm.objects.contacts.read',   # Read contacts (configured)
    'crm.objects.contacts.write',  # Write contacts (configured)
    'crm.objects.deals.read',      # Read deals (configured)
    'oauth'                        # Basic OAuth scope (configured)
]

# Create the authorization URL with proper scopes
scope_string = ' '.join(SCOPES)
# URL encode the redirect URI properly
encoded_redirect_uri = urllib.parse.quote(REDIRECT_URI, safe='')
authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={encoded_redirect_uri}&scope={scope_string}'

async def authorize_hubspot(user_id, org_id):
    """Initialize HubSpot OAuth authorization flow"""
    # Check if credentials are configured
    if CLIENT_ID == 'XXX' or CLIENT_SECRET == 'XXX':
        # Mock mode - return a fake authorization URL that will trigger mock data
        state_data = {
            'state': secrets.token_urlsafe(32),
            'user_id': user_id,
            'org_id': org_id,
            'mock': True
        }
        encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
        
        # Store mock state
        await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
        
        # Return a mock authorization URL with correct redirect URI
        return f'http://localhost:8000/integrations/hubspot/oauth2callback?code=mock_code&state={encoded_state}'
    
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
    
    # Use the properly configured authorization URL with correct scopes
    auth_url = f'{authorization_url}&state={encoded_state}'
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
    
    return auth_url

async def oauth2callback_hubspot(request: Request):
    """Handle HubSpot OAuth callback"""
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    
    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail='Missing code or state parameter')
    
    try:
        state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
    except:
        raise HTTPException(status_code=400, detail='Invalid state parameter')
    
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')
    is_mock = state_data.get('mock', False)
    
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')
    
    # Handle mock mode
    if is_mock or code == 'mock_code':
        # Create mock token data
        mock_token_data = {
            'access_token': 'mock_access_token',
            'refresh_token': 'mock_refresh_token',
            'expires_in': 3600,
            'token_type': 'bearer'
        }
        await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(mock_token_data), expire=600)
        
        close_window_script = """
        <html>
            <script>
                window.close();
            </script>
        </html>
        """
        return HTMLResponse(content=close_window_script)
    
    # Exchange code for access token (real OAuth flow)
    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail='Failed to exchange code for token')
    
    token_data = response.json()
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(token_data), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    """Retrieve stored HubSpot credentials"""
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    credentials = json.loads(credentials)
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials

async def create_integration_item_metadata_object(response_json, item_type="Contact"):
    """Create IntegrationItem from HubSpot response"""
    properties = response_json.get('properties', {})
    
    # Handle different object types
    if item_type == "Contact":
        name = f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip()
        if not name:
            name = properties.get('email', 'Unknown Contact')
        url = f"https://app.hubspot.com/contacts/{response_json.get('id')}"
    elif item_type == "Company":
        name = properties.get('name', 'Unknown Company')
        url = f"https://app.hubspot.com/contacts/{response_json.get('id')}"
    elif item_type == "Deal":
        name = properties.get('dealname', 'Unknown Deal')
        url = f"https://app.hubspot.com/contacts/{response_json.get('id')}"
    else:
        name = f"{item_type} {response_json.get('id', '')}"
        url = f"https://app.hubspot.com/contacts/{response_json.get('id')}"
    
    # Handle timestamps - HubSpot uses milliseconds
    created_at = response_json.get('createdAt')
    updated_at = response_json.get('updatedAt')
    
    creation_time = None
    last_modified_time = None
    
    if created_at:
        try:
            creation_time = datetime.fromtimestamp(int(created_at) / 1000)
        except (ValueError, TypeError):
            pass
    
    if updated_at:
        try:
            last_modified_time = datetime.fromtimestamp(int(updated_at) / 1000)
        except (ValueError, TypeError):
            pass
    
    return IntegrationItem(
        id=str(response_json.get('id')),
        type=item_type,
        name=name,
        creation_time=creation_time,
        last_modified_time=last_modified_time,
        url=url,
        visibility=True
    )

async def get_items_hubspot(credentials):
    """Fetch HubSpot contacts and return as IntegrationItem objects"""
    credentials = json.loads(credentials) if isinstance(credentials, str) else credentials
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='No access token found in credentials')
    
    # Handle mock data
    if access_token == 'mock_access_token':
        # Return mock HubSpot data
        mock_items = [
            IntegrationItem(
                id="1",
                type="Contact",
                name="John Doe",
                creation_time=datetime.now(),
                last_modified_time=datetime.now(),
                url="https://app.hubspot.com/contacts/1",
                visibility=True
            ),
            IntegrationItem(
                id="2",
                type="Contact",
                name="Jane Smith",
                creation_time=datetime.now(),
                last_modified_time=datetime.now(),
                url="https://app.hubspot.com/contacts/2",
                visibility=True
            ),
            IntegrationItem(
                id="3",
                type="Company",
                name="Acme Corporation",
                creation_time=datetime.now(),
                last_modified_time=datetime.now(),
                url="https://app.hubspot.com/contacts/3",
                visibility=True
            ),
            IntegrationItem(
                id="4",
                type="Deal",
                name="Enterprise Deal",
                creation_time=datetime.now(),
                last_modified_time=datetime.now(),
                url="https://app.hubspot.com/contacts/4",
                visibility=True
            )
        ]
        return mock_items
    
    list_of_integration_items = []
    
    # Fetch contacts from HubSpot
    async with httpx.AsyncClient() as client:
        # Get contacts
        contacts_response = await client.get(
            'https://api.hubapi.com/crm/v3/objects/contacts',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            params={
                'limit': 100  # Adjust as needed
            }
        )
        
        if contacts_response.status_code == 200:
            contacts_data = contacts_response.json()
            for contact in contacts_data.get('results', []):
                integration_item = await create_integration_item_metadata_object(contact, 'Contact')
                list_of_integration_items.append(integration_item)
        
        # Get companies
        companies_response = await client.get(
            'https://api.hubapi.com/crm/v3/objects/companies',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            params={
                'limit': 100  # Adjust as needed
            }
        )
        
        if companies_response.status_code == 200:
            companies_data = companies_response.json()
            for company in companies_data.get('results', []):
                integration_item = await create_integration_item_metadata_object(company, 'Company')
                list_of_integration_items.append(integration_item)
        
        # Get deals
        deals_response = await client.get(
            'https://api.hubapi.com/crm/v3/objects/deals',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            params={
                'limit': 100  # Adjust as needed
            }
        )
        
        if deals_response.status_code == 200:
            deals_data = deals_response.json()
            for deal in deals_data.get('results', []):
                integration_item = await create_integration_item_metadata_object(deal, 'Deal')
                list_of_integration_items.append(integration_item)
    
    print(f'HubSpot integration items: {list_of_integration_items}')
    return list_of_integration_items