"""
Simplified automated content generation command
Single command to generate everything: video + blog post
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys
from pathlib import Path

# Add sora utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'utils'))

from sora.utils.auto_content_pipeline import AutoContentPipeline


class Command(BaseCommand):
    help = 'Auto-generate diverse health content: AI prompt → Sora video → Blog post (fully automated with diversity optimization)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Optional: Specific health topic (will auto-generate if not provided)'
        )
        parser.add_argument(
            '--category',
            choices=['Nutrition', 'Fitness', 'Mental Health', 'Sleep', 'Hydration', 'Skincare', 'Wellness', 'Digestive Health', 'Immune System', 'Weight Management'],
            help='Optional: Filter by health category'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of content pieces to generate (default: 1)'
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Test mode - skip expensive video generation, only test content creation'
        )

    def handle(self, *args, **options):
        """
        Single command that does everything:
        1. OpenAI generates video prompt + blog post
        2. Sora generates video
        3. Video uploads to S3
        4. S3 URL added to Google Sheets
        5. Blog post published with embedded video
        """
        
        topic = options.get('topic')
        category = options.get('category')
        count = options.get('count', 1)
        test_mode = options.get('test_mode', False)
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🤖 DIVERSE HEALTH CONTENT GENERATION")
        self.stdout.write("="*70)
        if test_mode:
            self.stdout.write("🧪 TEST MODE - NO EXPENSIVE VIDEO GENERATION")
            self.stdout.write("="*70)
            self.stdout.write("This will:")
            self.stdout.write("  1. Generate diverse AI content (video prompt + blog post)")
            self.stdout.write("  2. Check for content similarity and diversity")
            self.stdout.write("  3. Test video prompt processing (NO Sora API call)")
            self.stdout.write("  4. Validate 12-second video optimization")
            self.stdout.write("  5. Track content for diversity analysis")
            self.stdout.write("="*70)
        else:
            self.stdout.write("This will:")
            self.stdout.write("  1. Generate diverse AI content (video prompt + blog post)")
            self.stdout.write("  2. Check for content similarity and diversity")
            self.stdout.write("  3. Create video with Sora")
            self.stdout.write("  4. Upload video to S3")
            self.stdout.write("  5. Add to Google Sheets")
            self.stdout.write("  6. Publish blog post with embedded video")
            self.stdout.write("  7. Track content for diversity optimization")
            self.stdout.write("="*70)
        
        if topic:
            self.stdout.write(f"Topic: {topic}")
        else:
            self.stdout.write("Topic: Auto-generated")
        
        if category:
            self.stdout.write(f"Category: {category}")
        
        self.stdout.write(f"Count: {count}")
        self.stdout.write("="*70 + "\n")
        
        try:
            pipeline = AutoContentPipeline()
        except Exception as e:
            raise CommandError(f"Failed to initialize pipeline: {e}")
        
        success_count = 0
        failed_count = 0
        results = []
        
        for i in range(count):
            if count > 1:
                self.stdout.write(f"\n{'~'*70}")
                self.stdout.write(f"📝 Content Piece {i+1}/{count}")
                self.stdout.write("~"*70 + "\n")
            
            try:
                result = pipeline.run(
                    topic=topic,
                    category=category,
                    publish_immediately=True,
                    test_mode=test_mode
                )
                
                if result['success']:
                    success_count += 1
                    results.append(result)
                    
                    if result.get('test_mode'):
                        # Test mode - no post created
                        self.stdout.write(self.style.SUCCESS(
                            f"\n✅ Test completed successfully!"
                        ))
                        self.stdout.write(f"   Title: {result['content_data']['blog_post']['title']}")
                        self.stdout.write(f"   Category: {result['content_data']['blog_post']['category']}")
                        self.stdout.write(f"   Video Prompt: {result.get('video_prompt', 'N/A')[:50]}...")
                        self.stdout.write(f"   Message: {result.get('message', 'Test completed')}")
                    else:
                        # Regular mode - post created
                        post = result['post']
                        self.stdout.write(self.style.SUCCESS(
                            f"\n✅ Content created successfully!"
                        ))
                        self.stdout.write(f"   Title: {post.title}")
                        self.stdout.write(f"   URL: https://healthyengland.com{post.get_absolute_url()}")
                        self.stdout.write(f"   Category: {post.category.name}")
                        self.stdout.write(f"   Video: {result.get('video_url', 'N/A')}")
                    
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    
                    if result.get('duplicate'):
                        self.stdout.write(self.style.WARNING(
                            f"\n⚠️ Skipped (duplicate): {error}"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"\n❌ Failed: {error}"
                        ))
                
                # Small delay between generations
                if i < count - 1:
                    import time
                    self.stdout.write("\n⏳ Waiting 10 seconds...")
                    time.sleep(10)
                    
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n\n⚠️ Interrupted by user"))
                break
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"\n❌ Error: {e}"))
                import traceback
                traceback.print_exc()
        
        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📊 FINAL SUMMARY")
        self.stdout.write("="*70)
        self.stdout.write(f"✅ Successful: {success_count}/{count}")
        self.stdout.write(f"❌ Failed: {failed_count}/{count}")
        
        if success_count > 0:
            self.stdout.write(f"\n🎉 {success_count} new blog post(s) published!")
            self.stdout.write("Visit: https://healthyengland.com")
        
        self.stdout.write("="*70 + "\n")
        
        if failed_count == count:
            raise CommandError("All content generation attempts failed")

