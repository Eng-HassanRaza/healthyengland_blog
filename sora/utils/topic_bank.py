"""
Topic Bank System
Comprehensive database of health topics with categories and difficulty levels
"""

import random
from typing import List, Dict, Optional
from django.db import models


class TopicBank:
    """Comprehensive database of health topics for content generation."""
    
    # Topic database organized by category
    TOPIC_DATABASE = {
        'Nutrition': {
            'beginner': [
                'Drink 8 glasses of water daily for glowing skin',
                'Eat 5 servings of fruits and vegetables every day',
                'Start your morning with a glass of warm lemon water',
                'Include protein in every meal for sustained energy',
                'Choose whole grains over refined grains for better nutrition',
                'Add colorful vegetables to your plate for antioxidants',
                'Eat slowly and chew your food thoroughly',
                'Include healthy fats like avocado and nuts in your diet',
                'Drink herbal tea instead of sugary beverages',
                'Plan your meals ahead to avoid unhealthy choices'
            ],
            'intermediate': [
                'Intermittent fasting benefits for metabolism and weight management',
                'Meal prep strategies for busy professionals',
                'Understanding macronutrient ratios for optimal health',
                'Fermented foods for gut health and immunity',
                'Anti-inflammatory diet principles and food choices',
                'Seasonal eating for maximum nutritional benefits',
                'Plant-based protein sources and complete amino acids',
                'Hydration timing for optimal performance',
                'Pre and post workout nutrition strategies',
                'Mindful eating techniques for better digestion'
            ],
            'advanced': [
                'Personalized nutrition based on genetic testing',
                'Advanced supplementation strategies for athletes',
                'Metabolic flexibility and fat adaptation',
                'Nutrient timing for competitive performance',
                'Therapeutic diets for specific health conditions',
                'Advanced meal planning for body composition goals',
                'Biohacking nutrition for longevity',
                'Functional medicine approach to nutrition',
                'Advanced hydration protocols for elite performance',
                'Nutritional strategies for stress management'
            ]
        },
        'Fitness': {
            'beginner': [
                'Take a 10-minute walk after every meal',
                'Do 20 squats every morning to start your day',
                'Stretch for 5 minutes before getting out of bed',
                'Use stairs instead of elevators when possible',
                'Park farther away to get extra steps',
                'Do wall push-ups to build upper body strength',
                'Take regular breaks to stand and stretch at work',
                'Dance to your favorite song for 3 minutes',
                'Do calf raises while brushing your teeth',
                'Take a 15-minute walk during your lunch break'
            ],
            'intermediate': [
                'High-intensity interval training (HIIT) for fat loss',
                'Progressive overload principles for strength gains',
                'Compound exercises for full-body workouts',
                'Flexibility and mobility routines for injury prevention',
                'Cardio zone training for endurance improvement',
                'Functional movement patterns for daily activities',
                'Recovery strategies for optimal performance',
                'Bodyweight training progressions',
                'Core stability exercises for better posture',
                'Balance and coordination training'
            ],
            'advanced': [
                'Periodization training for peak performance',
                'Advanced strength training techniques',
                'Sport-specific conditioning protocols',
                'Recovery optimization through technology',
                'Advanced flexibility and mobility training',
                'Competition preparation strategies',
                'Injury rehabilitation through exercise',
                'Performance testing and assessment',
                'Advanced training periodization',
                'Elite athlete recovery protocols'
            ]
        },
        'Mental Health': {
            'beginner': [
                'Take 5 deep breaths when feeling stressed',
                'Write down 3 things you are grateful for each day',
                'Spend 10 minutes in nature to reduce anxiety',
                'Practice saying no to reduce overwhelm',
                'Listen to calming music during stressful times',
                'Take regular breaks from social media',
                'Practice positive self-talk throughout the day',
                'Connect with a friend or family member daily',
                'Engage in a hobby you enjoy for 30 minutes',
                'Practice mindfulness during routine activities'
            ],
            'intermediate': [
                'Meditation techniques for stress reduction',
                'Cognitive behavioral therapy (CBT) strategies',
                'Emotional regulation techniques',
                'Mindfulness-based stress reduction (MBSR)',
                'Breathing exercises for anxiety management',
                'Journaling for emotional processing',
                'Social connection strategies for mental health',
                'Sleep hygiene for mental wellness',
                'Stress management through physical activity',
                'Mindfulness practices for daily life'
            ],
            'advanced': [
                'Advanced meditation and mindfulness practices',
                'Therapeutic approaches for complex trauma',
                'Neuroplasticity training for mental resilience',
                'Advanced stress management techniques',
                'Mental health optimization strategies',
                'Therapeutic relationship building skills',
                'Advanced emotional intelligence development',
                'Mental health crisis intervention',
                'Therapeutic communication techniques',
                'Advanced mindfulness and awareness practices'
            ]
        },
        'Sleep': {
            'beginner': [
                'Go to bed at the same time every night',
                'Keep your bedroom cool and dark for better sleep',
                'Avoid screens 1 hour before bedtime',
                'Create a relaxing bedtime routine',
                'Use your bed only for sleep and intimacy',
                'Avoid caffeine after 2 PM',
                'Get sunlight exposure in the morning',
                'Keep a sleep diary to track patterns',
                'Avoid large meals before bedtime',
                'Create a comfortable sleep environment'
            ],
            'intermediate': [
                'Sleep hygiene optimization strategies',
                'Circadian rhythm regulation techniques',
                'Sleep environment optimization',
                'Relaxation techniques for better sleep',
                'Sleep restriction therapy for insomnia',
                'Light therapy for sleep disorders',
                'Sleep tracking and analysis',
                'Advanced sleep hygiene practices',
                'Sleep debt recovery strategies',
                'Sleep optimization for shift workers'
            ],
            'advanced': [
                'Advanced sleep medicine and disorders',
                'Sleep optimization for athletes',
                'Advanced circadian rhythm management',
                'Sleep research and monitoring techniques',
                'Advanced sleep disorder treatments',
                'Sleep optimization for performance',
                'Advanced sleep tracking and analysis',
                'Sleep medicine and pharmacology',
                'Advanced sleep research methods',
                'Sleep optimization for elite performance'
            ]
        },
        'Hydration': {
            'beginner': [
                'Drink a glass of water when you wake up',
                'Carry a water bottle with you throughout the day',
                'Drink water before you feel thirsty',
                'Add lemon or cucumber to water for flavor',
                'Drink water with every meal',
                'Set hourly reminders to drink water',
                'Choose water over sugary drinks',
                'Drink water before, during, and after exercise',
                'Monitor your urine color for hydration status',
                'Drink herbal tea for additional hydration'
            ],
            'intermediate': [
                'Electrolyte balance for optimal hydration',
                'Hydration strategies for different activities',
                'Water quality and filtration systems',
                'Hydration timing for performance',
                'Electrolyte supplementation strategies',
                'Hydration monitoring and tracking',
                'Advanced hydration protocols',
                'Hydration for different climates',
                'Electrolyte replacement strategies',
                'Hydration optimization techniques'
            ],
            'advanced': [
                'Advanced hydration science and research',
                'Hydration optimization for elite athletes',
                'Advanced electrolyte management',
                'Hydration protocols for extreme conditions',
                'Advanced water quality analysis',
                'Hydration optimization for performance',
                'Advanced hydration monitoring',
                'Hydration science and physiology',
                'Advanced hydration strategies',
                'Hydration optimization for competition'
            ]
        },
        'Skincare': {
            'beginner': [
                'Wash your face twice daily with gentle cleanser',
                'Apply sunscreen every morning',
                'Moisturize your skin after cleansing',
                'Remove makeup before going to bed',
                'Use lukewarm water for face washing',
                'Pat your skin dry instead of rubbing',
                'Exfoliate gently 2-3 times per week',
                'Use products suitable for your skin type',
                'Keep your hands away from your face',
                'Change your pillowcase regularly'
            ],
            'intermediate': [
                'Advanced skincare routine optimization',
                'Understanding skin types and conditions',
                'Skincare ingredient analysis and selection',
                'Professional skincare treatments',
                'Advanced exfoliation techniques',
                'Skincare for different age groups',
                'Advanced moisturizing strategies',
                'Skincare for different skin concerns',
                'Advanced sun protection strategies',
                'Skincare routine customization'
            ],
            'advanced': [
                'Advanced dermatological treatments',
                'Skincare science and research',
                'Advanced skincare ingredient analysis',
                'Professional skincare consultation',
                'Advanced skincare treatment protocols',
                'Skincare for medical conditions',
                'Advanced skincare technology',
                'Skincare research and development',
                'Advanced skincare treatment methods',
                'Skincare optimization for professionals'
            ]
        },
        'Wellness': {
            'beginner': [
                'Take time for yourself every day',
                'Practice gratitude daily',
                'Connect with nature regularly',
                'Engage in activities you enjoy',
                'Maintain social connections',
                'Practice self-care routines',
                'Set boundaries in your life',
                'Engage in creative activities',
                'Practice relaxation techniques',
                'Maintain a positive outlook'
            ],
            'intermediate': [
                'Holistic wellness approaches',
                'Wellness lifestyle integration',
                'Advanced self-care strategies',
                'Wellness goal setting and tracking',
                'Wellness routine optimization',
                'Advanced wellness practices',
                'Wellness for different life stages',
                'Wellness lifestyle design',
                'Advanced wellness strategies',
                'Wellness optimization techniques'
            ],
            'advanced': [
                'Advanced wellness science and research',
                'Wellness optimization for professionals',
                'Advanced wellness protocols',
                'Wellness science and methodology',
                'Advanced wellness strategies',
                'Wellness optimization for performance',
                'Advanced wellness research',
                'Wellness science and technology',
                'Advanced wellness approaches',
                'Wellness optimization for experts'
            ]
        },
        'Digestive Health': {
            'beginner': [
                'Eat slowly and chew your food thoroughly',
                'Include fiber-rich foods in your diet',
                'Drink plenty of water throughout the day',
                'Eat regular meals at consistent times',
                'Include probiotic foods in your diet',
                'Avoid eating too close to bedtime',
                'Limit processed and fried foods',
                'Include a variety of vegetables in meals',
                'Practice mindful eating',
                'Listen to your body\'s hunger cues'
            ],
            'intermediate': [
                'Gut health optimization strategies',
                'Digestive enzyme supplementation',
                'Prebiotic and probiotic combinations',
                'Digestive health monitoring',
                'Advanced gut health protocols',
                'Digestive health for different conditions',
                'Advanced digestive strategies',
                'Gut health research and application',
                'Advanced digestive health',
                'Digestive health optimization'
            ],
            'advanced': [
                'Advanced digestive health science',
                'Gut microbiome research and application',
                'Advanced digestive protocols',
                'Digestive health for medical conditions',
                'Advanced gut health strategies',
                'Digestive health research methods',
                'Advanced digestive science',
                'Gut health optimization for professionals',
                'Advanced digestive health research',
                'Digestive health science and technology'
            ]
        },
        'Immune System': {
            'beginner': [
                'Wash your hands regularly with soap and water',
                'Get adequate sleep for immune function',
                'Eat a variety of colorful fruits and vegetables',
                'Stay hydrated throughout the day',
                'Manage stress through relaxation techniques',
                'Exercise regularly to boost immunity',
                'Avoid smoking and excessive alcohol',
                'Get regular sunlight exposure',
                'Practice good hygiene habits',
                'Maintain social connections for mental health'
            ],
            'intermediate': [
                'Immune system optimization strategies',
                'Advanced immune support protocols',
                'Immune health monitoring and tracking',
                'Advanced immune system support',
                'Immune health for different age groups',
                'Advanced immune strategies',
                'Immune system research and application',
                'Advanced immune health protocols',
                'Immune health optimization techniques',
                'Advanced immune system science'
            ],
            'advanced': [
                'Advanced immune system science',
                'Immune system research and development',
                'Advanced immune protocols',
                'Immune health for medical conditions',
                'Advanced immune system strategies',
                'Immune health research methods',
                'Advanced immune science',
                'Immune system optimization for professionals',
                'Advanced immune health research',
                'Immune system science and technology'
            ]
        },
        'Weight Management': {
            'beginner': [
                'Eat regular meals to avoid overeating',
                'Include protein in every meal',
                'Drink water before meals to feel full',
                'Use smaller plates to control portions',
                'Eat slowly and savor your food',
                'Include vegetables in every meal',
                'Limit sugary drinks and snacks',
                'Get regular physical activity',
                'Track your food intake',
                'Set realistic weight management goals'
            ],
            'intermediate': [
                'Advanced weight management strategies',
                'Metabolic optimization techniques',
                'Weight management for different body types',
                'Advanced nutrition for weight management',
                'Weight management monitoring and tracking',
                'Advanced weight management protocols',
                'Weight management for different life stages',
                'Advanced weight management strategies',
                'Weight management optimization techniques',
                'Advanced weight management science'
            ],
            'advanced': [
                'Advanced weight management science',
                'Weight management research and development',
                'Advanced weight management protocols',
                'Weight management for medical conditions',
                'Advanced weight management strategies',
                'Weight management research methods',
                'Advanced weight management science',
                'Weight management optimization for professionals',
                'Advanced weight management research',
                'Weight management science and technology'
            ]
        }
    }
    
    def __init__(self):
        """Initialize the topic bank."""
        self.categories = list(self.TOPIC_DATABASE.keys())
        self.difficulty_levels = ['beginner', 'intermediate', 'advanced']
    
    def get_topics_by_category(self, category: str, difficulty: str = None) -> List[str]:
        """
        Get topics for a specific category and optional difficulty level.
        
        Args:
            category: Health category name
            difficulty: Optional difficulty level filter
            
        Returns:
            List of topic strings
        """
        if category not in self.TOPIC_DATABASE:
            return []
        
        category_topics = self.TOPIC_DATABASE[category]
        
        if difficulty and difficulty in category_topics:
            return category_topics[difficulty]
        else:
            # Return all topics for the category
            all_topics = []
            for level_topics in category_topics.values():
                all_topics.extend(level_topics)
            return all_topics
    
    def get_random_topic(self, category: str = None, difficulty: str = None) -> str:
        """
        Get a random topic from the database.
        
        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            
        Returns:
            Random topic string
        """
        if category:
            topics = self.get_topics_by_category(category, difficulty)
        else:
            # Get random category if not specified
            if not category:
                category = random.choice(self.categories)
            topics = self.get_topics_by_category(category, difficulty)
        
        if not topics:
            return "General health and wellness tips"
        
        return random.choice(topics)
    
    def get_topics_by_difficulty(self, difficulty: str) -> List[str]:
        """
        Get all topics for a specific difficulty level across all categories.
        
        Args:
            difficulty: Difficulty level
            
        Returns:
            List of topic strings
        """
        all_topics = []
        for category in self.categories:
            topics = self.get_topics_by_category(category, difficulty)
            all_topics.extend(topics)
        return all_topics
    
    def get_category_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about topics in each category.
        
        Returns:
            Dict with category statistics
        """
        stats = {}
        for category in self.categories:
            category_data = self.TOPIC_DATABASE[category]
            stats[category] = {
                'beginner': len(category_data.get('beginner', [])),
                'intermediate': len(category_data.get('intermediate', [])),
                'advanced': len(category_data.get('advanced', [])),
                'total': sum(len(topics) for topics in category_data.values())
            }
        return stats
    
    def search_topics(self, keyword: str) -> List[Dict[str, str]]:
        """
        Search for topics containing a specific keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching topics with category and difficulty info
        """
        results = []
        keyword_lower = keyword.lower()
        
        for category in self.categories:
            for difficulty in self.difficulty_levels:
                topics = self.get_topics_by_category(category, difficulty)
                for topic in topics:
                    if keyword_lower in topic.lower():
                        results.append({
                            'topic': topic,
                            'category': category,
                            'difficulty': difficulty
                        })
        
        return results
    
    def get_diverse_topics(self, count: int = 5, exclude_categories: List[str] = None) -> List[Dict[str, str]]:
        """
        Get diverse topics across different categories and difficulty levels.
        
        Args:
            count: Number of topics to return
            exclude_categories: Categories to exclude
            
        Returns:
            List of diverse topics with metadata
        """
        if exclude_categories is None:
            exclude_categories = []
        
        available_categories = [cat for cat in self.categories if cat not in exclude_categories]
        
        if not available_categories:
            available_categories = self.categories
        
        diverse_topics = []
        used_combinations = set()
        
        while len(diverse_topics) < count and len(used_combinations) < len(available_categories) * len(self.difficulty_levels):
            category = random.choice(available_categories)
            difficulty = random.choice(self.difficulty_levels)
            
            combination = (category, difficulty)
            if combination not in used_combinations:
                used_combinations.add(combination)
                topics = self.get_topics_by_category(category, difficulty)
                if topics:
                    topic = random.choice(topics)
                    diverse_topics.append({
                        'topic': topic,
                        'category': category,
                        'difficulty': difficulty
                    })
        
        return diverse_topics


def test_topic_bank():
    """Test the topic bank functionality."""
    bank = TopicBank()
    
    print("🧪 Testing Topic Bank System")
    print("=" * 50)
    
    # Test category stats
    print("\n📊 Category Statistics:")
    stats = bank.get_category_stats()
    for category, data in stats.items():
        print(f"  {category}: {data['total']} topics ({data['beginner']}B, {data['intermediate']}I, {data['advanced']}A)")
    
    # Test random topic selection
    print(f"\n🎯 Random Topics:")
    for i in range(3):
        topic = bank.get_random_topic()
        print(f"  {i+1}. {topic}")
    
    # Test category-specific topics
    print(f"\n🏃 Fitness Topics (Beginner):")
    fitness_topics = bank.get_topics_by_category('Fitness', 'beginner')
    for i, topic in enumerate(fitness_topics[:3], 1):
        print(f"  {i}. {topic}")
    
    # Test diverse topic selection
    print(f"\n🌈 Diverse Topics:")
    diverse = bank.get_diverse_topics(5)
    for i, topic_data in enumerate(diverse, 1):
        print(f"  {i}. {topic_data['topic']} ({topic_data['category']}, {topic_data['difficulty']})")
    
    # Test search functionality
    print(f"\n🔍 Search Results for 'water':")
    search_results = bank.search_topics('water')
    for i, result in enumerate(search_results[:3], 1):
        print(f"  {i}. {result['topic']} ({result['category']})")
    
    print("\n✅ Topic bank test completed!")


if __name__ == "__main__":
    test_topic_bank()
