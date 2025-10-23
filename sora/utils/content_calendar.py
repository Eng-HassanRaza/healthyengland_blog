"""
Content Calendar System
Systematic topic rotation and content planning for diverse health content
"""

import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone

from sora.models import GeneratedContent
from sora.utils.diversity_engine import TopicDiversityEngine
from sora.utils.topic_bank import TopicBank
from sora.utils.smart_selector import SmartTopicSelector


class ContentCalendar:
    """Systematic content planning and topic rotation system."""
    
    def __init__(self):
        """Initialize the content calendar."""
        self.diversity_engine = TopicDiversityEngine()
        self.topic_bank = TopicBank()
        self.smart_selector = SmartTopicSelector()
        
        # Content calendar settings
        self.planning_days = 30  # Days to plan ahead
        self.categories = list(self.diversity_engine.HEALTH_CATEGORIES.keys())
        self.difficulty_levels = ['beginner', 'intermediate', 'advanced']
    
    def generate_content_calendar(self, 
                                days: int = 30, 
                                content_per_day: int = 1) -> Dict:
        """
        Generate a content calendar with diverse topics.
        
        Args:
            days: Number of days to plan
            content_per_day: Number of content pieces per day
            
        Returns:
            Dict with content calendar
        """
        calendar = {
            'planning_period': days,
            'content_per_day': content_per_day,
            'total_content_pieces': days * content_per_day,
            'daily_schedule': [],
            'category_rotation': {},
            'diversity_metrics': {}
        }
        
        # Generate daily schedule
        for day in range(days):
            date = timezone.now() + timedelta(days=day)
            daily_content = self._generate_daily_content(date, content_per_day)
            calendar['daily_schedule'].append(daily_content)
        
        # Analyze category rotation
        calendar['category_rotation'] = self._analyze_category_rotation(calendar['daily_schedule'])
        
        # Calculate diversity metrics
        calendar['diversity_metrics'] = self._calculate_calendar_diversity(calendar['daily_schedule'])
        
        return calendar
    
    def _generate_daily_content(self, date: datetime, count: int) -> Dict:
        """Generate content for a specific day."""
        daily_content = {
            'date': date.strftime('%Y-%m-%d'),
            'day_of_week': date.strftime('%A'),
            'content_pieces': []
        }
        
        for i in range(count):
            # Use smart selection for diversity
            content_piece = self._generate_content_piece(date, i)
            daily_content['content_pieces'].append(content_piece)
        
        return daily_content
    
    def _generate_content_piece(self, date: datetime, index: int) -> Dict:
        """Generate a single content piece with diversity optimization."""
        # Get optimal topic selection
        selection_result = self.smart_selector.select_optimal_topic()
        
        # Get topic from topic bank
        topic = self.topic_bank.get_random_topic(
            category=selection_result['category'],
            difficulty=selection_result['difficulty']
        )
        
        return {
            'index': index + 1,
            'topic': topic,
            'category': selection_result['category'],
            'difficulty': selection_result['difficulty'],
            'confidence': selection_result['confidence'],
            'diversity_score': self._calculate_piece_diversity(topic, selection_result['category'])
        }
    
    def _calculate_piece_diversity(self, topic: str, category: str) -> float:
        """Calculate diversity score for a content piece."""
        # Get recent content for comparison
        recent_content = GeneratedContent.get_recent_content(30)
        
        # Calculate similarity to recent content
        similarities = []
        for content in recent_content:
            similarity = self.diversity_engine.calculate_topic_similarity(topic, content.topic)
            similarities.append(similarity)
        
        # Calculate diversity score
        max_similarity = max(similarities) if similarities else 0
        diversity_score = 1.0 - max_similarity
        
        return diversity_score
    
    def _analyze_category_rotation(self, daily_schedule: List[Dict]) -> Dict:
        """Analyze category rotation in the calendar."""
        category_usage = {}
        category_sequence = []
        
        for day in daily_schedule:
            for piece in day['content_pieces']:
                category = piece['category']
                category_usage[category] = category_usage.get(category, 0) + 1
                category_sequence.append(category)
        
        # Calculate rotation metrics
        rotation_analysis = {
            'category_distribution': category_usage,
            'category_sequence': category_sequence,
            'rotation_efficiency': self._calculate_rotation_efficiency(category_sequence),
            'category_balance': self._calculate_category_balance(category_usage)
        }
        
        return rotation_analysis
    
    def _calculate_rotation_efficiency(self, category_sequence: List[str]) -> float:
        """Calculate how efficiently categories are rotated."""
        if len(category_sequence) < 2:
            return 1.0
        
        # Count consecutive same categories
        consecutive_count = 0
        for i in range(1, len(category_sequence)):
            if category_sequence[i] == category_sequence[i-1]:
                consecutive_count += 1
        
        # Efficiency = 1 - (consecutive_count / total_possible_consecutive)
        max_consecutive = len(category_sequence) - 1
        efficiency = 1.0 - (consecutive_count / max_consecutive) if max_consecutive > 0 else 1.0
        
        return efficiency
    
    def _calculate_category_balance(self, category_usage: Dict) -> float:
        """Calculate how balanced category usage is."""
        if not category_usage:
            return 1.0
        
        usage_counts = list(category_usage.values())
        max_usage = max(usage_counts)
        min_usage = min(usage_counts)
        
        # Balance = 1 - (max_usage - min_usage) / max_usage
        balance = 1.0 - (max_usage - min_usage) / max_usage if max_usage > 0 else 1.0
        
        return balance
    
    def _calculate_calendar_diversity(self, daily_schedule: List[Dict]) -> Dict:
        """Calculate overall diversity metrics for the calendar."""
        all_topics = []
        all_categories = []
        
        for day in daily_schedule:
            for piece in day['content_pieces']:
                all_topics.append(piece['topic'])
                all_categories.append(piece['category'])
        
        # Calculate topic diversity
        topic_diversity = self._calculate_topic_diversity(all_topics)
        
        # Calculate category diversity
        category_diversity = len(set(all_categories)) / len(self.categories)
        
        # Calculate overall diversity
        overall_diversity = (topic_diversity + category_diversity) / 2
        
        return {
            'topic_diversity': topic_diversity,
            'category_diversity': category_diversity,
            'overall_diversity': overall_diversity,
            'total_topics': len(all_topics),
            'unique_categories': len(set(all_categories))
        }
    
    def _calculate_topic_diversity(self, topics: List[str]) -> float:
        """Calculate diversity score for a list of topics."""
        if len(topics) < 2:
            return 1.0
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(topics)):
            for j in range(i + 1, len(topics)):
                similarity = self.diversity_engine.calculate_topic_similarity(topics[i], topics[j])
                similarities.append(similarity)
        
        if not similarities:
            return 1.0
        
        # Diversity = 1 - average similarity
        avg_similarity = sum(similarities) / len(similarities)
        diversity = 1.0 - avg_similarity
        
        return diversity
    
    def get_next_content_schedule(self, days: int = 7) -> List[Dict]:
        """
        Get the next content schedule for the specified number of days.
        
        Args:
            days: Number of days to schedule
            
        Returns:
            List of content schedules
        """
        schedule = []
        
        for day in range(days):
            date = timezone.now() + timedelta(days=day)
            
            # Get optimal content for this day
            content_piece = self._generate_content_piece(date, 0)
            
            schedule.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_of_week': date.strftime('%A'),
                'recommended_topic': content_piece['topic'],
                'recommended_category': content_piece['category'],
                'recommended_difficulty': content_piece['difficulty'],
                'diversity_score': content_piece['diversity_score'],
                'confidence': content_piece['confidence']
            })
        
        return schedule
    
    def optimize_calendar_diversity(self, calendar: Dict) -> Dict:
        """
        Optimize calendar for maximum diversity.
        
        Args:
            calendar: Content calendar to optimize
            
        Returns:
            Optimized calendar
        """
        optimized_calendar = calendar.copy()
        
        # Reorder content pieces to maximize diversity
        for day in optimized_calendar['daily_schedule']:
            day['content_pieces'] = self._optimize_daily_diversity(day['content_pieces'])
        
        # Recalculate metrics
        optimized_calendar['category_rotation'] = self._analyze_category_rotation(
            optimized_calendar['daily_schedule']
        )
        optimized_calendar['diversity_metrics'] = self._calculate_calendar_diversity(
            optimized_calendar['daily_schedule']
        )
        
        return optimized_calendar
    
    def _optimize_daily_diversity(self, content_pieces: List[Dict]) -> List[Dict]:
        """Optimize daily content for maximum diversity."""
        if len(content_pieces) <= 1:
            return content_pieces
        
        # Sort by diversity score
        optimized_pieces = sorted(content_pieces, key=lambda x: x['diversity_score'], reverse=True)
        
        return optimized_pieces
    
    def get_content_recommendations(self, 
                                  current_date: datetime = None,
                                  look_ahead_days: int = 7) -> Dict:
        """
        Get content recommendations for the specified period.
        
        Args:
            current_date: Starting date (defaults to now)
            look_ahead_days: Number of days to look ahead
            
        Returns:
            Dict with content recommendations
        """
        if current_date is None:
            current_date = timezone.now()
        
        # Get next content schedule
        schedule = self.get_next_content_schedule(look_ahead_days)
        
        # Get diversity analysis
        diversity_analysis = self.diversity_engine.get_diversity_report(30)
        
        # Get smart selector strategy
        strategy = self.smart_selector.get_next_content_strategy()
        
        return {
            'current_date': current_date.strftime('%Y-%m-%d'),
            'look_ahead_days': look_ahead_days,
            'content_schedule': schedule,
            'diversity_analysis': diversity_analysis,
            'strategy': strategy,
            'recommendations': self._generate_calendar_recommendations(schedule, diversity_analysis)
        }
    
    def _generate_calendar_recommendations(self, 
                                         schedule: List[Dict], 
                                         diversity_analysis: Dict) -> List[str]:
        """Generate recommendations based on calendar and diversity analysis."""
        recommendations = []
        
        # Check category distribution
        categories = [day['recommended_category'] for day in schedule]
        category_counts = {}
        for category in categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Recommend category balance
        if len(set(categories)) < len(self.categories) * 0.5:
            recommendations.append("Consider diversifying across more health categories")
        
        # Check diversity scores
        avg_diversity = sum(day['diversity_score'] for day in schedule) / len(schedule)
        if avg_diversity < 0.6:
            recommendations.append("Content diversity could be improved - consider more varied topics")
        
        # Check difficulty distribution
        difficulties = [day['recommended_difficulty'] for day in schedule]
        difficulty_counts = {}
        for difficulty in difficulties:
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        if difficulty_counts.get('beginner', 0) > len(schedule) * 0.7:
            recommendations.append("Consider adding more intermediate and advanced content")
        
        return recommendations


