#!/bin/bash

# Simple deployment script using AWS Systems Manager
set -e

AWS_PROFILE="bragging-rights"
REGION="us-east-1"
INSTANCE_ID="i-077af7ed670cdfa5d"

echo "🚀 Deploying Homework Agent MCP Server using AWS Systems Manager..."

# Wait for instance to be ready
echo "⏳ Waiting for instance to be ready..."
aws --profile $AWS_PROFILE ssm wait instance-in-service --instance-ids $INSTANCE_ID --region $REGION

# Install Python and dependencies
echo "📦 Installing Python and dependencies..."
aws --profile $AWS_PROFILE ssm send-command \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=[
        "sudo apt update",
        "sudo apt install -y python3 python3-pip python3-venv",
        "python3 --version"
    ]' \
    --output text --query 'Command.CommandId'

echo "✅ Deployment initiated! The server is being set up."
echo "📋 Instance ID: $INSTANCE_ID"
echo "🌐 You can check the status in the AWS Systems Manager console."
