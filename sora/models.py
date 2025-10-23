from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class GeneratedContent(models.Model):
    """Track all generated content to ensure diversity and prevent repetition."""
    
    # Content identification
    title = models.CharField(max_length=300, help_text="Generated content title")
    topic = models.CharField(max_length=200, help_text="Main topic/subject")
    category = models.CharField(max_length=50, help_text="Content category")
    unique_id = models.CharField(max_length=100, unique=True, help_text="Unique identifier for content")
    
    # Video information
    video_id = models.CharField(max_length=100, blank=True, null=True, help_text="Sora video ID")
    video_url = models.URLField(max_length=500, blank=True, null=True, help_text="S3 video URL")
    video_prompt = models.TextField(blank=True, help_text="Sora video generation prompt")
    
    # Content metadata
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
        default='beginner'
    )
    tags = models.JSONField(default=list, help_text="Content tags")
    focus_keywords = models.JSONField(default=list, help_text="SEO focus keywords")
    
    # Generation tracking
    generated_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_published = models.BooleanField(default=False, help_text="Whether content was published")
    
    # Diversity tracking
    topic_keywords = models.JSONField(default=list, help_text="Extracted topic keywords for similarity detection")
    category_usage_count = models.PositiveIntegerField(default=0, help_text="How many times this category was used recently")
    
    class Meta:
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['topic']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.category})"
    
    @classmethod
    def get_recent_content(cls, days=30):
        """Get content created in the last N days."""
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        return cls.objects.filter(generated_at__gte=cutoff_date)
    
    @classmethod
    def get_category_usage(cls, category, days=30):
        """Get usage count for a specific category in recent days."""
        return cls.get_recent_content(days).filter(category=category).count()
    
    @classmethod
    def get_least_used_categories(cls, days=30, limit=5):
        """Get categories that have been used least recently."""
        recent_content = cls.get_recent_content(days)
        category_counts = {}
        
        for content in recent_content:
            category = content.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sort by usage count and return least used
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1])
        return [cat[0] for cat in sorted_categories[:limit]]
