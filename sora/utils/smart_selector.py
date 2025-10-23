"""
Smart Topic Selection Algorithm
Intelligent topic selection based on diversity rules and content history
"""

import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone

from sora.models import GeneratedContent
from sora.utils.diversity_engine import TopicDiversityEngine
from sora.utils.topic_bank import TopicBank


class SmartTopicSelector:
    """Intelligent topic selection system that ensures diversity and prevents repetition."""
    
    def __init__(self):
        """Initialize the smart selector."""
        self.diversity_engine = TopicDiversityEngine()
        self.topic_bank = TopicBank()
        self.similarity_threshold = 0.4  # Maximum allowed similarity
        self.recent_days = 30  # Days to look back for diversity analysis
    
    def select_optimal_topic(self, 
                           preferred_category: str = None,
                           difficulty: str = None,
                           exclude_recent: bool = True) -> Dict[str, str]:
        """
        Select the optimal topic using smart algorithms.
        
        Args:
            preferred_category: Preferred category (optional)
            difficulty: Preferred difficulty level (optional)
            exclude_recent: Whether to exclude recently used topics
            
        Returns:
            Dict with selected topic and metadata
        """
        # Step 1: Determine optimal category using diversity engine
        if preferred_category:
            category = preferred_category
        else:
            category = self._select_diverse_category(exclude_recent)
        
        # Step 2: Get available topics for the category
        available_topics = self.topic_bank.get_topics_by_category(category, difficulty)
        
        if not available_topics:
            # Fallback to any topic in the category
            available_topics = self.topic_bank.get_topics_by_category(category)
        
        # Step 3: Filter out similar topics if needed
        if exclude_recent:
            filtered_topics = self._filter_similar_topics(available_topics)
        else:
            filtered_topics = available_topics
        
        # Step 4: Select final topic
        if filtered_topics:
            selected_topic = random.choice(filtered_topics)
        else:
            # Fallback to any available topic
            selected_topic = random.choice(available_topics) if available_topics else "General health and wellness tips"
        
        # Step 5: Determine difficulty level
        topic_difficulty = self._determine_difficulty_level(selected_topic, category)
        
        return {
            'topic': selected_topic,
            'category': category,
            'difficulty': topic_difficulty,
            'confidence': self._calculate_selection_confidence(selected_topic, category)
        }
    
    def _select_diverse_category(self, exclude_recent: bool = True) -> str:
        """Select a category using diversity algorithms."""
        if exclude_recent:
            # Get categories used in the last 7 days
            recent_categories = set()
            recent_content = GeneratedContent.get_recent_content(7)
            for content in recent_content:
                recent_categories.add(content.category)
            
            # Use diversity engine to select from non-recent categories
            return self.diversity_engine.select_diverse_category(
                exclude_categories=list(recent_categories)
            )
        else:
            return self.diversity_engine.select_diverse_category()
    
    def _filter_similar_topics(self, topics: List[str]) -> List[str]:
        """Filter out topics that are too similar to recently generated content."""
        recent_content = GeneratedContent.get_recent_content(self.recent_days)
        recent_topics = [content.topic for content in recent_content]
        
        filtered_topics = []
        for topic in topics:
            is_similar = False
            for recent_topic in recent_topics:
                similarity = self.diversity_engine.calculate_topic_similarity(topic, recent_topic)
                if similarity >= self.similarity_threshold:
                    is_similar = True
                    break
            
            if not is_similar:
                filtered_topics.append(topic)
        
        return filtered_topics
    
    def _determine_difficulty_level(self, topic: str, category: str) -> str:
        """Determine the difficulty level of a topic."""
        # Check if topic exists in specific difficulty levels
        for difficulty in ['beginner', 'intermediate', 'advanced']:
            topics_in_level = self.topic_bank.get_topics_by_category(category, difficulty)
            if topic in topics_in_level:
                return difficulty
        
        # Default to beginner if not found
        return 'beginner'
    
    def _calculate_selection_confidence(self, topic: str, category: str) -> float:
        """Calculate confidence score for topic selection."""
        # Base confidence
        confidence = 0.8
        
        # Boost confidence if category is underused
        category_usage = GeneratedContent.get_category_usage(category, self.recent_days)
        if category_usage == 0:
            confidence += 0.2  # Bonus for unused category
        elif category_usage < 3:
            confidence += 0.1  # Small bonus for underused category
        
        # Reduce confidence if topic is similar to recent content
        similar_topics = self.diversity_engine.find_similar_topics(topic, self.similarity_threshold)
        if similar_topics:
            confidence -= 0.3  # Penalty for similarity
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def get_topic_suggestions(self, count: int = 5, 
                            preferred_categories: List[str] = None) -> List[Dict[str, str]]:
        """
        Get multiple topic suggestions with diversity.
        
        Args:
            count: Number of suggestions to generate
            preferred_categories: Preferred categories (optional)
            
        Returns:
            List of topic suggestions with metadata
        """
        suggestions = []
        used_combinations = set()
        
        for _ in range(count * 2):  # Generate extra to ensure diversity
            if len(suggestions) >= count:
                break
            
            # Select category
            if preferred_categories:
                category = random.choice(preferred_categories)
            else:
                category = self._select_diverse_category()
            
            # Get topics for category
            topics = self.topic_bank.get_topics_by_category(category)
            if not topics:
                continue
            
            # Select random topic
            topic = random.choice(topics)
            
            # Check if combination is already used
            combination = (topic, category)
            if combination not in used_combinations:
                used_combinations.add(combination)
                
                # Check similarity to recent content
                if not self.diversity_engine.is_topic_too_similar(topic):
                    difficulty = self._determine_difficulty_level(topic, category)
                    confidence = self._calculate_selection_confidence(topic, category)
                    
                    suggestions.append({
                        'topic': topic,
                        'category': category,
                        'difficulty': difficulty,
                        'confidence': confidence
                    })
        
        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:count]
    
    def analyze_content_patterns(self, days: int = 30) -> Dict:
        """
        Analyze content generation patterns and provide insights.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with analysis results
        """
        recent_content = GeneratedContent.get_recent_content(days)
        
        # Category distribution
        category_counts = {}
        for content in recent_content:
            category = content.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Difficulty distribution
        difficulty_counts = {}
        for content in recent_content:
            difficulty = content.difficulty_level
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        # Topic keyword analysis
        all_keywords = []
        for content in recent_content:
            keywords = self.diversity_engine.extract_topic_keywords(content.topic)
            all_keywords.extend(keywords)
        
        # Most common keywords
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        most_common_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Diversity metrics
        diversity_score = self.diversity_engine.get_diversity_score(days)
        
        # Recommendations
        recommendations = self._generate_recommendations(category_counts, difficulty_counts, most_common_keywords)
        
        return {
            'period_days': days,
            'total_content': len(recent_content),
            'category_distribution': category_counts,
            'difficulty_distribution': difficulty_counts,
            'most_common_keywords': most_common_keywords,
            'diversity_score': diversity_score,
            'recommendations': recommendations,
            'underused_categories': self._get_underused_categories(category_counts),
            'overused_keywords': self._get_overused_keywords(most_common_keywords)
        }
    
    def _generate_recommendations(self, category_counts: Dict, difficulty_counts: Dict, 
                             common_keywords: List[Tuple[str, int]]) -> List[str]:
        """Generate recommendations based on content patterns."""
        recommendations = []
        
        # Category diversity recommendations
        if len(category_counts) < 5:
            recommendations.append("Consider diversifying across more health categories")
        
        # Difficulty balance recommendations
        if difficulty_counts.get('beginner', 0) > difficulty_counts.get('intermediate', 0) * 2:
            recommendations.append("Consider adding more intermediate-level content")
        
        # Keyword diversity recommendations
        if common_keywords and common_keywords[0][1] > 3:
            recommendations.append(f"Reduce repetition of '{common_keywords[0][0]}' keyword")
        
        return recommendations
    
    def _get_underused_categories(self, category_counts: Dict) -> List[str]:
        """Get categories that are underused."""
        all_categories = set(self.topic_bank.categories)
        used_categories = set(category_counts.keys())
        return list(all_categories - used_categories)
    
    def _get_overused_keywords(self, common_keywords: List[Tuple[str, int]]) -> List[str]:
        """Get keywords that are overused."""
        overused = []
        for keyword, count in common_keywords:
            if count > 3:  # Threshold for overuse
                overused.append(keyword)
        return overused
    
    def get_next_content_strategy(self) -> Dict:
        """
        Get strategy for next content generation.
        
        Returns:
            Dict with recommended strategy
        """
        # Analyze current patterns
        analysis = self.analyze_content_patterns(30)
        
        # Get diversity report
        diversity_report = self.diversity_engine.get_diversity_report(30)
        
        # Determine next category
        next_category = self.diversity_engine.suggest_next_category()
        
        # Get topic suggestions
        suggestions = self.get_topic_suggestions(3, [next_category])
        
        return {
            'recommended_category': next_category,
            'topic_suggestions': suggestions,
            'diversity_analysis': analysis,
            'diversity_report': diversity_report,
            'strategy': self._generate_strategy(analysis, diversity_report)
        }
    
    def _generate_strategy(self, analysis: Dict, diversity_report: Dict) -> str:
        """Generate content strategy based on analysis."""
        strategy_parts = []
        
        # Category strategy
        if analysis['underused_categories']:
            strategy_parts.append(f"Focus on underused categories: {', '.join(analysis['underused_categories'][:3])}")
        
        # Diversity strategy
        if diversity_report['diversity_metrics']['score'] < 0.7:
            strategy_parts.append("Increase content diversity across categories and topics")
        
        # Keyword strategy
        if analysis['overused_keywords']:
            strategy_parts.append(f"Avoid overused keywords: {', '.join(analysis['overused_keywords'][:3])}")
        
        if not strategy_parts:
            strategy_parts.append("Continue with current diverse content approach")
        
        return "; ".join(strategy_parts)


