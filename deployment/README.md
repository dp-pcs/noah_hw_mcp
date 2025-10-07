# Remote MCP Server Deployment Guide

This guide shows how to deploy your Infinite Campus MCP server to a remote server so you can access it from OpenAI's preview or any remote AI agent.

## Deployment Options

### 1. Cloud VPS (Recommended)
- **DigitalOcean Droplet** - $5-10/month
- **AWS EC2** - Pay as you go
- **Google Cloud Compute** - Pay as you go
- **Linode** - $5-10/month

### 2. Container Platforms
- **Railway** - Easy deployment
- **Render** - Free tier available
- **Fly.io** - Good for Python apps

### 3. Serverless (Advanced)
- **AWS Lambda** - Requires adaptation
- **Google Cloud Functions** - Requires adaptation

## Quick Start (DigitalOcean)

1. **Create Droplet**
   - Ubuntu 22.04 LTS
   - 2GB RAM minimum
   - 25GB SSD

2. **Deploy Server**
   ```bash
   # On your local machine
   scp -r . user@your-server-ip:/home/user/homework-mcp/
   
   # On the server
   cd /home/user/homework-mcp/
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Configure OpenAI**
   - Use the server's IP address
   - Configure MCP client to connect remotely

## Files in this directory

- `deploy.sh` - Automated deployment script
- `docker-compose.yml` - Docker deployment
- `requirements.txt` - Python dependencies
- `systemd/` - Service configuration
- `nginx/` - Reverse proxy configuration