def test_content_calendar():
    """Test the content calendar system."""
    calendar = ContentCalendar()
    
    print("🧪 Testing Content Calendar System")
    print("=" * 50)
    
    # Test calendar generation
    print("\n📅 Generating Content Calendar:")
    content_calendar = calendar.generate_content_calendar(days=7, content_per_day=1)
    
    print(f"   Planning period: {content_calendar['planning_period']} days")
    print(f"   Content per day: {content_calendar['content_per_day']}")
    print(f"   Total content pieces: {content_calendar['total_content_pieces']}")
    
    # Display daily schedule
    print(f"\n📋 Daily Schedule:")
    for day in content_calendar['daily_schedule']:
        print(f"   {day['date']} ({day['day_of_week']}):")
        for piece in day['content_pieces']:
            print(f"     • {piece['topic']} ({piece['category']}, {piece['difficulty']})")
            print(f"       Diversity: {piece['diversity_score']:.2f}, Confidence: {piece['confidence']:.2f}")
    
    # Display diversity metrics
    print(f"\n📊 Diversity Metrics:")
    metrics = content_calendar['diversity_metrics']
    print(f"   Topic diversity: {metrics['topic_diversity']:.2f}")
    print(f"   Category diversity: {metrics['category_diversity']:.2f}")
    print(f"   Overall diversity: {metrics['overall_diversity']:.2f}")
    
    # Display category rotation
    print(f"\n🔄 Category Rotation:")
    rotation = content_calendar['category_rotation']
    print(f"   Rotation efficiency: {rotation['rotation_efficiency']:.2f}")
    print(f"   Category balance: {rotation['category_balance']:.2f}")
    print(f"   Category distribution:")
    for category, count in rotation['category_distribution'].items():
        print(f"     • {category}: {count}")
    
    # Test content recommendations
    print(f"\n💡 Content Recommendations:")
    recommendations = calendar.get_content_recommendations(look_ahead_days=5)
    
    if recommendations['recommendations']:
        for rec in recommendations['recommendations']:
            print(f"   • {rec}")
    
    print("\n✅ Content calendar test completed!")


if __name__ == "__main__":
    test_content_calendar()
