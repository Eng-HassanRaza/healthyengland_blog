"""
Enhanced Content Generator for Diverse Health Topics
Generates video prompts and blog posts across multiple health categories
"""

import os
import json
import uuid
from typing import Dict, Optional, List
from openai import OpenAI

from sora.utils.smart_selector import SmartTopicSelector
from sora.utils.diversity_engine import TopicDiversityEngine
from sora.models import GeneratedContent


class EnhancedContentGenerator:
    """Generate diverse health content using OpenAI with smart topic selection."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client and diversity systems."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
        self.smart_selector = SmartTopicSelector()
        self.diversity_engine = TopicDiversityEngine()
    
    def generate_content_package(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        use_smart_selection: bool = True
    ) -> Dict:
        """
        Generate complete content package with diversity optimization.
        
        Args:
            topic: Specific topic (optional, will auto-generate if None)
            category: Health category (optional, will auto-select if None)
            difficulty: Difficulty level (optional, will auto-select if None)
            use_smart_selection: Whether to use smart topic selection
            
        Returns:
            Dict with video_prompt, blog_post, and metadata
        """
        
        # Smart topic selection if enabled
        if use_smart_selection and not topic:
            selection_result = self.smart_selector.select_optimal_topic(
                preferred_category=category,
                difficulty=difficulty
            )
            topic = selection_result['topic']
            category = selection_result['category']
            difficulty = selection_result['difficulty']
        
        # Generate system prompt based on category
        system_prompt = self._generate_system_prompt(category)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(topic, category, difficulty)
        
        try:
            print("🤖 Generating diverse health content with OpenAI...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8
            )
            
            content_json = response.choices[0].message.content
            content_data = json.loads(content_json)
            
            # Add diversity metadata
            content_data['diversity_metadata'] = {
                'category': category,
                'difficulty': difficulty,
                'topic_keywords': self.diversity_engine.extract_topic_keywords(topic),
                'unique_id': str(uuid.uuid4())[:8]
            }
            
            # Convert camelCase to snake_case for consistency
            if 'videoPrompt' in content_data:
                content_data['video_prompt'] = content_data.pop('videoPrompt')
            if 'blogPost' in content_data:
                content_data['blog_post'] = content_data.pop('blogPost')
            if 'video' in content_data:
                content_data['video_prompt'] = content_data.pop('video')
            if 'content_package' in content_data:
                content_data['blog_post'] = content_data.pop('content_package')
            
            # Ensure category field exists in blog_post
            if 'blog_post' in content_data and 'category' not in content_data['blog_post']:
                content_data['blog_post']['category'] = category
            
            print("✅ Diverse content package generated!")
            
            # Debug: Print content structure
            print(f"   Content keys: {list(content_data.keys())}")
            
            if 'blog_post' in content_data:
                print(f"   Topic: {content_data['blog_post']['title']}")
                print(f"   Category: {content_data['blog_post']['category']}")
            else:
                print("   ⚠️ No blog_post found in content data")
            
            # Safely access video duration
            video_duration = content_data.get('video_prompt', {}).get('duration', '12 seconds')
            print(f"   Video Duration: {video_duration}")
            
            return {
                "success": True,
                "data": content_data
            }
            
        except Exception as e:
            print(f"❌ Content generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_system_prompt(self, category: str) -> str:
        """Generate system prompt based on health category."""
        
        category_prompts = {
            'Nutrition': """You are a nutrition expert. Create a 12-second video + blog post about healthy eating.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in kitchen or garden
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Chef apron or casual professional (NOT medical scrubs)
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about nutrition
- Category: Nutrition
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags

