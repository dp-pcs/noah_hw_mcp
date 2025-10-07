#!/bin/bash

# Script to update credentials on the deployed AWS instance

set -e

# Configuration
AWS_PROFILE="bragging-rights"
REGION="us-east-1"
KEY_NAME="homework-mcp-key"

# Get instance IP
echo "🔍 Finding your homework-mcp instance..."
INSTANCE_ID=$(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$REGION" --filters "Name=tag:Name,Values=homework-mcp-server" "Name=instance-state-name,Values=running" --query 'Reservations[0].Instances[0].InstanceId' --output text)

if [ "$INSTANCE_ID" = "None" ] || [ -z "$INSTANCE_ID" ]; then
    echo "❌ No running homework-mcp instance found."
    echo "Available instances:"
    aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$REGION" --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,PublicIpAddress]' --output table
    exit 1
fi

PUBLIC_IP=$(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "✅ Found instance: $INSTANCE_ID"
echo "🌐 Public IP: $PUBLIC_IP"

# Prompt for credentials
echo ""
echo "🔐 Please enter your Infinite Campus credentials:"
read -p "Username: " USERNAME
read -s -p "Password: " PASSWORD
echo ""

# Create update script
cat > update_creds.sh << EOF
#!/bin/bash
echo "Updating credentials..."
sudo sed -i 's/PORTAL_USERNAME=.*/PORTAL_USERNAME=$USERNAME/' /opt/homework-mcp/.env
sudo sed -i 's/PORTAL_PASSWORD=.*/PORTAL_PASSWORD=$PASSWORD/' /opt/homework-mcp/.env
echo "✅ Credentials updated"
echo "Restarting service..."
sudo systemctl restart homework-mcp
echo "✅ Service restarted"
echo "Testing service..."
sleep 5
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Service not responding yet"
EOF

# Copy and run the update script
echo "📤 Uploading credentials update..."
scp -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no update_creds.sh ubuntu@$PUBLIC_IP:/tmp/
ssh -i "${KEY_NAME}.pem" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "chmod +x /tmp/update_creds.sh && /tmp/update_creds.sh"

# Clean up
rm -f update_creds.sh

echo ""
echo "✅ Credentials updated successfully!"
echo "🌐 Your MCP server is now ready at: http://$PUBLIC_IP:8000"
echo "🔍 Test it: curl http://$PUBLIC_IP:8000/health"
