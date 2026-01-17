#!/bin/bash

# ===========================================
# VocabMaster Deployment Script
# Server: 178.128.58.51
# Domain: english.iamstudying.tech
# ===========================================

set -e  # Exit on error

echo "=========================================="
echo "VocabMaster Deployment Script"
echo "=========================================="

# Variables
APP_NAME="vocabmaster"
APP_USER="www-data"
APP_DIR="/var/www/vocabmaster"
REPO_URL="https://github.com/vannt010391/english-leanring.git"
DOMAIN="english.iamstudying.tech"
PYTHON_VERSION="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

echo ""
echo "Step 1: Update system packages..."
apt update && apt upgrade -y
print_status "System updated"

echo ""
echo "Step 2: Install required packages..."
apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx
print_status "Packages installed"

echo ""
echo "Step 3: Create application directory..."
mkdir -p $APP_DIR
cd $APP_DIR
print_status "Directory created: $APP_DIR"

echo ""
echo "Step 4: Clone repository..."
if [ -d "$APP_DIR/.git" ]; then
    print_warning "Repository exists, pulling latest changes..."
    git pull origin main || git pull origin master
else
    git clone $REPO_URL .
fi
print_status "Repository cloned/updated"

echo ""
echo "Step 5: Create Python virtual environment..."
cd $APP_DIR/vocab_project
$PYTHON_VERSION -m venv venv
source venv/bin/activate
print_status "Virtual environment created"

echo ""
echo "Step 6: Install Python dependencies..."
pip install --upgrade pip
pip install django djangorestframework gunicorn whitenoise pillow

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
print_status "Dependencies installed"

echo ""
echo "Step 7: Configure Django settings for production..."

# Create production settings
cat > $APP_DIR/vocab_project/config/settings_production.py << 'SETTINGS_EOF'
from .settings import *

# Production settings
DEBUG = False
ALLOWED_HOSTS = ['english.iamstudying.tech', '178.128.58.51', 'localhost', '127.0.0.1']

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Static files
STATIC_ROOT = '/var/www/vocabmaster/vocab_project/staticfiles'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = '/var/www/vocabmaster/vocab_project/media'
MEDIA_URL = '/media/'

# Whitenoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
SETTINGS_EOF

print_status "Production settings created"

echo ""
echo "Step 8: Run Django migrations and collect static files..."
export DJANGO_SETTINGS_MODULE=config.settings_production
python manage.py migrate --noinput
python manage.py collectstatic --noinput
print_status "Migrations and static files done"

echo ""
echo "Step 9: Create Gunicorn systemd service..."
cat > /etc/systemd/system/vocabmaster.service << 'SERVICE_EOF'
[Unit]
Description=VocabMaster Gunicorn Daemon
Requires=vocabmaster.socket
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vocabmaster/vocab_project
Environment="DJANGO_SETTINGS_MODULE=config.settings_production"
ExecStart=/var/www/vocabmaster/vocab_project/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/vocabmaster.sock \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
SERVICE_EOF

cat > /etc/systemd/system/vocabmaster.socket << 'SOCKET_EOF'
[Unit]
Description=VocabMaster Gunicorn Socket

[Socket]
ListenStream=/run/vocabmaster.sock

[Install]
WantedBy=sockets.target
SOCKET_EOF

print_status "Gunicorn service created"

echo ""
echo "Step 10: Configure Nginx..."
cat > /etc/nginx/sites-available/vocabmaster << 'NGINX_EOF'
server {
    listen 80;
    server_name english.iamstudying.tech 178.128.58.51;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /var/www/vocabmaster/vocab_project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/vocabmaster/vocab_project/media/;
        expires 30d;
    }

    # Proxy to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/vocabmaster.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript application/json;
}
NGINX_EOF

# Enable site
ln -sf /etc/nginx/sites-available/vocabmaster /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx config
nginx -t
print_status "Nginx configured"

echo ""
echo "Step 11: Set permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
print_status "Permissions set"

echo ""
echo "Step 12: Start services..."
systemctl daemon-reload
systemctl enable vocabmaster.socket
systemctl enable vocabmaster.service
systemctl start vocabmaster.socket
systemctl start vocabmaster.service
systemctl restart nginx
print_status "Services started"

echo ""
echo "Step 13: Configure firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable
print_status "Firewall configured"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application is now running at:"
echo "  - http://$DOMAIN"
echo "  - http://178.128.58.51"
echo ""
echo "To enable HTTPS with Let's Encrypt, run:"
echo "  certbot --nginx -d $DOMAIN"
echo ""
echo "Useful commands:"
echo "  - Check status: systemctl status vocabmaster"
echo "  - View logs: journalctl -u vocabmaster -f"
echo "  - Restart app: systemctl restart vocabmaster"
echo ""