SPEECH CONTENT REQUIREMENTS:
- MUST be a practical health/fitness tip (NOT motivational)
- Focus on actionable advice (what to do, how to do it)
- Avoid motivational language like "you can do it", "believe in yourself"
- Use instructional language like "try this", "do this", "use this method"
- Examples: "Drink lemon water for energy", "Try chamomile tea for sleep", "Take deep breaths for focus" """,

            'Fitness': """You are a fitness expert. Create a 12-second video + blog post about exercise.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in gym or outdoor
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Athletic wear (yoga pants, tank top) NOT medical scrubs
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about fitness
- Category: Fitness
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags""",

            'Mental Health': """You are a mental health expert. Create a 12-second video + blog post about wellness.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in office or home
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Casual professional (blouse, cardigan) NOT medical scrubs
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about mental health
- Category: Mental Health
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags""",

            'Sleep': """You are a sleep expert. Create a 12-second video + blog post about sleep.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in bedroom
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Comfortable clothes (sweater, pajamas) NOT medical scrubs
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about sleep
- Category: Sleep
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags""",

            'Hydration': """You are a hydration expert. Create a 12-second video + blog post about water intake.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in gym or outdoor
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Athletic wear (sports wear) NOT medical scrubs
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about hydration
- Category: Hydration
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags"""
        }
        
        # Default to general health if category not found
        default_prompt = """You are a health expert. Create a 12-second video + blog post about wellness.

VIDEO REQUIREMENTS:
- 12 seconds total (no more, no less)
- Expert talking to camera in home or office
- Natural remedies only (NO products, technology, or devices)
- Hook: 3-4 seconds, Tip: 8-9 seconds
- Character: European/English/African only
- Attire: Casual professional (wellness clothing) NOT medical scrubs
- Speech: MAXIMUM 1 sentence (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)
- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)
- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)

BLOG POST REQUIREMENTS:
- 800-1500 words about health
- Category: Health
- SEO optimized with keywords
- Natural remedies focus
- Include title, meta description, tags

