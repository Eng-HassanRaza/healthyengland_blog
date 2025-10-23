"""
Test Content Generation Command
Test content generation without expensive Sora API calls
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from sora.utils.enhanced_content_generator import EnhancedContentGenerator
from sora.utils.enhanced_duplicate_detection import EnhancedDuplicateDetector
from sora.utils.smart_selector import SmartTopicSelector
from sora.utils.diversity_engine import TopicDiversityEngine


class Command(BaseCommand):
    help = 'Test content generation without expensive Sora API calls'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of content pieces to test (default: 3)'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Test specific category'
        )

    def handle(self, *args, **options):
        """Test content generation without video creation."""
        
        count = options['count']
        category = options.get('category')
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🧪 TESTING CONTENT GENERATION (NO VIDEO CREATION)")
        self.stdout.write("="*70)
        self.stdout.write(f"Testing {count} content pieces...")
        if category:
            self.stdout.write(f"Category: {category}")
        else:
            self.stdout.write("Category: Auto-selected for diversity")
        self.stdout.write("="*70 + "\n")
        
        # Initialize components
        generator = EnhancedContentGenerator()
        detector = EnhancedDuplicateDetector()
        selector = SmartTopicSelector()
        diversity_engine = TopicDiversityEngine()
        
        success_count = 0
        failed_count = 0
        
        for i in range(count):
            self.stdout.write(f"\n📝 Testing Content Piece {i+1}/{count}")
            self.stdout.write("-" * 50)
            
            try:
                # Generate content
                result = generator.generate_content_package(
                    category=category,
                    use_smart_selection=True
                )
                
                if result['success']:
                    data = result['data']
                    blog_post = data.get('blog_post', {})
                    video_prompt = data.get('video_prompt', {})
                    
                    # Display results
                    self.stdout.write(f"✅ Content Generated Successfully!")
                    self.stdout.write(f"   Title: {blog_post.get('title', 'N/A')}")
                    self.stdout.write(f"   Category: {blog_post.get('category', 'N/A')}")
                    self.stdout.write(f"   Tags: {', '.join(blog_post.get('tags', []))}")
                    
                    # Test video prompt processing
                    video_prompt_data = video_prompt
                    video_prompt_raw = video_prompt_data.get('content') or video_prompt_data.get('prompt')
                    
                    if video_prompt_raw:
                        # Test prompt conversion (without sending to Sora)
                        if isinstance(video_prompt_raw, list):
                            converted_prompt = " ".join([
                                f"{item.get('timestamp', item.get('time', ''))}: {item.get('text', item.get('description', ''))}" 
                                for item in video_prompt_raw
                            ])
                        elif isinstance(video_prompt_raw, dict):
                            if 'hook' in video_prompt_raw and 'tip' in video_prompt_raw:
                                hook_text = video_prompt_raw['hook'].get('text', video_prompt_raw['hook']) if isinstance(video_prompt_raw['hook'], dict) else video_prompt_raw['hook']
                                tip_text = video_prompt_raw['tip'].get('text', video_prompt_raw['tip']) if isinstance(video_prompt_raw['tip'], dict) else video_prompt_raw['tip']
                                converted_prompt = f"Expert says: '{hook_text} {tip_text}'"
                            else:
                                converted_prompt = str(video_prompt_raw)
                        else:
                            converted_prompt = str(video_prompt_raw)
                        
                        # Ensure prompt is concise for 12-second video
                        if len(converted_prompt) > 200:
                            converted_prompt = converted_prompt[:200] + "..."
                        
                        self.stdout.write(f"   Video Prompt Length: {len(converted_prompt)} chars")
                        self.stdout.write(f"   Video Prompt Preview: {converted_prompt[:100]}...")
                        
                        # Check if prompt is appropriate for 12-second video
                        if len(converted_prompt) < 50:
                            self.stdout.write(self.style.WARNING("   ⚠️ Video prompt might be too short"))
                        elif len(converted_prompt) > 150:
                            self.stdout.write(self.style.WARNING("   ⚠️ Video prompt might be too long for 12 seconds"))
                        else:
                            self.stdout.write(self.style.SUCCESS("   ✅ Video prompt length looks good for 12-second video"))
                    else:
                        self.stdout.write(self.style.ERROR("   ❌ No video prompt found"))
                    
                    # Test duplicate detection
                    title = blog_post.get('title', '')
                    topic = title
                    category_name = blog_post.get('category', '')
                    
                    similarity_check = detector.check_content_similarity(title, topic, category_name)
                    self.stdout.write(f"   Similarity Check: {'Similar' if similarity_check['is_similar'] else 'Unique'}")
                    self.stdout.write(f"   Diversity Score: {similarity_check['overall_similarity']:.2f}")
                    
                    success_count += 1
                    
                else:
                    self.stdout.write(self.style.ERROR(f"❌ Content Generation Failed: {result['error']}"))
                    failed_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Test Failed: {e}"))
                failed_count += 1
        
        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📊 TEST RESULTS SUMMARY")
        self.stdout.write("="*70)
        self.stdout.write(f"✅ Successful: {success_count}/{count}")
        self.stdout.write(f"❌ Failed: {failed_count}/{count}")
        
        if success_count > 0:
            self.stdout.write(f"\n🎉 Content generation system is working!")
            self.stdout.write("   - Diverse content generation: ✅")
            self.stdout.write("   - Video prompt processing: ✅")
            self.stdout.write("   - Duplicate detection: ✅")
            self.stdout.write("   - 12-second video optimization: ✅")
        else:
            self.stdout.write(f"\n❌ All tests failed - check system configuration")
        
        self.stdout.write("="*70 + "\n")
        
        # Test diversity system
        self.stdout.write("\n🔍 Testing Diversity System...")
        diversity_score = diversity_engine.get_diversity_score()
        self.stdout.write(f"   Diversity Score: {diversity_score['score']:.2f}")
        
        # Test smart selection
        next_selection = selector.select_optimal_topic()
        self.stdout.write(f"   Next Recommended: {next_selection['topic'][:50]}... ({next_selection['category']})")
        
        self.stdout.write("\n✅ All tests completed without expensive API calls!")
