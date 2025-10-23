"""
Enhanced Duplicate Detection System
Prevents similar topic repetition and ensures content diversity
"""

import re
from typing import List, Dict, Optional, Tuple
from django.utils import timezone
from datetime import timedelta

from sora.models import GeneratedContent
from sora.utils.diversity_engine import TopicDiversityEngine


class EnhancedDuplicateDetector:
    """Advanced duplicate detection system for content diversity."""
    
    def __init__(self):
        """Initialize the duplicate detector."""
        self.diversity_engine = TopicDiversityEngine()
        self.similarity_threshold = 0.4  # Maximum allowed similarity
        self.recent_days = 30  # Days to look back for similarity check
    
    def check_content_similarity(self, 
                                title: str, 
                                topic: str, 
                                category: str = None) -> Dict[str, any]:
        """
        Check if content is too similar to recently generated content.
        
        Args:
            title: Content title
            topic: Main topic
            category: Content category
            
        Returns:
            Dict with similarity analysis results
        """
        recent_content = GeneratedContent.get_recent_content(self.recent_days)
        
        # Check title similarity
        title_similarities = []
        for content in recent_content:
            similarity = self.diversity_engine.calculate_topic_similarity(title, content.title)
            if similarity > 0.3:  # Lower threshold for titles
                title_similarities.append({
                    'content': content,
                    'similarity': similarity,
                    'type': 'title'
                })
        
        # Check topic similarity
        topic_similarities = []
        for content in recent_content:
            similarity = self.diversity_engine.calculate_topic_similarity(topic, content.topic)
            if similarity > self.similarity_threshold:
                topic_similarities.append({
                    'content': content,
                    'similarity': similarity,
                    'type': 'topic'
                })
        
        # Check category repetition
        category_repetition = self._check_category_repetition(category, recent_content)
        
        # Check keyword repetition
        keyword_repetition = self._check_keyword_repetition(topic, recent_content)
        
        # Calculate overall similarity score
        max_title_similarity = max([s['similarity'] for s in title_similarities], default=0)
        max_topic_similarity = max([s['similarity'] for s in topic_similarities], default=0)
        overall_similarity = max(max_title_similarity, max_topic_similarity)
        
        # Determine if content is too similar
        is_too_similar = (
            overall_similarity > self.similarity_threshold or
            category_repetition['is_repetitive'] or
            keyword_repetition['is_repetitive']
        )
        
        return {
            'is_similar': is_too_similar,
            'overall_similarity': overall_similarity,
            'title_similarities': title_similarities,
            'topic_similarities': topic_similarities,
            'category_repetition': category_repetition,
            'keyword_repetition': keyword_repetition,
            'recommendations': self._generate_similarity_recommendations(
                title_similarities, topic_similarities, category_repetition, keyword_repetition
            )
        }
    
    def _check_category_repetition(self, category: str, recent_content: List[GeneratedContent]) -> Dict:
        """Check if category has been used too recently."""
        if not category:
            return {'is_repetitive': False, 'recent_usage': 0, 'message': 'No category specified'}
        
        # Count recent usage of this category
        recent_usage = sum(1 for content in recent_content if content.category == category)
        
        # Check if category was used in the last 3 days
        three_days_ago = timezone.now() - timedelta(days=3)
        very_recent_usage = sum(
            1 for content in recent_content 
            if content.category == category and content.generated_at >= three_days_ago
        )
        
        is_repetitive = very_recent_usage > 0 or recent_usage > 2
        
        return {
            'is_repetitive': is_repetitive,
            'recent_usage': recent_usage,
            'very_recent_usage': very_recent_usage,
            'message': f'Category "{category}" used {recent_usage} times recently' if recent_usage > 0 else f'Category "{category}" not used recently'
        }
    
    def _check_keyword_repetition(self, topic: str, recent_content: List[GeneratedContent]) -> Dict:
        """Check for keyword repetition in recent content."""
        topic_keywords = set(self.diversity_engine.extract_topic_keywords(topic))
        
        if not topic_keywords:
            return {'is_repetitive': False, 'repeated_keywords': [], 'message': 'No keywords to check'}
        
        # Count keyword usage in recent content
        keyword_usage = {}
        for content in recent_content:
            content_keywords = set(content.topic_keywords) if content.topic_keywords else set()
            for keyword in topic_keywords:
                if keyword in content_keywords:
                    keyword_usage[keyword] = keyword_usage.get(keyword, 0) + 1
        
        # Find overused keywords
        overused_keywords = [
            keyword for keyword, count in keyword_usage.items() 
            if count > 2  # Threshold for overuse
        ]
        
        is_repetitive = len(overused_keywords) > 0
        
        return {
            'is_repetitive': is_repetitive,
            'repeated_keywords': overused_keywords,
            'keyword_usage': keyword_usage,
            'message': f'Overused keywords: {", ".join(overused_keywords)}' if overused_keywords else 'No keyword repetition detected'
        }
    
    def _generate_similarity_recommendations(self, 
                                           title_similarities: List, 
                                           topic_similarities: List,
                                           category_repetition: Dict,
                                           keyword_repetition: Dict) -> List[str]:
        """Generate recommendations based on similarity analysis."""
        recommendations = []
        
        if title_similarities:
            max_similarity = max(s['similarity'] for s in title_similarities)
            recommendations.append(f"Title is {max_similarity:.1%} similar to recent content - consider a more unique title")
        
        if topic_similarities:
            max_similarity = max(s['similarity'] for s in topic_similarities)
            recommendations.append(f"Topic is {max_similarity:.1%} similar to recent content - consider a different angle")
        
        if category_repetition['is_repetitive']:
            recommendations.append(f"Category '{category_repetition['message']}' - consider using a different category")
        
        if keyword_repetition['is_repetitive']:
            recommendations.append(f"Keywords '{keyword_repetition['message']}' - avoid overused terms")
        
        if not recommendations:
            recommendations.append("Content appears unique and diverse")
        
        return recommendations
    
    def suggest_content_alternatives(self, 
                                   original_topic: str, 
                                   category: str = None,
                                   count: int = 3) -> List[Dict[str, str]]:
        """
        Suggest alternative content topics to avoid similarity.
        
        Args:
            original_topic: Original topic to find alternatives for
            category: Preferred category
            count: Number of alternatives to suggest
            
        Returns:
            List of alternative topic suggestions
        """
        from sora.utils.topic_bank import TopicBank
        
        topic_bank = TopicBank()
        alternatives = []
        
        # Get topics from the same category
        if category:
            category_topics = topic_bank.get_topics_by_category(category)
        else:
            # Get topics from all categories
            category_topics = []
            for cat in topic_bank.categories:
                category_topics.extend(topic_bank.get_topics_by_category(cat))
        
        # Filter out similar topics
        for topic in category_topics:
            similarity = self.diversity_engine.calculate_topic_similarity(original_topic, topic)
            if similarity < self.similarity_threshold:
                alternatives.append({
                    'topic': topic,
                    'category': category or 'Various',
                    'similarity_to_original': similarity,
                    'diversity_score': 1.0 - similarity
                })
        
        # Sort by diversity score and return top alternatives
        alternatives.sort(key=lambda x: x['diversity_score'], reverse=True)
        return alternatives[:count]
    
    def get_diversity_score_for_topic(self, topic: str, category: str = None) -> Dict:
        """
        Calculate diversity score for a specific topic.
        
        Args:
            topic: Topic to analyze
            category: Topic category
            
        Returns:
            Dict with diversity analysis
        """
        recent_content = GeneratedContent.get_recent_content(self.recent_days)
        
        # Calculate similarity to recent content
        similarities = []
        for content in recent_content:
            similarity = self.diversity_engine.calculate_topic_similarity(topic, content.topic)
            similarities.append(similarity)
        
        # Calculate diversity metrics
        max_similarity = max(similarities) if similarities else 0
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        diversity_score = 1.0 - max_similarity  # Higher score = more diverse
        
        # Check category diversity
        category_diversity = 1.0
        if category:
            category_usage = sum(1 for content in recent_content if content.category == category)
            category_diversity = 1.0 / (1.0 + category_usage)  # Lower usage = higher diversity
        
        # Overall diversity score
        overall_diversity = (diversity_score + category_diversity) / 2
        
        return {
            'topic': topic,
            'category': category,
            'diversity_score': overall_diversity,
            'max_similarity': max_similarity,
            'avg_similarity': avg_similarity,
            'category_diversity': category_diversity,
            'is_diverse': overall_diversity > 0.6,
            'recommendations': self._get_diversity_recommendations(overall_diversity, max_similarity)
        }
    
    def _get_diversity_recommendations(self, diversity_score: float, max_similarity: float) -> List[str]:
        """Get recommendations based on diversity score."""
        recommendations = []
        
        if diversity_score < 0.4:
            recommendations.append("Content is not diverse enough - consider a completely different topic")
        elif diversity_score < 0.6:
            recommendations.append("Content has moderate diversity - consider slight topic variations")
        else:
            recommendations.append("Content is highly diverse - good choice for content generation")
        
        if max_similarity > 0.5:
            recommendations.append("Content is too similar to recent topics - try a different angle")
        elif max_similarity > 0.3:
            recommendations.append("Content has some similarity to recent topics - consider minor adjustments")
        
        return recommendations
    
    def validate_content_diversity(self, 
                                 title: str, 
                                 topic: str, 
                                 category: str = None) -> Dict:
        """
        Comprehensive content diversity validation.
        
        Args:
            title: Content title
            topic: Main topic
            category: Content category
            
        Returns:
            Dict with comprehensive validation results
        """
        # Check similarity
        similarity_analysis = self.check_content_similarity(title, topic, category)
        
        # Get diversity score
        diversity_analysis = self.get_diversity_score_for_topic(topic, category)
        
        # Get alternatives if needed
        alternatives = []
        if similarity_analysis['is_similar'] or diversity_analysis['diversity_score'] < 0.6:
            alternatives = self.suggest_content_alternatives(topic, category, 3)
        
        # Overall validation
        is_valid = (
            not similarity_analysis['is_similar'] and 
            diversity_analysis['is_diverse']
        )
        
        return {
            'is_valid': is_valid,
            'similarity_analysis': similarity_analysis,
            'diversity_analysis': diversity_analysis,
            'alternatives': alternatives,
            'overall_score': (1.0 - similarity_analysis['overall_similarity'] + diversity_analysis['diversity_score']) / 2,
            'recommendations': similarity_analysis['recommendations'] + diversity_analysis['recommendations']
        }


