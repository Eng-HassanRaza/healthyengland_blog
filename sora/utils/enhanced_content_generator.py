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
            'Nutrition': """You are an expert nutritionist and registered dietitian.

Generate a complete content package for a nutrition and healthy eating blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert nutritionist/dietitian talking directly to camera
- Professional expert in relevant nutrition environment (kitchen, clinic, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real nutritionist/dietitian
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (lab coat, medical scrubs, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds
- KEEP SPEECH SHORT AND CONCISE - MAXIMUM 2-3 SENTENCES TOTAL
- NO LONG EXPLANATIONS - JUST THE ESSENTIAL TIP

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for nutrition and healthy eating niche
- Actionable, practical nutrition advice
- Expert nutritionist tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear nutrition benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with nutrition keywords
- Meta description (150-160 characters)
- 3-5 relevant nutrition tags
- Focus keywords for search
- Category (Nutrition, Healthy Eating, Meal Planning, etc.)""",

            'Fitness': """You are an expert fitness trainer and exercise physiologist.

Generate a complete content package for a fitness and exercise blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert fitness trainer talking directly to camera
- Professional expert in relevant fitness environment (gym, studio, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real fitness trainer/coach
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (fitness gear, athletic wear, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for fitness and exercise niche
- Actionable, practical fitness advice
- Expert trainer tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear fitness benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with fitness keywords
- Meta description (150-160 characters)
- 3-5 relevant fitness tags
- Focus keywords for search
- Category (Fitness, Exercise, Workout, etc.)""",

            'Mental Health': """You are an expert mental health professional and psychologist.

Generate a complete content package for a mental health and wellness blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert mental health professional talking directly to camera
- Professional expert in relevant mental health environment (office, clinic, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real psychologist/therapist
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (lab coat, medical scrubs, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for mental health and wellness niche
- Actionable, practical mental health advice
- Expert psychologist tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear mental health benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with mental health keywords
- Meta description (150-160 characters)
- 3-5 relevant mental health tags
- Focus keywords for search
- Category (Mental Health, Wellness, Stress Management, etc.)""",

            'Sleep': """You are an expert sleep specialist and sleep medicine doctor.

Generate a complete content package for a sleep and rest optimization blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert sleep specialist talking directly to camera
- Professional expert in relevant sleep environment (bedroom, clinic, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real sleep doctor/specialist
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (lab coat, medical scrubs, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for sleep and rest niche
- Actionable, practical sleep advice
- Expert sleep specialist tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear sleep benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with sleep keywords
- Meta description (150-160 characters)
- 3-5 relevant sleep tags
- Focus keywords for search
- Category (Sleep, Rest, Sleep Hygiene, etc.)""",

            'Hydration': """You are an expert hydration specialist and sports medicine doctor.

Generate a complete content package for a hydration and water intake blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert hydration specialist talking directly to camera
- Professional expert in relevant hydration environment (clinic, gym, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real hydration specialist/doctor
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (lab coat, medical scrubs, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for hydration and water intake niche
- Actionable, practical hydration advice
- Expert hydration specialist tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear hydration benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with hydration keywords
- Meta description (150-160 characters)
- 3-5 relevant hydration tags
- Focus keywords for search
- Category (Hydration, Water Intake, Fluid Balance, etc.)"""
        }
        
        # Default to general health if category not found
        default_prompt = """You are an expert health professional and wellness specialist.

Generate a complete content package for a health and wellness blog.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- EXACTLY 12 seconds of content (STRICT LIMIT - NO MORE, NO LESS)
- Single continuous shot (no scene changes)
- Expert health professional talking directly to camera
- Professional expert in relevant health environment (clinic, office, or professional setup)
- Include exact timing breakdown that totals EXACTLY 12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real health professional
- Focus on NATURAL/HOME REMEDIES and LIFESTYLE TIPS (NO product promotion)
- Professional attire (lab coat, medical scrubs, or professional clothing)
- STRONG HOOK in first 3-4 seconds to grab attention
- NO third-party products, brands, or commercial items visible
- Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities)
- Complete the tip in 10 seconds

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for health and wellness niche
- Actionable, practical health advice
- Expert health professional tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear health benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with health keywords
- Meta description (150-160 characters)
- 3-5 relevant health tags
- Focus keywords for search
- Category (Health, Wellness, Lifestyle, etc.)"""
        
        return category_prompts.get(category, default_prompt)
    
    def _build_user_prompt(self, topic: str, category: str, difficulty: str) -> str:
        """Build user prompt for content generation."""
        user_prompt = f"Generate a health content package about: {topic}"
        
        if category:
            user_prompt += f"\nCategory must be: {category}"
        
        if difficulty:
            user_prompt += f"\nDifficulty level: {difficulty}"
        
        user_prompt += "\n\nIMPORTANT: Video prompt must be DETAILED with exact timing that totals EXACTLY 12 seconds. Focus on natural health tips, home remedies, lifestyle advice - NO product promotion. Include a strong hook in the first 3-4 seconds. Add European/English/African race character in the video (NO Asian, Hispanic, or other ethnicities). Complete the tip in 10 seconds.\n\nRACE RESTRICTIONS: Only use European (Caucasian), English, or African race characters. NO Asian, Hispanic, Middle Eastern, or other ethnicities allowed.\n\nCRITICAL: Keep the spoken content SHORT - maximum 2-3 sentences total. The expert should speak quickly and concisely. NO long explanations or detailed descriptions. Just the essential tip that can be delivered in 10 seconds of speech.\n\nReturn ONLY valid JSON with this exact structure."
        
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
