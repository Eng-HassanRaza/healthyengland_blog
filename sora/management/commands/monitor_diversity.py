"""
Monitor Content Diversity Command
Monitor and report on content diversity metrics
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from sora.utils.diversity_engine import TopicDiversityEngine
from sora.utils.smart_selector import SmartTopicSelector
from sora.utils.content_calendar import ContentCalendar
from sora.models import GeneratedContent


class Command(BaseCommand):
    help = 'Monitor content diversity and provide recommendations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to analyze (default: 30)'
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Export diversity report to file'
        )

    def handle(self, *args, **options):
        """Monitor content diversity and provide insights."""
        
        days = options['days']
        export_results = options['export']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📊 CONTENT DIVERSITY MONITORING")
        self.stdout.write("="*70)
        self.stdout.write(f"Analyzing content from the last {days} days...")
        self.stdout.write("="*70 + "\n")
        
        # Initialize monitoring tools
        diversity_engine = TopicDiversityEngine()
        smart_selector = SmartTopicSelector()
        content_calendar = ContentCalendar()
        
        # Get diversity metrics
        self.stdout.write("🔍 Analyzing Diversity Metrics...")
        diversity_score = diversity_engine.get_diversity_score(days)
        diversity_report = diversity_engine.get_diversity_report(days)
        
        self.stdout.write(f"   Overall Diversity Score: {diversity_score['score']:.2f}")
        self.stdout.write(f"   Category Diversity: {diversity_score['category_diversity']:.2f}")
        self.stdout.write(f"   Topic Diversity: {diversity_score['topic_diversity']:.2f}")
        
        # Get content analysis
        self.stdout.write("\n📈 Content Pattern Analysis...")
        content_analysis = smart_selector.analyze_content_patterns(days)
        
        self.stdout.write(f"   Total Content: {content_analysis['total_content']}")
        self.stdout.write(f"   Categories Used: {len(content_analysis['category_distribution'])}")
        
        if content_analysis['category_distribution']:
            self.stdout.write(f"   Category Distribution:")
            for category, count in sorted(content_analysis['category_distribution'].items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"     • {category}: {count}")
        
        # Get next content strategy
        self.stdout.write("\n🚀 Next Content Strategy...")
        strategy = smart_selector.get_next_content_strategy()
        
        self.stdout.write(f"   Recommended Category: {strategy['recommended_category']}")
        self.stdout.write(f"   Strategy: {strategy['strategy']}")
        
        # Get content calendar recommendations
        self.stdout.write("\n📅 Content Calendar Analysis...")
        calendar_recommendations = content_calendar.get_content_recommendations(look_ahead_days=7)
        
        if calendar_recommendations['recommendations']:
            self.stdout.write(f"   Calendar Recommendations:")
            for rec in calendar_recommendations['recommendations']:
                self.stdout.write(f"     • {rec}")
        
        # Get database content analysis
        self.stdout.write("\n💾 Database Content Analysis...")
        recent_content = GeneratedContent.get_recent_content(days)
        
        self.stdout.write(f"   Tracked Content: {recent_content.count()}")
        
        if recent_content.exists():
            categories_used = set(content.category for content in recent_content)
            self.stdout.write(f"   Categories in Database: {len(categories_used)}")
            self.stdout.write(f"   Categories: {', '.join(sorted(categories_used))}")
            
            # Check for repetitive patterns
            topics = [content.topic for content in recent_content]
            if len(topics) > 1:
                similarities = []
                for i in range(len(topics)):
                    for j in range(i + 1, len(topics)):
                        similarity = diversity_engine.calculate_topic_similarity(topics[i], topics[j])
                        similarities.append(similarity)
                
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    max_similarity = max(similarities)
                    self.stdout.write(f"   Average Topic Similarity: {avg_similarity:.2f}")
                    self.stdout.write(f"   Maximum Topic Similarity: {max_similarity:.2f}")
                    
                    if max_similarity > 0.4:
                        self.stdout.write(self.style.WARNING("   ⚠️ High similarity detected - consider more diverse topics"))
                    else:
                        self.stdout.write(self.style.SUCCESS("   ✅ Good topic diversity"))
        else:
            self.stdout.write("   No tracked content found in database")
        
        # Generate recommendations
        self.stdout.write("\n💡 Diversity Recommendations...")
        recommendations = self._generate_diversity_recommendations(
            diversity_score, content_analysis, recent_content.count()
        )
        
        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f"   {i}. {rec}")
        
        # Export results if requested
        if export_results:
            self._export_diversity_report(diversity_score, content_analysis, strategy)
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("✅ Diversity monitoring completed!")
        self.stdout.write("="*70 + "\n")

    def _generate_diversity_recommendations(self, diversity_score, content_analysis, content_count):
        """Generate specific diversity recommendations."""
        recommendations = []
        
        # Overall diversity recommendations
        if diversity_score['score'] < 0.6:
            recommendations.append("Overall diversity is low - focus on more varied content across categories")
        elif diversity_score['score'] < 0.8:
            recommendations.append("Diversity is moderate - continue improving content variety")
        else:
            recommendations.append("Excellent diversity - maintain current approach")
        
        # Category diversity recommendations
        if content_analysis['total_content'] > 0:
            categories_used = len(content_analysis['category_distribution'])
            if categories_used < 5:
                recommendations.append(f"Only {categories_used} categories used - expand to more health categories")
            elif categories_used < 8:
                recommendations.append(f"Good category usage ({categories_used} categories) - consider adding more")
            else:
                recommendations.append(f"Excellent category diversity ({categories_used} categories)")
        
        # Content volume recommendations
        if content_count == 0:
            recommendations.append("No content tracked - start generating diverse content")
        elif content_count < 5:
            recommendations.append("Low content volume - increase generation frequency")
        elif content_count < 20:
            recommendations.append("Good content volume - maintain current frequency")
        else:
            recommendations.append("High content volume - ensure quality over quantity")
        
        # Topic similarity recommendations
        if content_analysis.get('most_common_keywords'):
            common_keywords = content_analysis['most_common_keywords'][:3]
            if any(count > 3 for _, count in common_keywords):
                recommendations.append("Some keywords are overused - diversify topic vocabulary")
        
        return recommendations

    def _export_diversity_report(self, diversity_score, content_analysis, strategy):
        """Export diversity report to file."""
        import json
        from datetime import datetime
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'diversity_score': diversity_score,
            'content_analysis': content_analysis,
            'strategy': strategy
        }
        
        filename = f"diversity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.stdout.write(f"\n📁 Diversity report exported to: {filename}")
