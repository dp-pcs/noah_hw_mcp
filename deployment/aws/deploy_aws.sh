#!/bin/bash

# AWS Deployment Script for Homework Agent MCP Server
# Uses the 'bragging rights' AWS profile

set -e

# Configuration
AWS_PROFILE="bragging-rights"
REGION="us-east-1"
INSTANCE_TYPE="t3.micro"  # Free tier eligible
KEY_NAME="homework-mcp-key"
SECURITY_GROUP="homework-mcp-sg"
INSTANCE_NAME="homework-mcp-server"

echo "🚀 Deploying Homework Agent MCP Server to AWS..."
echo "Profile: $AWS_PROFILE"
echo "Region: $REGION"
echo ""

# Check if AWS CLI is installed and profile exists
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

if ! aws configure list-profiles | grep -q "bragging rights"; then
    echo "❌ AWS profile 'bragging rights' not found."
    echo "Available profiles:"
    aws configure list-profiles
    exit 1
fi

echo "✅ AWS CLI and profile found"

# Create key pair if it doesn't exist
echo "🔑 Creating/checking key pair..."
if ! aws ec2 describe-key-pairs --profile "$AWS_PROFILE" --region "$REGION" --key-names "$KEY_NAME" &>/dev/null; then
    echo "Creating new key pair: $KEY_NAME"
    aws ec2 create-key-pair --profile "$AWS_PROFILE" --region "$REGION" --key-name "$KEY_NAME" --query 'KeyMaterial' --output text > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "✅ Key pair created and saved as ${KEY_NAME}.pem"
else
    echo "✅ Key pair $KEY_NAME already exists"
fi

# Create security group if it doesn't exist
echo "🔒 Creating/checking security group..."
if ! aws ec2 describe-security-groups --profile "$AWS_PROFILE" --region "$REGION" --group-names "$SECURITY_GROUP" &>/dev/null; then
    echo "Creating security group: $SECURITY_GROUP"
    SECURITY_GROUP_ID=$(aws ec2 create-security-group --profile "$AWS_PROFILE" --region "$REGION" --group-name "$SECURITY_GROUP" --description "Security group for Homework MCP Server" --query 'GroupId' --output text)
    
    # Allow SSH (port 22)
    aws ec2 authorize-security-group-ingress --profile "$AWS_PROFILE" --region "$REGION" --group-id "$SECURITY_GROUP_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0
    
    # Allow HTTP (port 8000)
    aws ec2 authorize-security-group-ingress --profile "$AWS_PROFILE" --region "$REGION" --group-id "$SECURITY_GROUP_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0
    
    echo "✅ Security group created with ID: $SECURITY_GROUP_ID"
else
    SECURITY_GROUP_ID=$(aws ec2 describe-security-groups --profile "$AWS_PROFILE" --region "$REGION" --group-names "$SECURITY_GROUP" --query 'SecurityGroups[0].GroupId' --output text)
    echo "✅ Security group $SECURITY_GROUP already exists with ID: $SECURITY_GROUP_ID"
fi

# Create user data script
echo "📝 Creating user data script..."
cat > user_data.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update && apt-get upgrade -y

# Install Python 3.12
apt-get install -y software-properties-common
add-apt-repository ppa:deadsnakes/ppa -y
apt-get update
apt-get install -y python3.12 python3.12-venv python3.12-dev python3-pip

# Install system dependencies
apt-get install -y wget curl git build-essential

# Create application directory
mkdir -p /opt/homework-mcp
cd /opt/homework-mcp

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install mcp>=1.0.0 playwright>=1.40.0 keyring>=24.0.0 pydantic>=2.0.0 python-dotenv>=1.0.0 fastapi>=0.100.0 uvicorn>=0.20.0

# Install Playwright browsers
playwright install chromium
playwright install-deps

# Create environment file
cat > .env << 'ENVEOF'
PORTAL_BASE_URL=https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2
LOGIN_URL=https://academy20co.infinitecampus.org/campus/SSO/academy20/portal/parents?configID=2
LOGIN_PATH=/login
PORTAL_USERNAME=your_username_here
PORTAL_PASSWORD=your_password_here
STATE_PATH=./state.json
HEADLESS=true
HOST=0.0.0.0
PORT=8000
ENVEOF

# Create systemd service
cat > /etc/systemd/system/homework-mcp.service << 'SERVICEEOF'
[Unit]
Description=Homework Agent MCP Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/homework-mcp
Environment=PATH=/opt/homework-mcp/venv/bin
ExecStart=/opt/homework-mcp/venv/bin/python remote_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Set permissions
chown -R ubuntu:ubuntu /opt/homework-mcp
chmod 600 /opt/homework-mcp/.env

# Enable and start service
systemctl daemon-reload
systemctl enable homework-mcp
systemctl start homework-mcp

# Create a simple status check
cat > /opt/homework-mcp/check_status.sh << 'STATUSEOF'
#!/bin/bash
echo "=== Homework MCP Server Status ==="
echo "Service status:"
systemctl status homework-mcp --no-pager
echo ""
echo "Server health:"
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Server not responding"
STATUSEOF

chmod +x /opt/homework-mcp/check_status.sh
chown ubuntu:ubuntu /opt/homework-mcp/check_status.sh
EOF

# Get the latest Ubuntu 22.04 AMI ID
echo "🔍 Finding latest Ubuntu 22.04 AMI..."
AMI_ID=$(aws ec2 describe-images --profile "$AWS_PROFILE" --region "$REGION" --owners 099720109477 --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' --output text)
echo "✅ Using AMI: $AMI_ID"

# Launch EC2 instance
echo "🚀 Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --profile "$AWS_PROFILE" \
    --region "$REGION" \
    --image-id "$AMI_ID" \
    --count 1 \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SECURITY_GROUP_ID" \
    --user-data file://user_data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Project,Value=homework-mcp}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched with ID: $INSTANCE_ID"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --profile "$AWS_PROFILE" --region "$REGION" --instance-ids "$INSTANCE_ID"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --profile "$AWS_PROFILE" --region "$REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "✅ Instance is running!"
echo "🌐 Public IP: $PUBLIC_IP"

# Wait a bit more for the service to start
echo "⏳ Waiting for service to start (this may take a few minutes)..."
sleep 60

# Test the service
echo "🧪 Testing the service..."
if curl -s "http://$PUBLIC_IP:8000/health" > /dev/null; then
    echo "✅ Service is running and accessible!"
    echo ""
    echo "🎉 Deployment successful!"
    echo "📊 Server URL: http://$PUBLIC_IP:8000"
    echo "🔍 Health check: http://$PUBLIC_IP:8000/health"
    echo "📋 API docs: http://$PUBLIC_IP:8000/docs"
    echo ""
    echo "🔧 Next steps:"
    echo "1. SSH into the instance: ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
    echo "2. Edit credentials: sudo nano /opt/homework-mcp/.env"
    echo "3. Restart service: sudo systemctl restart homework-mcp"
    echo "4. Check status: /opt/homework-mcp/check_status.sh"
    echo ""
    echo "💡 Save this information:"
    echo "Instance ID: $INSTANCE_ID"
    echo "Public IP: $PUBLIC_IP"
    echo "Key file: ${KEY_NAME}.pem"
else
    echo "⚠️ Service may still be starting. Try again in a few minutes."
    echo "You can check the status by SSH'ing into the instance:"
    echo "ssh -i ${KEY_NAME}.pem ubuntu@$PUBLIC_IP"
    echo "Then run: /opt/homework-mcp/check_status.sh"
fi

# Clean up
rm -f user_data.sh

echo ""
echo "🏁 Deployment script completed!"
