# Deployment Guide

## 🚀 Quick Deployment to Render.com

### Step 1: Fork the Repository
1. Go to [https://github.com/dp-pcs/noah_hw_mcp](https://github.com/dp-pcs/noah_hw_mcp)
2. Click "Fork" to create your own copy

### Step 2: Deploy to Render
1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub account
4. Select your forked `noah_hw_mcp` repository
5. Configure the service:
   - **Name**: `homework-agent-mcp` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `echo "No build needed"`
   - **Start Command**: `python3 heroku_server.py`
   - **Port**: `8000`

### Step 3: Deploy
1. Click "Create Web Service"
2. Wait for deployment (usually 2-3 minutes)
3. Your server will be available at: `https://your-app-name.onrender.com`

### Step 4: Configure Your OpenAI Agent

Use this configuration in your OpenAI agent:

```json
{
  "name": "homework-agent-mcp",
  "description": "MCP Server for Infinite Campus parent portal access",
  "server": {
    "type": "http",
    "url": "https://your-app-name.onrender.com",
    "authentication": {
      "type": "api_key",
      "api_key": "hw_agent_2024_secure_key_abc123xyz789"
    }
  },
  "tools": [
    {
      "name": "check_missing_assignments",
      "description": "Get missing assignments from Infinite Campus",
      "parameters": {
        "since_days": {
          "type": "integer",
          "description": "Number of days to look back (default: 14)",
          "default": 14
        }
      }
    },
    {
      "name": "get_course_grades", 
      "description": "Get course grade history from Infinite Campus",
      "parameters": {
        "course": {
          "type": "string",
          "description": "Course name filter (optional)"
        },
        "since_days": {
          "type": "integer", 
          "description": "Number of days to look back (default: 14)",
          "default": 14
        }
      }
    },
    {
      "name": "health",
      "description": "Check server health and portal connectivity",
      "parameters": {}
    }
  ]
}
```

## 🔧 Alternative Deployments

### Railway.app
1. Go to [railway.app](https://railway.app)
2. Connect GitHub and select your repository
3. Deploy with default settings
4. Use the provided URL in your agent configuration

### Heroku
1. Install Heroku CLI
2. Run: `heroku create your-app-name`
3. Run: `git push heroku main`
4. Use the Heroku URL in your agent configuration

### AWS EC2
Use the provided deployment scripts:
```bash
./deployment/aws/deploy_aws.sh
```

## 🧪 Testing Your Deployment

Once deployed, test your server:

```bash
# Health check
curl https://your-app-name.onrender.com/health

# List tools
curl https://your-app-name.onrender.com/tools/list

# Test tool call
curl -X POST https://your-app-name.onrender.com/tools/call \
  -H "Authorization: Bearer hw_agent_2024_secure_key_abc123xyz789" \
  -H "Content-Type: application/json" \
  -d '{"tool": "health", "arguments": {}}'
```

## 🔐 Security Notes

- The API key is included for testing - change it for production
- The server uses mock data for demonstration
- For real Infinite Campus integration, update the server code with actual scraping logic

## 📞 Support

If you encounter issues:
1. Check the Render logs in your dashboard
2. Verify the server is responding to health checks
3. Ensure your OpenAI agent configuration is correct
