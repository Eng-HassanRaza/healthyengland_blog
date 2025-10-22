# Healthy England Blog

A modern, responsive Django-based blogging website for health and wellness content.

## Features

- **Modern Design**: Clean, responsive design with Bootstrap 5
- **Rich Content**: WYSIWYG editor for blog posts with image support
- **Categories & Tags**: Organize content with categories and tags
- **Search Functionality**: Search through all blog posts
- **Comments System**: Allow readers to comment on posts
- **Newsletter Signup**: Collect email subscriptions
- **Contact Form**: Allow visitors to contact you
- **Admin Interface**: Full Django admin for content management
- **SEO Optimized**: Meta tags and SEO-friendly URLs
- **Social Sharing**: Share buttons for social media
- **Like System**: Readers can like posts
- **View Counter**: Track post views

## Technology Stack

- **Backend**: Django 5.2
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Rich Text Editor**: Summernote
- **Forms**: Django Crispy Forms with Bootstrap 5
- **Tags**: Django Taggit
- **Icons**: Font Awesome
- **Fonts**: Google Fonts (Inter)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd healthyengland_blog
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Create Static Files Directory

```bash
mkdir static
mkdir media
mkdir logs
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to see your blog!

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,healthyengland.com

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/healthyengland

# Email Settings (Configured for healthyengland.com)
EMAIL_PASSWORD=your-email-password-here
```

The project is configured to use healthyengland.com's SMTP server for sending emails via info@healthyengland.com.

### Production Settings

For production deployment:

1. Set `DEBUG = False`
2. Update `SECRET_KEY`
3. Configure proper database
4. Set up static file serving
5. Configure email backend
6. Set up SSL/HTTPS

## Usage

### Admin Interface

Access the admin interface at `/admin/` to:

- Create and manage blog posts
- Manage categories and tags
- Moderate comments
- Manage newsletter subscriptions
- View contact form submissions

### Creating Content

1. **Blog Posts**: Create rich content with images, formatting, and media
2. **Categories**: Organize posts into categories
3. **Tags**: Add relevant tags to posts
4. **Featured Images**: Upload featured images for posts

### Customization

#### Styling

- Edit `blog/templates/blog/base.html` for global styles
- Modify CSS variables in the `<style>` section
- Add custom CSS files to `static/css/`

#### Content

- Update site information in templates
- Modify the hero section in `post_list.html`
- Customize the about page content
- Update contact information

## File Structure

```
healthyengland_blog/
├── blog/
│   ├── models.py          # Database models
│   ├── views.py           # View functions
│   ├── urls.py            # URL patterns
│   ├── admin.py           # Admin configuration
│   ├── forms.py           # Form definitions
│   └── templates/blog/    # HTML templates
├── healthyengland/
│   ├── settings.py        # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploaded files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Deployment

### Using Heroku

1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: gunicorn healthyengland.wsgi
   ```
3. Create `runtime.txt`:
   ```
   python-3.11.0
   ```
4. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py createsuperuser
   ```

### Using DigitalOcean

1. Set up Ubuntu server
2. Install Python, PostgreSQL, Nginx
3. Configure SSL with Let's Encrypt
4. Set up static file serving
5. Configure database and email

## Features in Detail

### Blog Posts

- Rich text editor with image upload
- Featured images
- Categories and tags
- View counter
- Like system
- Social sharing
- SEO-friendly URLs

### User Interaction

- Comment system with moderation
- Newsletter subscription
- Contact form
- Search functionality
- Category and tag filtering

### Admin Features

- Full CRUD operations
- Comment moderation
- Newsletter management
- Contact form submissions
- Analytics and statistics

## Customization Guide

### Adding New Features

1. **New Models**: Add to `blog/models.py`
2. **New Views**: Add to `blog/views.py`
3. **New URLs**: Add to `blog/urls.py`
4. **New Templates**: Create in `blog/templates/blog/`

### Styling Changes

1. **Colors**: Modify CSS variables in `base.html`
2. **Layout**: Update Bootstrap classes
3. **Components**: Customize card styles, buttons, etc.

### Content Management

1. **Homepage**: Edit `post_list.html`
2. **About Page**: Update `about.html`
3. **Contact Info**: Modify `contact.html`
4. **Navigation**: Update `base.html`

## Support

For support and questions:

- Email: info@healthyengland.com
- Documentation: Django documentation
- Community: Django forums

## License

This project is licensed under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Healthy England** - Your trusted source for health and wellness information.
