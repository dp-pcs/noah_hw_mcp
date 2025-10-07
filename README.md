# Homework Agent MCP Server

A Model Context Protocol (MCP) server for accessing Infinite Campus parent portal data. This server provides tools for AI agents to retrieve student grades, missing assignments, and other academic information.

## 🚀 Quick Start

### For OpenAI Agents

Use this configuration in your OpenAI agent:

```json
{
  "name": "homework-agent-mcp",
  "server": {
    "type": "http",
    "url": "https://your-deployed-server.com",
    "authentication": {
      "type": "api_key",
      "api_key": "hw_agent_2024_secure_key_abc123xyz789"
    }
  }
}
```

### Available Tools

- **`check_missing_assignments`** - Get missing assignments
- **`get_course_grades`** - Get course grade history  
- **`health`** - Check server health

## 🌐 Deployment Options

### Option 1: Render.com (Free & Easy)

1. Fork this repository
2. Go to [render.com](https://render.com)
3. Create new "Web Service"
4. Connect your GitHub repo
5. Use these settings:
   - **Build Command**: `echo "No build needed"`
   - **Start Command**: `python3 heroku_server.py`
   - **Port**: `8000`

### Option 2: AWS EC2

Use the deployment scripts in `deployment/aws/`:

```bash
./deployment/aws/deploy_aws.sh
```

### Option 3: Local Development

```bash
python3 working_server.py
```

## Features

- **Secure Authentication**: Uses macOS Keychain or environment variables for credential storage
- **Session Persistence**: Saves login sessions to avoid repeated authentication
- **Grade Tracking**: Retrieve current grades and grade history for specific courses
- **Missing Assignments**: Get a list of missing assignments within a specified time window
- **Health Monitoring**: Check server status and portal connectivity

## Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Configuration

Copy the example environment file and configure your school portal:

```bash
cp env.example .env
```

Edit `.env` with your school portal details:

```env
PORTAL_BASE_URL=https://your-school-portal.edu
LOGIN_PATH=/login
PORTAL_USERNAME=your_username
PORTAL_PASSWORD=your_password
```

**Alternative: Use macOS Keychain (Recommended)**

Instead of storing credentials in `.env`, you can use macOS Keychain:

```bash
# Store credentials in Keychain
keyring set "homework-agent" "PORTAL_USERNAME" "your_username"
keyring set "homework-agent" "PORTAL_PASSWORD" "your_password"
```

### 3. Customize Portal Selectors

The server needs to be customized for your specific school portal. Edit `server.py` and update the selectors in these functions:

- `ensure_login()`: Update login form selectors
- `scrape_missing_assignments()`: Update assignment page selectors
- `scrape_course_grades()`: Update grades page selectors

Common portal systems and their typical selectors:

#### Canvas
```python
# Login
await page.fill("input[name='username']", USERNAME)
await page.fill("input[name='password']", PASSWORD)

# Assignments
rows = page.locator(".assignment-row")
```

#### PowerSchool
```python
# Login
await page.fill("input[name='account']", USERNAME)
await page.fill("input[name='pw']", PASSWORD)

# Grades
courses = page.locator(".course-card")
```

#### Infinite Campus
```python
# Login
await page.fill("input[name='username']", USERNAME)
await page.fill("input[name='password']", PASSWORD)
```

### 4. Run the Server

```bash
python server.py
```

The server will start and listen for MCP client connections via stdio.

## Available Tools

### `check_missing_assignments`

Retrieve missing assignments within a specified time window.

**Parameters:**
- `since_days` (optional): Number of days to look back (default: 14)

**Example Response:**
```json
{
  "count": 3,
  "items": [
    {
      "title": "Math Worksheet Chapter 5",
      "course": "Algebra I",
      "due_date": "2024-01-15T00:00:00",
      "status": "missing",
      "points_possible": 100.0,
      "points_earned": null,
      "link": "https://portal.example.edu/assignment/123"
    }
  ]
}
```

### `get_course_grades`

Get grade history for courses within a specified time window.

**Parameters:**
- `course` (optional): Course name filter (e.g., "Math")
- `since_days` (optional): Number of days to include (default: 14)

**Example Response:**
```json
{
  "course_filter": "Math",
  "items": [
    {
      "course": "Algebra I",
      "date": "2024-01-10T00:00:00",
      "grade_percent": 85.5
    }
  ]
}
```

### `health`

Check server health and portal connectivity.

**Example Response:**
```json
{
  "time": "2024-01-15T10:30:00",
  "base_url": "https://portal.example.edu",
  "state_file": "/path/to/state.json",
  "credentials_configured": true
}
```

## Security Notes

- **Credential Storage**: Prefer macOS Keychain over plain text `.env` files
- **Session Storage**: The `state.json` file contains session cookies - keep it private
- **Rate Limiting**: The server respects school portal terms of use
- **Headless Mode**: Runs in headless mode by default for security

## Troubleshooting

### Common Issues

1. **Login Failures**: Check that selectors match your portal's login form
2. **Missing Data**: Verify that assignment and grade page selectors are correct
3. **Session Expired**: Delete `state.json` to force re-authentication
4. **Playwright Issues**: Run `playwright install` to ensure browsers are installed

### Debug Mode

To run with visible browser (for debugging):

```bash
HEADLESS=false python server.py
```

### Portal-Specific Configuration

Different school portals require different configurations:

#### Canvas
- Login URL: Usually `/login`
- Username field: `input[name='username']`
- Password field: `input[name='password']`

#### PowerSchool
- Login URL: Usually `/public/`
- Username field: `input[name='account']`
- Password field: `input[name='pw']`

#### Infinite Campus
- Login URL: Usually `/campus/portal/`
- Username field: `input[name='username']`
- Password field: `input[name='password']`

## Development

### Project Structure

```
noah_hw_mcp/
├── server.py              # Main MCP server
├── requirements.txt       # Python dependencies
├── env.example           # Environment configuration template
├── README.md             # This file
└── state.json            # Session storage (created at runtime)
```

### Adding New Tools

To add new tools, follow this pattern:

1. Add the tool to `handle_list_tools()`
2. Add the handler to `handle_call_tool()`
3. Implement the scraping logic

## License

This project is for educational and personal use. Please respect your school's terms of service and privacy policies.
