# Integrations Technical Assessment

A full-stack application demonstrating integrations with popular SaaS platforms including HubSpot, Airtable, and Notion. Built with FastAPI backend and React frontend.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis server
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd integrations_technical_assessment
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Start Redis
```bash
# Start Redis server (if not already running)
redis-server
```

### 5. Run the Project
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

## 🌐 Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Uvicorn ASGI server
- **Database**: Redis for session management
- **Integrations**: HubSpot, Airtable, Notion APIs
- **Authentication**: OAuth 2.0 flows

### Frontend (React)
- **Framework**: React 18 with Material-UI
- **State Management**: React hooks and context
- **HTTP Client**: Axios for API communication
- **UI Components**: Material-UI components

## 🔌 Integrations

### HubSpot Integration
- **OAuth 2.0**: Full OAuth flow implementation
- **Scopes**: CRM contacts, deals, and OAuth permissions
- **Features**: Contact management, deal tracking
- **Status**: ✅ Fully functional

### Airtable Integration
- **OAuth 2.0**: OAuth flow for Airtable
- **Features**: Base and table management
- **Status**: 🔄 Ready for configuration

### Notion Integration
- **OAuth 2.0**: OAuth flow for Notion
- **Features**: Page and database access
- **Status**: 🔄 Ready for configuration

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the backend directory:

```bash
# HubSpot
HUBSPOT_CLIENT_ID=your_hubspot_client_id
HUBSPOT_CLIENT_SECRET=your_hubspot_client_secret

# Airtable
AIRTABLE_CLIENT_ID=your_airtable_client_id
AIRTABLE_CLIENT_SECRET=your_airtable_client_secret

# Notion
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret

# Redis
REDIS_URL=redis://localhost:6379
```

### HubSpot App Configuration
1. Go to [HubSpot Developer Portal](https://developers.hubspot.com/)
2. Create a new app
3. Configure OAuth settings:
   - **Redirect URL**: `http://localhost:8000/integrations/hubspot/oauth`
   - **Scopes**: `crm.objects.contacts.read`, `crm.objects.contacts.write`, `crm.objects.deals.read`, `oauth`
4. Copy Client ID and Client Secret to your `.env` file

## 🧪 Testing

### Mock Mode
The application includes a mock mode for testing without real API credentials:
- Set `CLIENT_ID = 'XXX'` and `CLIENT_SECRET = 'XXX'` in integration files
- Mock data will be returned for testing purposes

### API Testing
- Use the interactive API docs at http://localhost:8000/docs
- Test OAuth flows through the frontend interface
- Monitor Redis for session data

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Kill existing processes
pkill -f uvicorn

# Check port availability
lsof -i :8000

# Restart with fresh environment
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Won't Start
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

#### Redis Connection Issues
```bash
# Check Redis status
redis-cli ping

# Start Redis if not running
redis-server
```

#### OAuth Flow Issues
- Verify redirect URLs match exactly between app and code
- Check scopes are properly configured
- Ensure environment variables are set correctly
- Clear browser cookies and cache

### Error Messages

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Activate virtual environment and install requirements |
| `Address already in use` | Kill existing processes with `pkill -f uvicorn` |
| `Authorization failed because one or more scopes are invalid` | Update scopes in HubSpot app configuration |
| `Redirect URL doesn't match` | Ensure redirect URLs match exactly in app settings |

## 📁 Project Structure

```
integrations_technical_assessment/
├── backend/
│   ├── venv/                 # Python virtual environment
│   ├── integrations/         # Integration modules
│   │   ├── hubspot.py       # HubSpot OAuth and API
│   │   ├── airtable.py      # Airtable integration
│   │   └── notion.py        # Notion integration
│   ├── main.py              # FastAPI application
│   ├── redis_client.py      # Redis operations
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── integrations/    # Integration components
│   │   └── App.js          # Main React component
│   ├── package.json         # Node.js dependencies
│   └── README.md           # Frontend-specific docs
├── venv/                    # Root virtual environment
└── README.md               # This file
```

## 🚀 Deployment

### Production Considerations
- Use environment variables for all sensitive data
- Set up proper Redis configuration
- Configure CORS for production domains
- Use HTTPS in production
- Set up proper logging and monitoring

### Docker Support
```bash
# Build and run with Docker (if Dockerfile exists)
docker build -t integrations-app .
docker run -p 8000:8000 -p 3000:3000 integrations-app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of a technical assessment and is not intended for production use.

## 🆘 Support

For issues related to:
- **OAuth Configuration**: Check app settings and environment variables
- **API Integration**: Verify API keys and permissions
- **Development Setup**: Ensure all prerequisites are installed
- **Redis Issues**: Check Redis server status and connection

---

**Last Updated**: December 2024  
**Status**: ✅ All integrations functional and tested
