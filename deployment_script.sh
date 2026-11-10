#!/bin/bash
# Irish Energy Analytics Website - Final Deployment Script
# This script contains all the steps needed to deploy the website to EC2

set -e  # Exit on any error

echo "=== Irish Energy Analytics Website Deployment Script ==="

# Variables - these will be replaced with actual values during deployment
REGION="eu-west-1"
INSTANCE_ID=""
SECURITY_GROUP_ID="sg-05dadb0f44f4ade82"
KEY_PAIR_NAME="YOUR_KEY_PAIR"  # Replace with actual key pair name
SUBNET_ID="subnet-061adec1381e69146"
AMI_ID="ami-004a99a2ac96ef6aa"  # Ubuntu 22.04 LTS

# 1. Create the website directory structure
echo "Creating website directory structure..."
sudo mkdir -p /var/www/irish-energy
sudo chown -R ubuntu:ubuntu /var/www/irish-energy

# 2. Copy website files
echo "Copying website files..."
# This would be done from local machine to remote instance:
# scp -i ~/.ssh/$KEY_PAIR_NAME.pem -r website/* ubuntu@$INSTANCE_IP:/var/www/irish-energy/

# 3. Install required packages
echo "Installing required packages..."
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 4. Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/irish-energy << 'EOF'
server {
    listen 80;
    server_name irish-energy.ai-autofy-general-server.com www.irish-energy.ai-autofy-general-server.com;

    location / {
        root /var/www/irish-energy;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl http2;
    server_name irish-energy.ai-autofy-general-server.com www.irish-energy.ai-autofy-general-server.com;

    root /var/www/irish-energy;
    index index.html;

    ssl_certificate /etc/letsencrypt/live/irish-energy.ai-autofy-general-server.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/irish-energy.ai-autofy-general-server.com/privkey.pem;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 5. Enable site and remove default
echo "Enabling website configuration..."
sudo ln -s /etc/nginx/sites-available/irish-energy /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 6. Install SSL certificate
echo "Installing SSL certificate..."
sudo certbot --nginx -d irish-energy.ai-autofy-general-server.com --non-interactive --agree-tos --email admin@ai-autofy-general-server.com

# 7. Configure API endpoint
echo "Configuring API endpoint..."
sudo tee /var/www/irish-energy/config.js << 'EOF'
const API_CONFIG = {
    baseURL: 'https://dnse188i83.execute-api.eu-west-1.amazonaws.com'
};
EOF

# 8. Verify deployment
echo "Verifying deployment..."
curl -I https://irish-energy.ai-autofy-general-server.com
curl -X GET https://dnse188i83.execute-api.eu-west-1.amazonaws.com/health

echo "=== Deployment Complete ==="
echo "Next steps:"
echo "1. Create DNS A record pointing to the Elastic IP"
echo "2. Test website functionality in browser"
echo "3. Verify API connectivity"