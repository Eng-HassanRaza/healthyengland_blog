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
from sora.utils.enhanced_content_generator import EnhancedContentGenerator
from sora.utils.generator import SoraVideoGenerator
from sora.utils.enhanced_duplicate_detection import EnhancedDuplicateDetector
from blog.utils import check_duplicate_post, create_blog_post_from_content


class AutoContentPipeline:
    """Automated pipeline for creating video + blog content."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.content_generator = EnhancedContentGenerator()
        self.video_generator = SoraVideoGenerator()
        self.duplicate_detector = EnhancedDuplicateDetector()
        
        # Get default author (admin user)
        try:
            self.author = User.objects.filter(is_staff=True).first()
            if not self.author:
                raise ValueError("No admin user found. Create one first.")
        except Exception as e:
            raise ValueError(f"Could not get author: {e}")
    
    def _optimize_video_prompt(self, prompt: str) -> str:
        """
        Use AI to optimize video prompt for 12-second video.
        
        Args:
            prompt: Original video prompt
            
        Returns:
            Optimized prompt that fits 12-second criteria
        """
        try:
            import openai
            from django.conf import settings
            
            # Get OpenAI API key
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                print("   ⚠️ OpenAI API key not found - using fallback optimization")
                return self._fallback_optimize_prompt(prompt)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Create optimization prompt
            optimization_prompt = f"""
You are a video content optimizer. Your task is to shorten this video prompt to fit exactly in a 12-second video.

ORIGINAL PROMPT:
{prompt}

REQUIREMENTS:
- Maximum 120 characters total
- Keep the essential message
- Make it punchy and engaging
- Ensure it can be spoken in 10 seconds
- Maintain the expert tone
- Keep the hook and tip structure
- ONLY use European/English/African race characters (NO Asian, Hispanic, or other ethnicities)

