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
    help = 'Auto-generate skincare content: AI prompt → Sora video → Blog post (fully automated)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Optional: Specific skincare topic (will auto-generate if not provided)'
        )
        parser.add_argument(
            '--category',
            choices=['Cleansing', 'Moisturizing', 'Anti-Aging', 'Acne', 'Sun Protection', 'Sensitive Skin', 'Oily Skin', 'Dry Skin'],
            help='Optional: Filter by skincare category'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of content pieces to generate (default: 1)'
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
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🤖 FULLY AUTOMATED CONTENT GENERATION")
        self.stdout.write("="*70)
        self.stdout.write("This will:")
        self.stdout.write("  1. Generate AI content (video prompt + blog post)")
        self.stdout.write("  2. Create video with Sora")
        self.stdout.write("  3. Upload video to S3")
        self.stdout.write("  4. Add to Google Sheets")
        self.stdout.write("  5. Publish blog post with embedded video")
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
                    publish_immediately=True
                )
                
                if result['success']:
                    success_count += 1
                    results.append(result)
                    
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

