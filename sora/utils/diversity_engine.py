"""
Topic Diversity Engine
Ensures content variety and prevents repetition across health categories
"""

import random
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q

from sora.models import GeneratedContent


class TopicDiversityEngine:
    """Engine to ensure content diversity and prevent topic repetition."""
    
    # Available health categories with weights (higher = more priority)
    HEALTH_CATEGORIES = {
        'Nutrition': {'weight': 8, 'description': 'Healthy eating, vitamins, meal planning'},
        'Fitness': {'weight': 7, 'description': 'Exercise routines, workout tips, physical activity'},
        'Mental Health': {'weight': 6, 'description': 'Stress management, mindfulness, mental wellness'},
        'Sleep': {'weight': 6, 'description': 'Sleep hygiene, rest optimization, bedtime routines'},
        'Hydration': {'weight': 5, 'description': 'Water intake, hydration benefits, fluid balance'},
        'Skincare': {'weight': 4, 'description': 'Natural skincare, skin health, beauty routines'},
        'Wellness': {'weight': 5, 'description': 'General wellness, lifestyle tips, self-care'},
        'Digestive Health': {'weight': 4, 'description': 'Gut health, digestion, digestive wellness'},
        'Immune System': {'weight': 5, 'description': 'Immune support, cold prevention, health defense'},
        'Weight Management': {'weight': 4, 'description': 'Healthy weight, metabolism, body composition'}
    }
    
    def __init__(self):
        """Initialize the diversity engine."""
        self.recent_days = 30  # Look back 30 days for diversity analysis
    
    def get_category_weights(self) -> Dict[str, float]:
        """
        Calculate dynamic category weights based on recent usage.
        Categories used less recently get higher weights.
        
        Returns:
            Dict mapping category names to their current weights
        """
        recent_content = GeneratedContent.get_recent_content(self.recent_days)
        category_counts = {}
        
        # Count recent usage for each category
        for content in recent_content:
            category = content.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate dynamic weights
        dynamic_weights = {}
        for category, base_weight in self.HEALTH_CATEGORIES.items():
            recent_usage = category_counts.get(category, 0)
            
            # Higher weight for less used categories
            # Add bonus weight inversely proportional to recent usage
            bonus_weight = max(0, 10 - recent_usage)  # Up to 10 bonus points
            dynamic_weights[category] = base_weight['weight'] + bonus_weight
        
        return dynamic_weights
    
    def select_diverse_category(self, exclude_categories: List[str] = None) -> str:
        """
        Select a category using weighted random selection favoring diversity.
        
        Args:
            exclude_categories: Categories to exclude from selection
            
        Returns:
            Selected category name
        """
        if exclude_categories is None:
            exclude_categories = []
        
        # Get dynamic weights
        weights = self.get_category_weights()
        
        # Remove excluded categories
        available_categories = {
            cat: weight for cat, weight in weights.items() 
            if cat not in exclude_categories
        }
        
        if not available_categories:
            # Fallback to all categories if all are excluded
            available_categories = weights
        
        # Weighted random selection
        categories = list(available_categories.keys())
        weights_list = list(available_categories.values())
        
        selected_category = random.choices(categories, weights=weights_list, k=1)[0]
        
        return selected_category
    
    def extract_topic_keywords(self, topic: str) -> List[str]:
        """
        Extract keywords from a topic for similarity detection.
        
        Args:
            topic: Topic string to analyze
            
        Returns:
            List of extracted keywords
        """
        # Convert to lowercase and split into words
        words = re.findall(r'\b\w+\b', topic.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def calculate_topic_similarity(self, topic1: str, topic2: str) -> float:
        """
        Calculate similarity between two topics (0.0 = no similarity, 1.0 = identical).
        
        Args:
            topic1: First topic
            topic2: Second topic
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        keywords1 = set(self.extract_topic_keywords(topic1))
        keywords2 = set(self.extract_topic_keywords(topic2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def find_similar_topics(self, topic: str, threshold: float = 0.3) -> List[GeneratedContent]:
        """
        Find previously generated topics similar to the given topic.
        
        Args:
            topic: Topic to check for similarity
            threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            List of similar GeneratedContent objects
        """
        recent_content = GeneratedContent.get_recent_content(self.recent_days)
        similar_content = []
        
        for content in recent_content:
            similarity = self.calculate_topic_similarity(topic, content.topic)
            if similarity >= threshold:
                similar_content.append(content)
        
        return similar_content
    
    def is_topic_too_similar(self, topic: str, max_similarity: float = 0.4) -> bool:
        """
        Check if a topic is too similar to recently generated content.
        
        Args:
            topic: Topic to check
            max_similarity: Maximum allowed similarity (0.0-1.0)
            
        Returns:
            True if topic is too similar, False otherwise
        """
        similar_topics = self.find_similar_topics(topic, max_similarity)
        return len(similar_topics) > 0
    
    def get_diversity_score(self, days: int = 30) -> Dict[str, float]:
        """
        Calculate diversity score for recent content generation.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with diversity metrics
        """
        recent_content = GeneratedContent.get_recent_content(days)
        
        if not recent_content:
            return {'score': 1.0, 'category_diversity': 1.0, 'topic_diversity': 1.0}
        
        # Category diversity (how many different categories used)
        categories_used = set(content.category for content in recent_content)
        total_categories = len(self.HEALTH_CATEGORIES)
        category_diversity = len(categories_used) / total_categories
        
        # Topic diversity (average similarity between topics)
        topics = [content.topic for content in recent_content]
        if len(topics) < 2:
            topic_diversity = 1.0
        else:
            similarities = []
            for i in range(len(topics)):
                for j in range(i + 1, len(topics)):
                    similarity = self.calculate_topic_similarity(topics[i], topics[j])
                    similarities.append(similarity)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0
            topic_diversity = 1.0 - avg_similarity  # Higher diversity = lower similarity
        
        # Overall diversity score
        overall_score = (category_diversity + topic_diversity) / 2
        
        return {
            'score': overall_score,
            'category_diversity': category_diversity,
            'topic_diversity': topic_diversity,
            'categories_used': len(categories_used),
            'total_categories': total_categories
        }
    
    def suggest_next_category(self, exclude_recent: bool = True) -> str:
        """
        Suggest the next category to use for content generation.
        
        Args:
            exclude_recent: Whether to exclude recently used categories
            
        Returns:
            Suggested category name
        """
        if exclude_recent:
            # Get categories used in the last 7 days
            recent_categories = set()
            recent_content = GeneratedContent.get_recent_content(7)
            for content in recent_content:
                recent_categories.add(content.category)
            
            # Exclude recently used categories
            return self.select_diverse_category(exclude_categories=list(recent_categories))
        else:
            return self.select_diverse_category()
    
    def get_diversity_report(self, days: int = 30) -> Dict:
        """
        Generate a comprehensive diversity report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with detailed diversity analysis
        """
        recent_content = GeneratedContent.get_recent_content(days)
        
        # Category usage
        category_usage = {}
        for content in recent_content:
            category = content.category
            category_usage[category] = category_usage.get(category, 0) + 1
        
        # Topic keywords analysis
        all_keywords = []
        for content in recent_content:
            keywords = self.extract_topic_keywords(content.topic)
            all_keywords.extend(keywords)
        
        # Most common keywords
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        most_common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Diversity metrics
        diversity_metrics = self.get_diversity_score(days)
        
        return {
            'period_days': days,
            'total_content': len(recent_content),
            'category_usage': category_usage,
            'diversity_metrics': diversity_metrics,
            'most_common_keywords': most_common_keywords,
            'suggested_next_category': self.suggest_next_category(),
            'least_used_categories': GeneratedContent.get_least_used_categories(days, 5)
        }


def test_diversity_engine():
    """Test the diversity engine functionality."""
    engine = TopicDiversityEngine()
    
    print("🧪 Testing Topic Diversity Engine")
    print("=" * 50)
    
    # Test category selection
    print("\n📊 Category Weights:")
    weights = engine.get_category_weights()
    for category, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {weight:.1f}")
    
    # Test diverse category selection
    print(f"\n🎯 Suggested Next Category: {engine.suggest_next_category()}")
    
    # Test diversity score
    diversity = engine.get_diversity_score()
    print(f"\n📈 Diversity Score: {diversity['score']:.2f}")
    print(f"   Category Diversity: {diversity['category_diversity']:.2f}")
    print(f"   Topic Diversity: {diversity['topic_diversity']:.2f}")
    
    # Test topic similarity
    test_topic = "honey and lemon face mask"
    similar = engine.find_similar_topics(test_topic)
    print(f"\n🔍 Similar topics to '{test_topic}': {len(similar)} found")
    
    is_similar = engine.is_topic_too_similar(test_topic)
    print(f"   Is too similar: {is_similar}")
    
    print("\n✅ Diversity engine test completed!")


if __name__ == "__main__":
    test_diversity_engine()