def test_enhanced_duplicate_detection():
    """Test the enhanced duplicate detection system."""
    detector = EnhancedDuplicateDetector()
    
    print("🧪 Testing Enhanced Duplicate Detection")
    print("=" * 50)
    
    # Test content similarity check
    print("\n🔍 Testing Content Similarity Check:")
    test_title = "Honey and Lemon Face Mask for Glowing Skin"
    test_topic = "natural skincare with honey and lemon"
    test_category = "Skincare"
    
    similarity_result = detector.check_content_similarity(test_title, test_topic, test_category)
    print(f"   Title: {test_title}")
    print(f"   Topic: {test_topic}")
    print(f"   Category: {test_category}")
    print(f"   Is similar: {similarity_result['is_similar']}")
    print(f"   Overall similarity: {similarity_result['overall_similarity']:.2f}")
    
    if similarity_result['recommendations']:
        print("   Recommendations:")
        for rec in similarity_result['recommendations']:
            print(f"     • {rec}")
    
    # Test diversity score
    print(f"\n📊 Testing Diversity Score:")
    diversity_result = detector.get_diversity_score_for_topic(test_topic, test_category)
    print(f"   Diversity score: {diversity_result['diversity_score']:.2f}")
    print(f"   Is diverse: {diversity_result['is_diverse']}")
    
    if diversity_result['recommendations']:
        print("   Recommendations:")
        for rec in diversity_result['recommendations']:
            print(f"     • {rec}")
    
    # Test content validation
    print(f"\n✅ Testing Content Validation:")
    validation_result = detector.validate_content_diversity(test_title, test_topic, test_category)
    print(f"   Is valid: {validation_result['is_valid']}")
    print(f"   Overall score: {validation_result['overall_score']:.2f}")
    
    if validation_result['alternatives']:
        print("   Alternative topics:")
        for alt in validation_result['alternatives'][:3]:
            print(f"     • {alt['topic']} (diversity: {alt['diversity_score']:.2f})")
    
    print("\n✅ Enhanced duplicate detection test completed!")


if __name__ == "__main__":
    test_enhanced_duplicate_detection()
