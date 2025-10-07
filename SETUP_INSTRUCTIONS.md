# Setup Instructions for Infinite Campus MCP Server

## Current Status

✅ **HTTP Server on Render.com**: Working and responding to requests  
❌ **Real Data Scraping**: Not implemented yet (returning mock data)  
❌ **Cursor Integration**: Not working (needs stdio-based server)

## What's Missing

### 1. Infinite Campus Credentials

The server needs your Infinite Campus login credentials to access real data.

**To add credentials:**

1. Go to your Render.com dashboard
2. Find your `noah-hw-mcp` service
3. Go to "Environment" settings
4. Add these environment variables:
   - `PORTAL_USERNAME`: Your Infinite Campus username
   - `PORTAL_PASSWORD`: Your Infinite Campus password
   - `PORTAL_BASE_URL`: `https://academy20co.infinitecampus.org`

### 2. Scraping Logic

The server currently returns mock data. To get real data, we need to:

1. **Login to Infinite Campus** using Playwright
2. **Navigate to the grades page**: `https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/grades?appName=academy20`
3. **Parse the HTML** to extract:
   - Course names
   - Current grades
   - Grade percentages
4. **Navigate to assignments page**: `https://academy20co.infinitecampus.org/campus/nav-wrapper/parent/portal/parent/assignment-list?missingFilter=true&appName=academy20`
5. **Parse missing assignments**

### 3. Testing Approach

**Option A: Test Locally First**
```bash
# Set credentials locally
export PORTAL_USERNAME="your_username"
export PORTAL_PASSWORD="your_password"
export PORTAL_BASE_URL="https://academy20co.infinitecampus.org"

# Run the working server locally
python3 working_server.py

# Test it
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer hw_agent_2024_secure_key_abc123xyz789" \
  -d '{"tool": "check_missing_assignments", "arguments": {"since_days": 7}}'
```

**Option B: Deploy to Render and Test**
1. Add credentials to Render environment variables
2. Push updated code
3. Test the live server

## Next Steps

1. **Add your Infinite Campus credentials** to the server
2. **Implement the scraping logic** to get real data
3. **Test locally** to make sure it works
4. **Deploy to Render** once it's working

## For Cursor Integration

Cursor needs a different approach. We can:

1. **Use the HTTP server** with a proxy/bridge
2. **Create a local stdio-based server** that calls the HTTP server
3. **Use OpenAI's agent preview** instead (which works with HTTP servers)

## Security Note

⚠️ **Important**: Your Infinite Campus credentials will be stored as environment variables on Render. Make sure:
- Use Render's encrypted environment variables
- Don't commit credentials to Git
- Consider using a read-only parent account if possible

## Questions?

1. Do you want to add the scraping logic to get real data?
2. Do you have your Infinite Campus login credentials ready?
3. Would you prefer to test locally first or deploy directly to Render?
4. For Cursor, would you prefer to use OpenAI's agent preview instead?
