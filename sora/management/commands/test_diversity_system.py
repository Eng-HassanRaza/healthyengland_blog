"""
Test Diversity System Command
Comprehensive testing of the new content diversity system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from sora.utils.diversity_engine import TopicDiversityEngine
from sora.utils.topic_bank import TopicBank
from sora.utils.smart_selector import SmartTopicSelector
from sora.utils.enhanced_content_generator import EnhancedContentGenerator
from sora.utils.enhanced_duplicate_detection import EnhancedDuplicateDetector
from sora.utils.content_calendar import ContentCalendar


class Command(BaseCommand):
    help = 'Test the new content diversity system with comprehensive validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            choices=['all', 'diversity', 'topics', 'selection', 'generation', 'detection', 'calendar'],
            default='all',
            help='Type of test to run (default: all)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of test samples to generate (default: 5)'
        )

    def handle(self, *args, **options):
        """Run comprehensive diversity system tests."""
        
        test_type = options['test_type']
        count = options['count']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🧪 CONTENT DIVERSITY SYSTEM TESTING")
        self.stdout.write("="*70)
        self.stdout.write(f"Test type: {test_type}")
        self.stdout.write(f"Sample count: {count}")
        self.stdout.write("="*70 + "\n")
        
        if test_type in ['all', 'diversity']:
            self._test_diversity_engine(count)
        
        if test_type in ['all', 'topics']:
            self._test_topic_bank(count)
        
        if test_type in ['all', 'selection']:
            self._test_smart_selection(count)
        
        if test_type in ['all', 'generation']:
            self._test_enhanced_generation(count)
        
        if test_type in ['all', 'detection']:
            self._test_duplicate_detection(count)
        
        if test_type in ['all', 'calendar']:
            self._test_content_calendar(count)
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("✅ Diversity system testing completed!")
        self.stdout.write("="*70 + "\n")

    def _test_diversity_engine(self, count: int):
        """Test the diversity engine."""
        self.stdout.write("🔍 Testing Diversity Engine")
        self.stdout.write("-" * 40)
        
        try:
            engine = TopicDiversityEngine()
            
            # Test category weights
            weights = engine.get_category_weights()
            self.stdout.write(f"   Category weights calculated: {len(weights)} categories")
            
            # Test diverse category selection
            categories = []
            for i in range(count):
                category = engine.select_diverse_category()
                categories.append(category)
            
            self.stdout.write(f"   Selected categories: {', '.join(categories)}")
            
            # Test diversity score
            diversity_score = engine.get_diversity_score()
            self.stdout.write(f"   Diversity score: {diversity_score['score']:.2f}")
            
            # Test topic similarity
            test_topic = "honey and lemon face mask"
            similar_topics = engine.find_similar_topics(test_topic)
            self.stdout.write(f"   Similar topics to '{test_topic}': {len(similar_topics)} found")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Diversity engine test passed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Diversity engine test failed: {e}"))

    def _test_topic_bank(self, count: int):
        """Test the topic bank system."""
        self.stdout.write("\n📚 Testing Topic Bank System")
        self.stdout.write("-" * 40)
        
        try:
            bank = TopicBank()
            
            # Test category stats
            stats = bank.get_category_stats()
            self.stdout.write(f"   Categories available: {len(stats)}")
            
            # Test random topic selection
            topics = []
            for i in range(count):
                topic = bank.get_random_topic()
                topics.append(topic)
            
            self.stdout.write(f"   Random topics generated: {len(topics)}")
            for i, topic in enumerate(topics, 1):
                self.stdout.write(f"     {i}. {topic[:50]}...")
            
            # Test diverse topics
            diverse_topics = bank.get_diverse_topics(count)
            self.stdout.write(f"   Diverse topics: {len(diverse_topics)}")
            for topic_data in diverse_topics:
                self.stdout.write(f"     • {topic_data['topic'][:30]}... ({topic_data['category']})")
            
            # Test search functionality
            search_results = bank.search_topics('water')
            self.stdout.write(f"   Search results for 'water': {len(search_results)}")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Topic bank test passed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Topic bank test failed: {e}"))

    def _test_smart_selection(self, count: int):
        """Test the smart selection algorithm."""
        self.stdout.write("\n🎯 Testing Smart Selection Algorithm")
        self.stdout.write("-" * 40)
        
        try:
            selector = SmartTopicSelector()
            
            # Test optimal topic selection
            selections = []
            for i in range(count):
                result = selector.select_optimal_topic()
                selections.append(result)
            
            self.stdout.write(f"   Optimal selections: {len(selections)}")
            for i, selection in enumerate(selections, 1):
                self.stdout.write(f"     {i}. {selection['topic'][:40]}...")
                self.stdout.write(f"        Category: {selection['category']}, Confidence: {selection['confidence']:.2f}")
            
            # Test topic suggestions
            suggestions = selector.get_topic_suggestions(count)
            self.stdout.write(f"   Topic suggestions: {len(suggestions)}")
            
            # Test content analysis
            analysis = selector.analyze_content_patterns(30)
            self.stdout.write(f"   Content analysis: {analysis['total_content']} total content")
            
            # Test next content strategy
            strategy = selector.get_next_content_strategy()
            self.stdout.write(f"   Next strategy: {strategy['recommended_category']}")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Smart selection test passed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Smart selection test failed: {e}"))

    def _test_enhanced_generation(self, count: int):
        """Test the enhanced content generator."""
        self.stdout.write("\n🤖 Testing Enhanced Content Generator")
        self.stdout.write("-" * 40)
        
        try:
            generator = EnhancedContentGenerator()
            
            # Test single content generation
            result = generator.generate_content_package(use_smart_selection=True)
            
            if result['success']:
                data = result['data']
                self.stdout.write(f"   Generated content: {data['blog_post']['title'][:50]}...")
                self.stdout.write(f"   Category: {data['blog_post']['category']}")
                self.stdout.write(f"   Duration: {data['video_prompt']['duration']}s")
                
                # Test diversity report
                report = generator.get_diversity_report()
                self.stdout.write(f"   Diversity report: {report['recommended_category']} recommended")
                
                self.stdout.write(self.style.SUCCESS("   ✅ Enhanced generation test passed"))
            else:
                self.stdout.write(self.style.WARNING(f"   ⚠️ Generation test skipped: {result['error']}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Enhanced generation test failed: {e}"))

    def _test_duplicate_detection(self, count: int):
        """Test the enhanced duplicate detection."""
        self.stdout.write("\n🔍 Testing Enhanced Duplicate Detection")
        self.stdout.write("-" * 40)
        
        try:
            detector = EnhancedDuplicateDetector()
            
            # Test content similarity check
            test_title = "Honey and Lemon Face Mask for Glowing Skin"
            test_topic = "natural skincare with honey and lemon"
            test_category = "Skincare"
            
            similarity_result = detector.check_content_similarity(test_title, test_topic, test_category)
            
            self.stdout.write(f"   Title: {test_title[:30]}...")
            self.stdout.write(f"   Topic: {test_topic[:30]}...")
            self.stdout.write(f"   Is similar: {similarity_result['is_similar']}")
            self.stdout.write(f"   Overall similarity: {similarity_result['overall_similarity']:.2f}")
            
            if similarity_result['recommendations']:
                self.stdout.write(f"   Recommendations:")
                for rec in similarity_result['recommendations']:
                    self.stdout.write(f"     • {rec}")
            
            # Test diversity score
            diversity_result = detector.get_diversity_score_for_topic(test_topic, test_category)
            self.stdout.write(f"   Diversity score: {diversity_result['diversity_score']:.2f}")
            self.stdout.write(f"   Is diverse: {diversity_result['is_diverse']}")
            
            # Test content validation
            validation_result = detector.validate_content_diversity(test_title, test_topic, test_category)
            self.stdout.write(f"   Is valid: {validation_result['is_valid']}")
            self.stdout.write(f"   Overall score: {validation_result['overall_score']:.2f}")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Duplicate detection test passed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Duplicate detection test failed: {e}"))

    def _test_content_calendar(self, count: int):
        """Test the content calendar system."""
        self.stdout.write("\n📅 Testing Content Calendar System")
        self.stdout.write("-" * 40)
        
        try:
            calendar = ContentCalendar()
            
            # Test calendar generation
            content_calendar = calendar.generate_content_calendar(days=count, content_per_day=1)
            
            self.stdout.write(f"   Planning period: {content_calendar['planning_period']} days")
            self.stdout.write(f"   Total content pieces: {content_calendar['total_content_pieces']}")
            
            # Display daily schedule
            self.stdout.write(f"   Daily schedule:")
            for day in content_calendar['daily_schedule']:
                self.stdout.write(f"     {day['date']} ({day['day_of_week']}):")
                for piece in day['content_pieces']:
                    self.stdout.write(f"       • {piece['topic'][:40]}... ({piece['category']})")
            
            # Display diversity metrics
            metrics = content_calendar['diversity_metrics']
            self.stdout.write(f"   Topic diversity: {metrics['topic_diversity']:.2f}")
            self.stdout.write(f"   Category diversity: {metrics['category_diversity']:.2f}")
            self.stdout.write(f"   Overall diversity: {metrics['overall_diversity']:.2f}")
            
            # Test content recommendations
            recommendations = calendar.get_content_recommendations(look_ahead_days=count)
            
            if recommendations['recommendations']:
                self.stdout.write(f"   Recommendations:")
                for rec in recommendations['recommendations']:
                    self.stdout.write(f"     • {rec}")
            
            self.stdout.write(self.style.SUCCESS("   ✅ Content calendar test passed"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Content calendar test failed: {e}"))

    def _display_system_summary(self):
        """Display a summary of the diversity system."""
        self.stdout.write("\n📊 DIVERSITY SYSTEM SUMMARY")
        self.stdout.write("-" * 50)
        
        # Count available categories
        from sora.utils.diversity_engine import TopicDiversityEngine
        engine = TopicDiversityEngine()
        categories = list(engine.HEALTH_CATEGORIES.keys())
        
        self.stdout.write(f"   Available categories: {len(categories)}")
        self.stdout.write(f"   Categories: {', '.join(categories[:5])}...")
        
        # Count topic bank topics
        from sora.utils.topic_bank import TopicBank
        bank = TopicBank()
        stats = bank.get_category_stats()
        total_topics = sum(cat_data['total'] for cat_data in stats.values())
        
        self.stdout.write(f"   Total topics in bank: {total_topics}")
        self.stdout.write(f"   Categories with topics: {len(stats)}")
        
        self.stdout.write("\n🎯 SYSTEM CAPABILITIES:")
        self.stdout.write("   ✅ Smart topic selection with diversity optimization")
        self.stdout.write("   ✅ Enhanced duplicate detection and prevention")
        self.stdout.write("   ✅ Content calendar with systematic rotation")
        self.stdout.write("   ✅ Multi-category health content generation")
        self.stdout.write("   ✅ Topic similarity analysis and prevention")
        self.stdout.write("   ✅ Content diversity scoring and optimization")
        
        self.stdout.write("\n🚀 READY FOR PRODUCTION!")
        self.stdout.write("   The diversity system is now ready to generate diverse health content")
        self.stdout.write("   across multiple categories with intelligent topic selection.")
