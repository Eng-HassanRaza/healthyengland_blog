"""
Django management command for automated content generation
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import sys
from pathlib import Path

# Add sora utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'utils'))

from auto_content_pipeline import AutoContentPipeline


class Command(BaseCommand):
    help = 'Generate automated health & fitness content (video + blog post)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Specific topic (optional, will auto-generate if not provided)'
        )
        parser.add_argument(
            '--category',
            choices=['Nutrition', 'Fitness', 'Mental Health', 'Wellness', 'Sleep'],
            help='Category filter (optional)'
        )
        parser.add_argument(
            '--draft',
            action='store_true',
            help='Save blog post as draft instead of publishing'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of content pieces to generate (default: 1)'
        )

    def handle(self, *args, **options):
        topic = options.get('topic')
        category = options.get('category')
        draft = options.get('draft')
        count = options.get('count', 1)
        
        self.stdout.write("="*70)
        self.stdout.write("🤖 AUTOMATED CONTENT GENERATION")
        self.stdout.write("="*70)
        self.stdout.write(f"Generating {count} content piece(s)")
        if topic:
            self.stdout.write(f"Topic: {topic}")
        if category:
            self.stdout.write(f"Category: {category}")
        self.stdout.write(f"Status: {'Draft' if draft else 'Published'}")
        self.stdout.write("="*70 + "\n")
        
        try:
            pipeline = AutoContentPipeline()
        except Exception as e:
            raise CommandError(f"Pipeline initialization failed: {e}")
        
        success_count = 0
        failed_count = 0
        
        for i in range(count):
            if count > 1:
                self.stdout.write(f"\n{'='*70}")
                self.stdout.write(f"📝 Generating content piece {i+1}/{count}")
                self.stdout.write("="*70 + "\n")
            
            try:
                result = pipeline.run(
                    topic=topic,
                    category=category,
                    publish_immediately=not draft
                )
                
                if result['success']:
                    success_count += 1
                    post = result['post']
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Successfully created: {post.title}"
                    ))
                    self.stdout.write(f"   URL: https://healthyengland.com{post.get_absolute_url()}")
                    self.stdout.write(f"   Video: {result.get('video_url', 'N/A')}")
                    
                else:
                    failed_count += 1
                    error = result.get('error', 'Unknown error')
                    
                    if result.get('duplicate'):
                        self.stdout.write(self.style.WARNING(f"⚠️ Skipped (duplicate): {error}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"❌ Failed: {error}"))
                
                # Delay between generations if creating multiple
                if i < count - 1:
                    self.stdout.write("\n⏳ Waiting 5 seconds before next generation...")
                    time.sleep(5)
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f"❌ Error: {e}"))
                import traceback
                traceback.print_exc()
        
        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📊 GENERATION COMPLETE")
        self.stdout.write("="*70)
        self.stdout.write(f"✅ Successful: {success_count}")
        self.stdout.write(f"❌ Failed: {failed_count}")
        self.stdout.write(f"📈 Success Rate: {(success_count/count)*100:.1f}%")
        self.stdout.write("="*70)
        
        if failed_count > 0:
            raise CommandError(f"{failed_count} content generation(s) failed")

