"""
Automated Content Pipeline
Generates video prompts, creates videos, and publishes blog posts
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthyengland.settings')
django.setup()

from django.contrib.auth.models import User
from sora.utils.content_generator import SkincareContentGenerator
from sora.utils.generator import SoraVideoGenerator
from blog.utils import check_duplicate_post, create_blog_post_from_content


class AutoContentPipeline:
    """Automated pipeline for creating video + blog content."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.content_generator = SkincareContentGenerator()
        self.video_generator = SoraVideoGenerator()
        
        # Get default author (admin user)
        try:
            self.author = User.objects.filter(is_staff=True).first()
            if not self.author:
                raise ValueError("No admin user found. Create one first.")
        except Exception as e:
            raise ValueError(f"Could not get author: {e}")
    
    def run(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        publish_immediately: bool = True
    ) -> Dict:
        """
        Run complete content generation pipeline.
        
        Args:
            topic: Specific topic (optional, auto-generated if None)
            category: Health category filter
            publish_immediately: Publish post immediately (True) or save as draft (False)
            
        Returns:
            Dict with results
        """
        
        print("\n" + "="*70)
        print("🚀 AUTOMATED CONTENT PIPELINE")
        print("="*70)
        print(f"Topic: {topic or 'Auto-generated'}")
        print(f"Category: {category or 'Any'}")
        print(f"Publish: {'Immediately' if publish_immediately else 'As Draft'}")
        print("="*70 + "\n")
        
        # Step 1: Generate content package
        print("Step 1: Generating content with OpenAI...")
        content_result = self.content_generator.generate_content_package(
            topic=topic,
            category=category
        )
        
        if not content_result['success']:
            return {
                "success": False,
                "error": f"Content generation failed: {content_result['error']}"
            }
        
        content_data = content_result['data']
        
        # Validate video prompt
        video_prompt_data = content_data.get('video_prompt', {})
        if not self.content_generator.validate_video_prompt(video_prompt_data):
            return {
                "success": False,
                "error": "Video prompt validation failed"
            }
        
        print(f"✅ Content generated: {content_data['blog_post']['title']}")
        
        # Step 2: Check for duplicates
        print("\nStep 2: Checking for duplicates...")
        unique_id = content_data['metadata'].get('unique_id')
        title = content_data['blog_post'].get('title')
        
        if check_duplicate_post(title=title, unique_id=unique_id):
            return {
                "success": False,
                "error": f"Duplicate content detected: {title}",
                "duplicate": True
            }
        
        print("✅ No duplicates found")
        
        # Step 3: Generate video with Sora
        print("\nStep 3: Generating video with Sora...")
        video_prompt = video_prompt_data.get('prompt')
        
        # Use .env settings for video generation (not content generator duration)
        video_result = self.video_generator.generate_video(
            prompt=video_prompt
            # duration, quality, aspect_ratio will be loaded from .env settings
        )
        
        if video_result.get('error'):
            return {
                "success": False,
                "error": f"Video generation failed: {video_result['error']}"
            }
        
        video_id = video_result.get('video_id')
        print(f"✅ Video generation started: {video_id}")
        
        # Step 4: Wait for video completion
        print("\nStep 4: Waiting for video completion...")
        status = self.video_generator.wait_for_completion(video_id, max_wait_time=600)
        
        if status.get('status') != 'completed':
            return {
                "success": False,
                "error": f"Video generation failed or timed out: {status.get('status')}"
            }
        
        print("✅ Video completed")
        
        # Step 5: Download and upload to S3
        print("\nStep 5: Downloading and uploading to S3...")
        
        # Prepare video metadata with SEO title
        from django.conf import settings
        video_metadata = {
            'video_id': video_id,
            'prompt': video_prompt,
            'duration': getattr(settings, 'SORA_DEFAULT_DURATION', 4),  # Use .env setting
            'seo_title': content_data['blog_post']['title']  # Add SEO title
        }
        
        video_path = self.video_generator.download_video(
            video_id,
            upload_to_s3=True,
            delete_local_after_s3=True,
            video_metadata=video_metadata
        )
        
        if not video_path:
            return {
                "success": False,
                "error": "Failed to download/upload video"
            }
        
        # Extract S3 URL
        if video_path.startswith('http'):
            video_url = video_path
            print(f"✅ Video uploaded to S3: {video_url}")
        else:
            # If local path returned, construct S3 URL (shouldn't happen with delete_local=True)
            video_url = None
            print(f"⚠️ Video saved locally: {video_path}")
        
        # Step 6: Create blog post
        print("\nStep 6: Creating blog post...")
        post_result = create_blog_post_from_content(
            content_data=content_data,
            author=self.author,
            video_url=video_url,
            status='published' if publish_immediately else 'draft'
        )
        
        if not post_result['success']:
            return {
                "success": False,
                "error": f"Blog post creation failed: {post_result['error']}",
                "video_url": video_url  # Video was created, just post failed
            }
        
        post = post_result['post']
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"Blog Post: {post.title}")
        print(f"   URL: {post.get_absolute_url()}")
        print(f"   Category: {post.category.name}")
        print(f"   Status: {post.status}")
        if video_url:
            print(f"Video URL: {video_url}")
        print(f"Google Sheets: Updated")
        print("="*70 + "\n")
        
        return {
            "success": True,
            "post": post,
            "video_url": video_url,
            "video_id": video_id,
            "content_data": content_data
        }


def main():
    """Run pipeline from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated health content pipeline")
    parser.add_argument('--topic', help='Specific topic (optional)')
    parser.add_argument('--category', choices=['Nutrition', 'Fitness', 'Mental Health', 'Wellness', 'Sleep'], help='Category filter')
    parser.add_argument('--draft', action='store_true', help='Save as draft instead of publishing')
    
    args = parser.parse_args()
    
    try:
        pipeline = AutoContentPipeline()
        result = pipeline.run(
            topic=args.topic,
            category=args.category,
            publish_immediately=not args.draft
        )
        
        if result['success']:
            print("✅ Success!")
            return 0
        else:
            print(f"❌ Failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

