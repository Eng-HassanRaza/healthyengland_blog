"""
Content History Analysis Command
Analyzes existing video metadata and creates topic usage patterns
"""

import json
import os
from pathlib import Path
from typing import Dict, List
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta

from sora.utils.diversity_engine import TopicDiversityEngine
from sora.utils.smart_selector import SmartTopicSelector
from sora.models import GeneratedContent


class Command(BaseCommand):
    help = 'Analyze existing video metadata and create topic usage patterns'

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
            help='Export analysis results to JSON file'
        )

    def handle(self, *args, **options):
        """Analyze content history and generate insights."""
        
        days = options['days']
        export_results = options['export']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📊 CONTENT HISTORY ANALYSIS")
        self.stdout.write("="*70)
        self.stdout.write(f"Analyzing content from the last {days} days...")
        self.stdout.write("="*70 + "\n")
        
        # Initialize analysis tools
        diversity_engine = TopicDiversityEngine()
        smart_selector = SmartTopicSelector()
        
        # Step 1: Analyze existing video metadata files
        self.stdout.write("Step 1: Analyzing existing video metadata...")
        video_analysis = self._analyze_video_metadata()
        
        # Step 2: Analyze database content
        self.stdout.write("\nStep 2: Analyzing database content...")
        db_analysis = self._analyze_database_content(days)
        
        # Step 3: Generate diversity insights
        self.stdout.write("\nStep 3: Generating diversity insights...")
        diversity_insights = self._generate_diversity_insights(days)
        
        # Step 4: Create topic usage patterns
        self.stdout.write("\nStep 4: Creating topic usage patterns...")
        usage_patterns = self._create_usage_patterns(days)
        
        # Step 5: Generate recommendations
        self.stdout.write("\nStep 5: Generating recommendations...")
        recommendations = self._generate_recommendations(days)
        
        # Compile final report
        analysis_report = {
            'analysis_date': timezone.now().isoformat(),
            'analysis_period_days': days,
            'video_metadata_analysis': video_analysis,
            'database_content_analysis': db_analysis,
            'diversity_insights': diversity_insights,
            'usage_patterns': usage_patterns,
            'recommendations': recommendations
        }
        
        # Display results
        self._display_analysis_results(analysis_report)
        
        # Export if requested
        if export_results:
            self._export_analysis_results(analysis_report)
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write("✅ Content history analysis completed!")
        self.stdout.write("="*70 + "\n")

    def _analyze_video_metadata(self) -> Dict:
        """Analyze existing video metadata files."""
        metadata_dir = Path("generated_videos")
        metadata_files = list(metadata_dir.glob("video_metadata_*.json"))
        
        analysis = {
            'total_metadata_files': len(metadata_files),
            'video_prompts': [],
            'creation_dates': [],
            'video_ids': []
        }
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                
                analysis['video_prompts'].append(data.get('prompt', ''))
                analysis['creation_dates'].append(data.get('timestamp', ''))
                analysis['video_ids'].append(data.get('video_id', ''))
                
            except Exception as e:
                self.stdout.write(f"⚠️ Error reading {metadata_file}: {e}")
        
        # Analyze prompt patterns
        prompt_analysis = self._analyze_prompt_patterns(analysis['video_prompts'])
        analysis['prompt_patterns'] = prompt_analysis
        
        return analysis

    def _analyze_prompt_patterns(self, prompts: List[str]) -> Dict:
        """Analyze patterns in video prompts."""
        if not prompts:
            return {'total_prompts': 0, 'common_keywords': [], 'pattern_analysis': 'No prompts found'}
        
        # Extract keywords from prompts
        diversity_engine = TopicDiversityEngine()
        all_keywords = []
        
        for prompt in prompts:
            keywords = diversity_engine.extract_topic_keywords(prompt)
            all_keywords.extend(keywords)
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Get most common keywords
        common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Analyze for repetitive patterns
        repetitive_keywords = [kw for kw, count in common_keywords if count > 2]
        
        return {
            'total_prompts': len(prompts),
            'common_keywords': common_keywords,
            'repetitive_keywords': repetitive_keywords,
            'diversity_score': len(set(all_keywords)) / len(all_keywords) if all_keywords else 0
        }

    def _analyze_database_content(self, days: int) -> Dict:
        """Analyze content in the database."""
        recent_content = GeneratedContent.get_recent_content(days)
        
        analysis = {
            'total_content': recent_content.count(),
            'categories_used': {},
            'difficulty_distribution': {},
            'publication_status': {},
            'topic_keywords': []
        }
        
        for content in recent_content:
            # Category analysis
            category = content.category
            analysis['categories_used'][category] = analysis['categories_used'].get(category, 0) + 1
            
            # Difficulty analysis
            difficulty = content.difficulty_level
            analysis['difficulty_distribution'][difficulty] = analysis['difficulty_distribution'].get(difficulty, 0) + 1
            
            # Publication status
            status = 'published' if content.is_published else 'draft'
            analysis['publication_status'][status] = analysis['publication_status'].get(status, 0) + 1
            
            # Topic keywords
            if content.topic_keywords:
                analysis['topic_keywords'].extend(content.topic_keywords)
        
        # Analyze topic keyword patterns
        if analysis['topic_keywords']:
            keyword_counts = {}
            for keyword in analysis['topic_keywords']:
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            analysis['most_common_keywords'] = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        else:
            analysis['most_common_keywords'] = []
        
        return analysis

    def _generate_diversity_insights(self, days: int) -> Dict:
        """Generate diversity insights using the diversity engine."""
        diversity_engine = TopicDiversityEngine()
        smart_selector = SmartTopicSelector()
        
        # Get diversity score
        diversity_score = diversity_engine.get_diversity_score(days)
        
        # Get diversity report
        diversity_report = diversity_engine.get_diversity_report(days)
        
        # Get content analysis
        content_analysis = smart_selector.analyze_content_patterns(days)
        
        return {
            'diversity_score': diversity_score,
            'diversity_report': diversity_report,
            'content_analysis': content_analysis
        }

    def _create_usage_patterns(self, days: int) -> Dict:
        """Create topic usage patterns."""
        recent_content = GeneratedContent.get_recent_content(days)
        
        patterns = {
            'category_rotation': {},
            'topic_similarity': {},
            'generation_frequency': {},
            'content_trends': {}
        }
        
        # Analyze category rotation
        categories = [content.category for content in recent_content]
        for i, category in enumerate(categories):
            if i > 0:
                prev_category = categories[i-1]
                key = f"{prev_category} -> {category}"
                patterns['category_rotation'][key] = patterns['category_rotation'].get(key, 0) + 1
        
        # Analyze topic similarity
        topics = [content.topic for content in recent_content]
        diversity_engine = TopicDiversityEngine()
        
        similarity_scores = []
        for i in range(len(topics)):
            for j in range(i + 1, len(topics)):
                similarity = diversity_engine.calculate_topic_similarity(topics[i], topics[j])
                similarity_scores.append(similarity)
        
        if similarity_scores:
            patterns['topic_similarity'] = {
                'average_similarity': sum(similarity_scores) / len(similarity_scores),
                'max_similarity': max(similarity_scores),
                'high_similarity_count': len([s for s in similarity_scores if s > 0.4])
            }
        
        # Analyze generation frequency
        generation_dates = [content.generated_at.date() for content in recent_content]
        date_counts = {}
        for date in generation_dates:
            date_counts[date] = date_counts.get(date, 0) + 1
        
        patterns['generation_frequency'] = {
            'most_active_dates': sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'average_daily_generation': len(recent_content) / days if days > 0 else 0
        }
        
        return patterns

    def _generate_recommendations(self, days: int) -> Dict:
        """Generate recommendations based on analysis."""
        smart_selector = SmartTopicSelector()
        diversity_engine = TopicDiversityEngine()
        
        # Get next content strategy
        strategy = smart_selector.get_next_content_strategy()
        
        # Get diversity recommendations
        diversity_report = diversity_engine.get_diversity_report(days)
        
        # Generate specific recommendations
        recommendations = {
            'next_content_strategy': strategy,
            'diversity_improvements': [],
            'category_recommendations': [],
            'topic_diversity_suggestions': []
        }
        
        # Analyze current patterns for specific recommendations
        recent_content = GeneratedContent.get_recent_content(days)
        
        # Category diversity recommendations
        categories_used = set(content.category for content in recent_content)
        all_categories = set(diversity_engine.HEALTH_CATEGORIES.keys())
        unused_categories = all_categories - categories_used
        
        if unused_categories:
            recommendations['category_recommendations'].append(
                f"Consider using underused categories: {', '.join(list(unused_categories)[:3])}"
            )
        
        # Topic diversity recommendations
        if len(recent_content) > 5:
            topics = [content.topic for content in recent_content]
            diversity_engine = TopicDiversityEngine()
            
            # Check for repetitive topics
            repetitive_topics = []
            for i, topic in enumerate(topics):
                for j, other_topic in enumerate(topics[i+1:], i+1):
                    similarity = diversity_engine.calculate_topic_similarity(topic, other_topic)
                    if similarity > 0.4:
                        repetitive_topics.append((topic, other_topic, similarity))
            
            if repetitive_topics:
                recommendations['topic_diversity_suggestions'].append(
                    f"Found {len(repetitive_topics)} similar topic pairs - consider more diverse topics"
                )
        
        return recommendations

    def _display_analysis_results(self, report: Dict):
        """Display analysis results."""
        self.stdout.write("\n📊 ANALYSIS RESULTS")
        self.stdout.write("-" * 50)
        
        # Video metadata analysis
        video_analysis = report['video_metadata_analysis']
        self.stdout.write(f"\n📹 Video Metadata Analysis:")
        self.stdout.write(f"   Total metadata files: {video_analysis['total_metadata_files']}")
        
        if video_analysis['prompt_patterns']['total_prompts'] > 0:
            patterns = video_analysis['prompt_patterns']
            self.stdout.write(f"   Total prompts analyzed: {patterns['total_prompts']}")
            self.stdout.write(f"   Diversity score: {patterns['diversity_score']:.2f}")
            
            if patterns['repetitive_keywords']:
                self.stdout.write(f"   ⚠️ Repetitive keywords: {', '.join(patterns['repetitive_keywords'][:5])}")
        
        # Database content analysis
        db_analysis = report['database_content_analysis']
        self.stdout.write(f"\n💾 Database Content Analysis:")
        self.stdout.write(f"   Total content: {db_analysis['total_content']}")
        self.stdout.write(f"   Categories used: {len(db_analysis['categories_used'])}")
        
        if db_analysis['categories_used']:
            self.stdout.write(f"   Category distribution:")
            for category, count in sorted(db_analysis['categories_used'].items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"     • {category}: {count}")
        
        # Diversity insights
        diversity_insights = report['diversity_insights']
        self.stdout.write(f"\n🌈 Diversity Insights:")
        diversity_score = diversity_insights['diversity_score']
        self.stdout.write(f"   Overall diversity score: {diversity_score['score']:.2f}")
        self.stdout.write(f"   Category diversity: {diversity_score['category_diversity']:.2f}")
        self.stdout.write(f"   Topic diversity: {diversity_score['topic_diversity']:.2f}")
        
        # Recommendations
        recommendations = report['recommendations']
        self.stdout.write(f"\n💡 Recommendations:")
        
        if recommendations['category_recommendations']:
            for rec in recommendations['category_recommendations']:
                self.stdout.write(f"   • {rec}")
        
        if recommendations['topic_diversity_suggestions']:
            for rec in recommendations['topic_diversity_suggestions']:
                self.stdout.write(f"   • {rec}")
        
        # Next content strategy
        strategy = recommendations['next_content_strategy']
        self.stdout.write(f"\n🚀 Next Content Strategy:")
        self.stdout.write(f"   Recommended category: {strategy['recommended_category']}")
        self.stdout.write(f"   Strategy: {strategy['strategy']}")

    def _export_analysis_results(self, report: Dict):
        """Export analysis results to JSON file."""
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"content_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.stdout.write(f"\n📁 Analysis results exported to: {filename}")