Return ONLY the optimized prompt, nothing else.
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a video content optimizer. Shorten prompts to fit 12-second videos while keeping the essential message."},
                    {"role": "user", "content": optimization_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            optimized = response.choices[0].message.content.strip()
            
            # Validate the optimized prompt
            if len(optimized) <= 120 and len(optimized) >= 30:
                return optimized
            else:
                print(f"   ⚠️ AI optimization result too long/short: {len(optimized)} chars")
                return None
                
        except Exception as e:
            print(f"   ⚠️ AI optimization failed: {e}")
            return self._fallback_optimize_prompt(prompt)
    
    def _fallback_optimize_prompt(self, prompt: str) -> str:
        """
        Fallback optimization when AI is not available.
        Uses simple text processing to shorten the prompt.
        
        Args:
            prompt: Original video prompt
            
        Returns:
            Optimized prompt that fits 12-second criteria
        """
        try:
            # Handle different prompt formats
            if "Expert says:" in prompt:
                # Extract the quoted content
                start = prompt.find("'") + 1
                end = prompt.rfind("'")
                if start > 0 and end > start:
                    content = prompt[start:end]
                    
                    # Split into sentences and take the most important parts
                    sentences = content.split('. ')
                    if len(sentences) >= 2:
                        # Take first sentence (hook) and shorten second sentence (tip)
                        hook = sentences[0].strip()
                        tip = sentences[1].strip()
                        
                        # Shorten tip if too long
                        if len(tip) > 50:
                            words = tip.split()
                            tip = ' '.join(words[:8])  # Take first 8 words
                        
                        optimized = f"Expert says: '{hook}. {tip}.'"
                        
                        # Ensure it's within limits
                        if len(optimized) <= 120:
                            return optimized
                        else:
                            # Further shorten
                            hook_words = hook.split()[:4]  # First 4 words of hook
                            tip_words = tip.split()[:6]   # First 6 words of tip
                            return f"Expert says: '{' '.join(hook_words)}. {' '.join(tip_words)}.'"
                    else:
                        # Single sentence - just truncate intelligently
                        words = content.split()
                        if len(words) > 12:
                            return f"Expert says: '{' '.join(words[:12])}...'"
                        else:
                            return f"Expert says: '{content}'"
                else:
                    # No quotes found, just truncate
                    if len(prompt) > 120:
                        return prompt[:117] + "..."
                    else:
                        return prompt
            elif "'hook':" in prompt and "'main_tip':" in prompt:
                # Handle dictionary format with hook and main_tip
                try:
                    import re
                    hook_match = re.search(r"'hook':\s*'([^']+)'", prompt)
                    tip_match = re.search(r"'main_tip':\s*'([^']+)'", prompt)
                    
                    if hook_match and tip_match:
                        hook = hook_match.group(1)
                        tip = tip_match.group(1)
                        
                        # Shorten tip if too long
                        if len(tip) > 60:
                            words = tip.split()
                            tip = ' '.join(words[:10])  # Take first 10 words
                        
                        optimized = f"Expert says: '{hook} {tip}'"
                        
                        # Ensure it's within limits
                        if len(optimized) <= 120:
                            return optimized
                        else:
                            # Further shorten
                            hook_words = hook.split()[:5]  # First 5 words of hook
                            tip_words = tip.split()[:8]    # First 8 words of tip
                            return f"Expert says: '{' '.join(hook_words)} {' '.join(tip_words)}'"
                    else:
                        # Fallback to simple truncation
                        if len(prompt) > 120:
                            return prompt[:117] + "..."
                        else:
                            return prompt
                except:
                    # Fallback to simple truncation
                    if len(prompt) > 120:
                        return prompt[:117] + "..."
                    else:
                        return prompt
            else:
                # No recognized format, just truncate
                if len(prompt) > 120:
                    return prompt[:117] + "..."
                else:
                    return prompt
                    
        except Exception as e:
            print(f"   ⚠️ Fallback optimization failed: {e}")
            # Last resort - simple truncation
            return prompt[:120] + "..." if len(prompt) > 120 else prompt
    
    def run(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        publish_immediately: bool = True,
        test_mode: bool = False
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
        
        # Step 1: Generate content package with diversity optimization
        print("Step 1: Generating diverse content with OpenAI...")
        content_result = self.content_generator.generate_content_package(
            topic=topic,
            category=category,
            use_smart_selection=True  # Enable smart selection for diversity
        )
        
        if not content_result['success']:
            return {
                "success": False,
                "error": f"Content generation failed: {content_result['error']}"
            }
        
        content_data = content_result['data']
        
        # Validate content_data structure
        if not content_data:
            return {
                "success": False,
                "error": "No content data received from generator"
            }
        
        # Check for required fields
        if 'blog_post' not in content_data:
            return {
                "success": False,
                "error": "Missing blog_post in content data"
            }
        
        blog_post = content_data.get('blog_post', {})
        if 'category' not in blog_post:
            return {
                "success": False,
                "error": "Missing category in blog_post data"
            }
        
        # Debug: Print content structure
        print(f"\n📋 Content Data Structure:")
        print(f"   Keys: {list(content_data.keys())}")
        if 'blog_post' in content_data:
            print(f"   Blog post keys: {list(content_data['blog_post'].keys())}")
            print(f"   Blog post content: {content_data['blog_post']}")
        if 'video_prompt' in content_data:
            print(f"   Video prompt keys: {list(content_data['video_prompt'].keys())}")
            print(f"   Video prompt content: {content_data['video_prompt']}")
        if 'diversity_metadata' in content_data:
            print(f"   Diversity metadata: {content_data['diversity_metadata']}")
        
        # Step 1.5: Enhanced duplicate detection
        print("\nStep 1.5: Checking for content similarity...")
        blog_post = content_data.get('blog_post', {})
        title = blog_post.get('title', '')
        topic = blog_post.get('title', '')  # Use title as topic
        category = blog_post.get('category', 'Unknown')
        
        # Debug: Print content structure
        print(f"   Title: {title}")
        print(f"   Category: {category}")
        
        # Check for similarity using enhanced duplicate detection
        try:
            similarity_check = self.duplicate_detector.check_content_similarity(title, topic, category)
            if similarity_check['is_similar']:
                return {
                    "success": False,
                    "error": f"Content too similar to recent content: {similarity_check['recommendations']}",
                    "duplicate": True
                }
            
            print("✅ Content is unique and diverse")
        except Exception as e:
            print(f"⚠️ Duplicate detection failed: {e}")
            print("   Continuing without duplicate check...")
        
        # Validate video prompt (skip if method doesn't exist)
        video_prompt_data = content_data.get('video_prompt', {})
        try:
            if hasattr(self.content_generator, 'validate_video_prompt'):
                if not self.content_generator.validate_video_prompt(video_prompt_data):
                    return {
                        "success": False,
                        "error": "Video prompt validation failed"
                    }
            else:
                print("   Video prompt validation skipped (method not available)")
        except Exception as e:
            print(f"   Video prompt validation failed: {e}")
            print("   Continuing without validation...")
        
        print(f"✅ Content generated: {content_data['blog_post']['title']}")
        print(f"   Category: {content_data['blog_post']['category']}")
        try:
            print(f"   Diversity Score: {similarity_check['overall_similarity']:.2f}")
        except:
            print("   Diversity Score: N/A (check failed)")
        
        # Debug: Print video prompt details
        print(f"   Video prompt length: {len(video_prompt) if 'video_prompt' in locals() else 'N/A'}")
        if 'video_prompt' in locals():
            print(f"   Video prompt preview: {video_prompt[:100]}...")
        
        # Step 2: Check for duplicates
        print("\nStep 2: Checking for duplicates...")
        unique_id = content_data.get('diversity_metadata', {}).get('unique_id')
        title = content_data['blog_post'].get('title')
        
        if check_duplicate_post(title=title, unique_id=unique_id):
            return {
                "success": False,
                "error": f"Duplicate content detected: {title}",
                "duplicate": True
            }
        
        print("✅ No duplicates found")
        
        # Step 3: Generate video with Sora (or skip in test mode)
        if test_mode:
            print("\nStep 3: Testing video prompt processing (NO Sora API call)...")
            # Test video prompt processing without expensive API call
            video_prompt_data = content_data.get('video_prompt', {})
            video_prompt_raw = video_prompt_data.get('content') or video_prompt_data.get('prompt')
            
            if video_prompt_raw:
                # Test prompt conversion (without sending to Sora)
                if isinstance(video_prompt_raw, list):
                    video_prompt = " ".join([
                        f"{item.get('timestamp', item.get('time', ''))}: {item.get('text', item.get('description', ''))}" 
                        for item in video_prompt_raw
                    ])
                elif isinstance(video_prompt_raw, dict):
                    if 'hook' in video_prompt_raw and 'tip' in video_prompt_raw:
                        hook_text = video_prompt_raw['hook'].get('text', video_prompt_raw['hook']) if isinstance(video_prompt_raw['hook'], dict) else video_prompt_raw['hook']
                        tip_text = video_prompt_raw['tip'].get('text', video_prompt_raw['tip']) if isinstance(video_prompt_raw['tip'], dict) else video_prompt_raw['tip']
                        video_prompt = f"Expert says: '{hook_text} {tip_text}'"
                    elif 'spoken_content' in video_prompt_raw:
                        # Handle spoken_content format
                        spoken = video_prompt_raw['spoken_content']
                        hook_text = spoken.get('hook', '')
                        tip_text = spoken.get('tip', '')
                        video_prompt = f"Expert says: '{hook_text} {tip_text}'"
                    elif 'timing_breakdown' in video_prompt_raw:
                        # Handle timing_breakdown format
                        timing = video_prompt_raw['timing_breakdown']
                        parts = []
                        for key, value in timing.items():
                            if isinstance(value, str) and ('Hook:' in value or 'Tip:' in value):
                                parts.append(value)
                        video_prompt = " ".join(parts) if parts else str(video_prompt_raw)
                    else:
                        video_prompt = str(video_prompt_raw)
                else:
                    video_prompt = str(video_prompt_raw)
                
                # Ensure prompt is concise for 12-second video
                if len(video_prompt) > 200:
                    video_prompt = video_prompt[:200] + "..."
                
                print(f"   Video Prompt Length: {len(video_prompt)} chars")
                print(f"   Video Prompt Preview: {video_prompt[:100]}...")
                
                # Check if prompt is appropriate for 12-second video
                if len(video_prompt) < 50:
                    print("   ⚠️ Video prompt might be too short")
                elif len(video_prompt) > 150:
                    print("   ⚠️ Video prompt might be too long for 12 seconds")
                    print("   🤖 Optimizing prompt with AI to fit 12-second criteria...")
                    
                    # Use AI to optimize the prompt for 12-second video
                    optimized_prompt = self._optimize_video_prompt(video_prompt)
                    if optimized_prompt and len(optimized_prompt) <= 150:
                        video_prompt = optimized_prompt
                        print(f"   ✅ Prompt optimized: {len(video_prompt)} chars")
                        print(f"   📝 Optimized content: {video_prompt[:100]}...")
                    else:
                        print("   ⚠️ Could not optimize prompt - using truncated version")
                        video_prompt = video_prompt[:150] + "..."
                else:
                    print("   ✅ Video prompt length looks good for 12-second video")
                
                print("✅ Video prompt processing test completed (NO API call made)")
            else:
                print("❌ No video prompt found in content data")
                return {
                    "success": False,
                    "error": "No video prompt found in content data"
                }
            
            # Skip video generation, S3 upload, and blog post creation in test mode
            print("\n🧪 TEST MODE: Skipping video generation, S3 upload, and blog post creation")
            print("✅ Content generation and video prompt processing test completed!")
            
            return {
                "success": True,
                "test_mode": True,
                "content_data": content_data,
                "video_prompt": video_prompt if 'video_prompt' in locals() else None,
                "message": "Test completed successfully - no expensive API calls made"
            }
        
        # Regular mode: Generate video with Sora
        print("\nStep 3: Generating video with Sora...")
        video_prompt_raw = video_prompt_data.get('content') or video_prompt_data.get('prompt')
        
        if not video_prompt_raw:
            return {
                "success": False,
                "error": "No video prompt found in content data"
            }
        
        # Convert structured prompt to string format for Sora
        if isinstance(video_prompt_raw, list):
            # Convert array of prompt objects to a single string
            video_prompt = " ".join([
                f"{item.get('timestamp', item.get('time', ''))}: {item.get('text', item.get('description', ''))}" 
                for item in video_prompt_raw
            ])
        elif isinstance(video_prompt_raw, dict):
            # Handle dictionary format - extract key content
            if 'hook' in video_prompt_raw and 'tip' in video_prompt_raw:
                hook_text = video_prompt_raw['hook'].get('text', video_prompt_raw['hook']) if isinstance(video_prompt_raw['hook'], dict) else video_prompt_raw['hook']
                tip_text = video_prompt_raw['tip'].get('text', video_prompt_raw['tip']) if isinstance(video_prompt_raw['tip'], dict) else video_prompt_raw['tip']
                video_prompt = f"Expert says: '{hook_text} {tip_text}'"
            elif 'content' in video_prompt_raw and isinstance(video_prompt_raw['content'], list):
                # Handle content array format
                video_prompt = " ".join([
                    f"{item.get('timestamp', item.get('time', ''))}: {item.get('text', item.get('description', ''))}" 
                    for item in video_prompt_raw['content']
                ])
            else:
                video_prompt = str(video_prompt_raw)
        else:
            video_prompt = str(video_prompt_raw)
        
        # Ensure prompt is concise for 12-second video
        if len(video_prompt) > 150:
            print("   🤖 Optimizing prompt with AI to fit 12-second criteria...")
            optimized_prompt = self._optimize_video_prompt(video_prompt)
            if optimized_prompt and len(optimized_prompt) <= 150:
                video_prompt = optimized_prompt
                print(f"   ✅ Prompt optimized: {len(video_prompt)} chars")
            else:
                print("   ⚠️ Could not optimize prompt - using truncated version")
                video_prompt = video_prompt[:150] + "..."
        
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
        
        # Step 7: Track generated content for diversity analysis
        print("\nStep 7: Tracking content for diversity analysis...")
        try:
            tracked_content = self.content_generator.track_generated_content(
                content_data=content_data,
                video_id=video_id,
                video_url=video_url
            )
            print(f"✅ Content tracked: {tracked_content.title}")
        except Exception as e:
            print(f"⚠️ Content tracking failed: {e}")
            print("   Continuing without content tracking...")
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 DIVERSE CONTENT PIPELINE COMPLETED!")
        print("="*70)
        print(f"Blog Post: {post.title}")
        print(f"   URL: {post.get_absolute_url()}")
        print(f"   Category: {post.category.name}")
        print(f"   Status: {post.status}")
        if video_url:
            print(f"Video URL: {video_url}")
        print(f"Google Sheets: Updated")
        print(f"Diversity: Content tracked for future optimization")
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

