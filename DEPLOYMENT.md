# Deployment Guide for Healthy England Blog

This guide covers deploying your Django blog to various platforms.

## Quick Start

1. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Visit: http://127.0.0.1:8000

2. **Access admin panel:**
   - URL: http://127.0.0.1:8000/admin
   - Username: admin
   - Password: admin123

## Production Deployment

### Option 1: Heroku (Recommended for beginners)

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

3. **Create production files**
   
   Create `Procfile`:
   ```
   web: gunicorn healthyengland.wsgi
   ```
   
   Create `runtime.txt`:
   ```
   python-3.11.0
   ```

4. **Update settings for production**
   
   Create `healthyengland/settings_production.py`:
   ```python
   from .settings import *
   import dj_database_url
   
   DEBUG = False
   ALLOWED_HOSTS = ['your-app-name.herokuapp.com', 'healthyengland.com']
   
   # Database
   DATABASES['default'] = dj_database_url.parse(os.environ.get('DATABASE_URL'))
   
   # Static files
   STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
   
   # Security
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   SECURE_HSTS_INCLUDE_SUBDOMAINS = True
   SECURE_HSTS_PRELOAD = True
   ```

5. **Deploy**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

### Option 2: DigitalOcean App Platform

1. **Connect your GitHub repository**
2. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `gunicorn healthyengland.wsgi`
3. **Set environment variables:**
   - `SECRET_KEY`: Your Django secret key
   - `DEBUG`: False
   - `ALLOWED_HOSTS`: your-domain.com

### Option 3: Traditional VPS (Ubuntu)

1. **Set up server:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx postgresql
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure PostgreSQL:**
   ```bash
   sudo -u postgres createdb healthyengland
   sudo -u postgres createuser --interactive
   ```

4. **Set up Nginx:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location /static/ {
           alias /path/to/your/project/staticfiles/;
       }
       
       location /media/ {
           alias /path/to/your/project/media/;
       }
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. **Set up SSL with Let's Encrypt:**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Environment Variables

Create a `.env` file for production:

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthyengland

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Static Files
STATIC_ROOT=/path/to/staticfiles
MEDIA_ROOT=/path/to/media
```

## Domain Setup

1. **Purchase domain** (e.g., from Namecheap, GoDaddy)
2. **Point DNS to your server:**
   - A record: @ → your-server-ip
   - CNAME: www → your-domain.com
3. **Update ALLOWED_HOSTS** in settings

## Security Checklist

- [ ] Set `DEBUG = False`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Set up proper database permissions
- [ ] Configure email backend
- [ ] Set up backup strategy
- [ ] Enable Django security middleware
- [ ] Set up monitoring and logging

## Performance Optimization

1. **Static files:**
   ```bash
   python manage.py collectstatic
   ```

2. **Database optimization:**
   - Add database indexes
   - Use database connection pooling
   - Consider Redis for caching

3. **CDN setup:**
   - Use CloudFlare or AWS CloudFront
   - Serve static files from CDN

## Monitoring

1. **Set up logging:**
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.FileHandler',
               'filename': 'django.log',
           },
       },
       'loggers': {
           'django': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }
   ```

2. **Health checks:**
   - Set up uptime monitoring
   - Monitor database performance
   - Track error rates

## Backup Strategy

1. **Database backups:**
   ```bash
   pg_dump healthyengland > backup_$(date +%Y%m%d).sql
   ```

2. **Media files backup:**
   ```bash
   tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
   ```

3. **Automated backups:**
   - Set up cron jobs for regular backups
   - Store backups in cloud storage (AWS S3, Google Cloud)

## Troubleshooting

### Common Issues

1. **Static files not loading:**
   - Run `python manage.py collectstatic`
   - Check STATIC_ROOT and STATIC_URL settings

2. **Database connection errors:**
   - Verify database credentials
   - Check if database server is running

3. **Permission errors:**
   - Check file permissions: `chmod 755`
   - Ensure proper ownership: `chown -R user:group`

### Logs

Check application logs:
```bash
# Django logs
tail -f django.log

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# System logs
journalctl -u your-app-service
```

## Support

For deployment issues:

1. Check Django documentation
2. Review server logs
3. Test locally first
4. Use staging environment
5. Monitor error rates

---

**Remember:** Always test your deployment in a staging environment before going live!
