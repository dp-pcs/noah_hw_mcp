# MCP Server Configuration for AI Agents

This directory contains configuration files for different AI agent platforms to use your Infinite Campus MCP server.

## Available Configurations

### 1. Claude Desktop (Anthropic)
- File: `claude_desktop.json`
- Instructions: Add this to your Claude Desktop MCP servers configuration

### 2. Cline (VS Code Extension)
- File: `cline_config.json`
- Instructions: Add this to your Cline configuration

### 3. Generic MCP Client
- File: `generic_client.py`
- Instructions: Use this as a template for any Python-based AI agent

## Quick Start

1. **For Claude Desktop:**
   - Copy `claude_desktop.json` content
   - Add to Claude Desktop MCP servers configuration
   - Restart Claude Desktop

2. **For Custom AI Agent:**
   - Use `generic_client.py` as a template
   - Import and use the MCPClient class
   - Call tools as needed

3. **For Direct Integration:**
   - Import `improved_server` module
   - Call `handle_call_tool()` function directly
   - Use in your existing Python code

## Available Tools

- `check_missing_assignments` - Get missing assignments
- `get_course_grades` - Get grade history
- `health` - Check server status

## Example Usage

```python
from improved_server import handle_call_tool

# Get missing assignments
result = await handle_call_tool('check_missing_assignments', {'since_days': 7})
assignments = result[0].text

# Get grades
result = await handle_call_tool('get_course_grades', {'course': 'Math'})
grades = result[0].text
```