def test_smart_selector():
    """Test the smart selector functionality."""
    selector = SmartTopicSelector()
    
    print("🧪 Testing Smart Topic Selector")
    print("=" * 50)
    
    # Test optimal topic selection
    print("\n🎯 Optimal Topic Selection:")
    for i in range(3):
        result = selector.select_optimal_topic()
        print(f"  {i+1}. {result['topic']}")
        print(f"     Category: {result['category']}, Difficulty: {result['difficulty']}")
        print(f"     Confidence: {result['confidence']:.2f}")
    
    # Test topic suggestions
    print(f"\n💡 Topic Suggestions:")
    suggestions = selector.get_topic_suggestions(5)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion['topic']} ({suggestion['category']}, {suggestion['difficulty']})")
        print(f"     Confidence: {suggestion['confidence']:.2f}")
    
    # Test content analysis
    print(f"\n📊 Content Pattern Analysis:")
    analysis = selector.analyze_content_patterns(30)
    print(f"  Total content: {analysis['total_content']}")
    print(f"  Categories used: {len(analysis['category_distribution'])}")
    print(f"  Diversity score: {analysis['diversity_score']['score']:.2f}")
    
    if analysis['recommendations']:
        print(f"  Recommendations:")
        for rec in analysis['recommendations']:
            print(f"    • {rec}")
    
    # Test next content strategy
    print(f"\n🚀 Next Content Strategy:")
    strategy = selector.get_next_content_strategy()
    print(f"  Recommended category: {strategy['recommended_category']}")
    print(f"  Strategy: {strategy['strategy']}")
    
    print("\n✅ Smart selector test completed!")


if __name__ == "__main__":
    test_smart_selector()
