# VocabMaster Deployment Guide

## Server: 178.128.58.51
## Domain: english.iamstudying.tech

---

## Step 1: Connect to Your Server

Open your terminal and run:
```bash
ssh root@178.128.58.51
```
Enter your password when prompted.

---

## Step 2: Run the Deployment (Copy & Paste)

Once connected, copy and paste this ENTIRE block:

```bash
# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx git certbot python3-certbot-nginx ufw

# Create app directory
mkdir -p /var/www/vocabmaster
cd /var/www/vocabmaster

# Clone repository
git clone https://github.com/vannt010391/english-leanring.git .

# Setup Python environment
cd /var/www/vocabmaster/vocab_project
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install django djangorestframework django-cors-headers gunicorn whitenoise Pillow
```

---

## Step 3: Create Production Settings

```bash
cat > /var/www/vocabmaster/vocab_project/config/settings_production.py << 'EOF'
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['english.iamstudying.tech', '178.128.58.51', 'localhost', '127.0.0.1']

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

STATIC_ROOT = '/var/www/vocabmaster/vocab_project/staticfiles'
STATIC_URL = '/static/'

MEDIA_ROOT = '/var/www/vocabmaster/vocab_project/media'
MEDIA_URL = '/media/'

MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
EOF
```

---

## Step 4: Run Django Setup

```bash
cd /var/www/vocabmaster/vocab_project
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings_production

python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

---

## Step 5: Create Gunicorn Service

```bash
cat > /etc/systemd/system/vocabmaster.service << 'EOF'
[Unit]
Description=VocabMaster Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vocabmaster/vocab_project
Environment="DJANGO_SETTINGS_MODULE=config.settings_production"
ExecStart=/var/www/vocabmaster/vocab_project/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/run/vocabmaster.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/vocabmaster.socket << 'EOF'
[Unit]
Description=VocabMaster Socket

[Socket]
ListenStream=/run/vocabmaster.sock

[Install]
WantedBy=sockets.target
EOF
```

---

## Step 6: Create Nginx Configuration

```bash
cat > /etc/nginx/sites-available/vocabmaster << 'EOF'
server {
    listen 80;
    server_name english.iamstudying.tech 178.128.58.51;

    location /static/ {
        alias /var/www/vocabmaster/vocab_project/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/vocabmaster/vocab_project/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/vocabmaster.sock;
    }
}
EOF

ln -sf /etc/nginx/sites-available/vocabmaster /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
```

---

## Step 7: Set Permissions & Start Services

```bash
chown -R www-data:www-data /var/www/vocabmaster
chmod -R 755 /var/www/vocabmaster

systemctl daemon-reload
systemctl enable vocabmaster.socket vocabmaster.service
systemctl start vocabmaster.socket vocabmaster.service
systemctl restart nginx
```

---

## Step 8: Configure Firewall

```bash
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable
```

---

## Step 9: Setup HTTPS (SSL Certificate)

First, make sure your domain DNS is pointing to 178.128.58.51, then run:

```bash
certbot --nginx -d english.iamstudying.tech
```

Follow the prompts to get a free SSL certificate.

---

## Done! Your app should be live at:
- http://english.iamstudying.tech
- https://english.iamstudying.tech (after SSL setup)

---

## Useful Commands

```bash
# Check app status
systemctl status vocabmaster

# View logs
journalctl -u vocabmaster -f

# Restart app
systemctl restart vocabmaster

# Restart nginx
systemctl restart nginx

# Update app from GitHub
cd /var/www/vocabmaster
git pull
source vocab_project/venv/bin/activate
cd vocab_project
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart vocabmaster
```

---

## Troubleshooting

### If you see 502 Bad Gateway:
```bash
# Check if gunicorn is running
systemctl status vocabmaster

# Check socket exists
ls -la /run/vocabmaster.sock

# View error logs
journalctl -u vocabmaster -n 50
```

### If static files don't load:
```bash
cd /var/www/vocabmaster/vocab_project
source venv/bin/activate
python manage.py collectstatic --noinput
chown -R www-data:www-data /var/www/vocabmaster
```
