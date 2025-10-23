"""
Utility functions for blog app
"""

from django.utils.text import slugify
from django.utils import timezone
from .models import Post


def check_duplicate_post(title: str = None, slug: str = None, unique_id: str = None) -> bool:
    """
    Check if a post with similar content already exists.
    
    Args:
        title: Post title
        slug: Post slug
        unique_id: Unique content identifier
        
    Returns:
        True if duplicate exists, False otherwise
    """
    if unique_id:
        # Check in post content or slug
        if Post.objects.filter(slug__icontains=unique_id).exists():
            return True
    
    if slug:
        if Post.objects.filter(slug=slug).exists():
            return True
    
    if title:
        title_slug = slugify(title)
        if Post.objects.filter(slug=title_slug).exists():
            return True
    
    return False


def create_blog_post_from_content(
    content_data: dict,
    author,
    video_url: str = None,
    status: str = 'published'
) -> dict:
    """
    Create a blog post from generated content.
    
    Args:
        content_data: Content dict from AI generator
        author: User instance (author)
        video_url: S3 URL of the video (optional)
        status: Post status (draft or published)
        
    Returns:
        Dict with post object and success status
    """
    from .models import Post, Category
    
    try:
        blog_data = content_data.get('blog_post', {})
        metadata = content_data.get('metadata', {})
        
        # Get or create category
        category_name = blog_data.get('category', 'Wellness')
        category, _ = Category.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{category_name} related content'}
        )
        
        # Generate unique slug
        base_slug = slugify(blog_data.get('title', 'untitled'))
        unique_id = metadata.get('unique_id', '')
        
        if unique_id:
            slug = f"{base_slug}-{unique_id}"
        else:
            slug = base_slug
        
        # Check for duplicates
        if Post.objects.filter(slug=slug).exists():
            return {
                "success": False,
                "error": f"Duplicate post with slug: {slug}"
            }
        
        # Use content as-is (video will be displayed in template)
        content = blog_data.get('content', '')
        
        # Create post with SEO fields
        post = Post.objects.create(
            title=blog_data.get('title'),
            slug=slug,
            author=author,
            category=category,
            content=content,
            excerpt=blog_data.get('excerpt', ''),
            video_url=video_url,
            meta_description=blog_data.get('meta_description', ''),
            focus_keywords=', '.join(blog_data.get('focus_keywords', [])),
            status=status,
            published_at=timezone.now() if status == 'published' else None,
            is_ai_generated=True
        )
        
        # Add tags
        tags = blog_data.get('tags', [])
        for tag in tags:
            post.tags.add(tag)
        
        print(f"✅ Blog post created: {post.title}")
        print(f"   URL: /post/{post.slug}/")
        print(f"   Category: {category.name}")
        print(f"   Tags: {', '.join(tags)}")
        
        return {
            "success": True,
            "post": post,
            "url": post.get_absolute_url()
        }
        
    except Exception as e:
        print(f"❌ Failed to create blog post: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def generate_seo_meta_tags(post) -> dict:
    """
    Generate SEO meta tags for a post.
    
    Args:
        post: Post instance
        
    Returns:
        Dict with meta tags
    """
    return {
        'title': post.title,
        'description': post.excerpt or post.get_excerpt(),
        'keywords': ', '.join([tag.name for tag in post.tags.all()]),
        'og_title': post.title,
        'og_description': post.excerpt,
        'og_image': post.featured_image.url if post.featured_image else None,
        'og_type': 'article',
        'article_author': post.author.get_full_name() or post.author.username,
        'article_published_time': post.published_at.isoformat() if post.published_at else None,
    }