SPEECH CONTENT REQUIREMENTS:
- MUST be a practical health/fitness tip (NOT motivational)
- Focus on actionable advice (what to do, how to do it)
- Avoid motivational language like "you can do it", "believe in yourself"
- Use instructional language like "try this", "do this", "use this method"
- Examples: "Drink lemon water for energy", "Try chamomile tea for sleep", "Take deep breaths for focus" """
        
        return category_prompts.get(category, default_prompt)
    
    def _get_character_variety(self, category: str) -> str:
        """Get diverse character types for each category."""
        import random
        
        character_varieties = {
            'Nutrition': [
                "chef in kitchen", "nutritionist in garden", "wellness coach at home",
                "dietitian in clinic", "healthy cooking instructor", "organic food specialist"
            ],
            'Fitness': [
                "yoga instructor in studio", "personal trainer at gym", "fitness coach outdoors",
                "pilates instructor", "crossfit trainer", "outdoor fitness guide"
            ],
            'Mental Health': [
                "therapist in office", "wellness coach at home", "meditation instructor",
                "life coach in nature", "stress management specialist", "mindfulness expert"
            ],
            'Sleep': [
                "sleep specialist in bedroom", "wellness coach in bedroom", "sleep consultant at home",
                "relaxation expert in bedroom", "sleep therapist in clinic"
            ],
            'Hydration': [
                "hydration specialist at gym", "sports nutritionist outdoors", "wellness coach at home",
                "fitness trainer with water", "health coach in nature"
            ]
        }
        
        return random.choice(character_varieties.get(category, ["health professional"]))
    
    def _validate_environment(self, category: str, environment: str) -> bool:
        """Validate that environment matches category requirements."""
        
        valid_environments = {
            'Nutrition': ['kitchen', 'garden', 'farmers market', 'home', 'clinic', 'cooking area', 'organic garden'],
            'Fitness': ['gym', 'studio', 'park', 'outdoor', 'home workout', 'yoga studio', 'hiking trail', 'beach'],
            'Mental Health': ['office', 'home', 'nature', 'clinic', 'therapy room', 'meditation space'],
            'Sleep': ['bedroom', 'home', 'clinic', 'sleep center', 'relaxation space'],
            'Hydration': ['gym', 'outdoor', 'home', 'clinic', 'sports center', 'nature']
        }
        
        return any(valid_env in environment.lower() for valid_env in valid_environments.get(category, []))
    
    def _build_user_prompt(self, topic: str, category: str, difficulty: str) -> str:
        """Build user prompt for content generation."""
        user_prompt = f"Generate a health content package about: {topic}"
        
        if category:
            user_prompt += f"\nCategory must be: {category}"
        
        if difficulty:
            user_prompt += f"\nDifficulty level: {difficulty}"
        
        # Add character variety suggestion
        character_suggestion = self._get_character_variety(category)
        user_prompt += f"\n\nCHARACTER VARIETY: Use this character type: {character_suggestion}"
        
        user_prompt += "\n\nIMPORTANT RULES:\n- 12 seconds total video (STRICT LIMIT)\n- Natural remedies only (NO products, technology, devices)\n- European/English/African characters only\n- MAXIMUM 1 sentence speech (8-10 words total) - MUST be a practical health/fitness tip (NOT motivational)\n- Hook: 3-4 seconds, Tip: 8-9 seconds\n- FIRST FRAME: Hook text overlay in center of screen (large, bold, readable text)\n- AUDIO BUFFER: Start with 2-second silence/pause before speech begins (to prevent first second audio cutoff)\n- Appropriate environment for category\n- Return valid JSON"
        
        return user_prompt
    
    def generate_diverse_content_batch(self, count: int = 3) -> List[Dict]:
        """
        Generate multiple diverse content pieces.
        
        Args:
            count: Number of content pieces to generate
            
        Returns:
            List of content generation results
        """
        results = []
        
        for i in range(count):
            print(f"\n📝 Generating content piece {i+1}/{count}")
            
            # Use smart selection for diversity
            result = self.generate_content_package(use_smart_selection=True)
            results.append(result)
            
            if result['success']:
                print(f"✅ Content {i+1} generated successfully")
            else:
                print(f"❌ Content {i+1} failed: {result['error']}")
        
        return results
    
    def track_generated_content(self, content_data: Dict, video_id: str = None, video_url: str = None) -> GeneratedContent:
        """
        Track generated content in the database for diversity analysis.
        
        Args:
            content_data: Generated content data
            video_id: Sora video ID
            video_url: S3 video URL
            
        Returns:
            GeneratedContent instance
        """
        blog_post = content_data.get('blog_post', {})
        video_prompt = content_data.get('video_prompt', {})
        diversity_metadata = content_data.get('diversity_metadata', {})
        
        # Extract topic keywords for similarity detection
        topic = blog_post.get('title', '')
        topic_keywords = self.diversity_engine.extract_topic_keywords(topic)
        
        # Create GeneratedContent record
        generated_content = GeneratedContent.objects.create(
            title=blog_post.get('title', ''),
            topic=topic,
            category=blog_post.get('category', ''),
            unique_id=diversity_metadata.get('unique_id', ''),
            video_id=video_id,
            video_url=video_url,
            video_prompt=video_prompt.get('prompt', ''),
            difficulty_level=diversity_metadata.get('difficulty', 'beginner'),
            tags=blog_post.get('tags', []),
            focus_keywords=blog_post.get('focus_keywords', []),
            topic_keywords=topic_keywords,
            is_published=True
        )
        
        return generated_content
    
    def get_diversity_report(self) -> Dict:
        """Get comprehensive diversity report."""
        return self.smart_selector.get_next_content_strategy()


def test_enhanced_generator():
    """Test the enhanced content generator."""
    generator = EnhancedContentGenerator()
    
    print("🧪 Testing Enhanced Content Generator")
    print("=" * 50)
    
    # Test single content generation
    print("\n📝 Single Content Generation:")
    result = generator.generate_content_package(use_smart_selection=True)
    
    if result['success']:
        data = result['data']
        print(f"✅ Generated: {data['blog_post']['title']}")
        print(f"   Category: {data['blog_post']['category']}")
        print(f"   Duration: {data['video_prompt']['duration']}s")
    else:
        print(f"❌ Failed: {result['error']}")
    
    # Test diversity report
    print(f"\n📊 Diversity Report:")
    report = generator.get_diversity_report()
    print(f"   Recommended category: {report['recommended_category']}")
    print(f"   Strategy: {report['strategy']}")
    
    print("\n✅ Enhanced generator test completed!")


if __name__ == "__main__":
    test_enhanced_generator()
