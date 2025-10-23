"""
AI Content Generator for Skincare
Generates video prompts and blog posts using OpenAI API
"""

import os
import json
from typing import Dict, Optional
from openai import OpenAI


class SkincareContentGenerator:
    """Generate skincare content using OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
    
    def generate_content_package(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict:
        """
        Generate complete content package: video prompt + blog post.
        
        Args:
            topic: Specific topic (optional, will auto-generate if None)
            category: Skincare category (Cleansing, Moisturizing, Anti-Aging, Acne, Sun Protection, etc.)
            
        Returns:
            Dict with video_prompt, blog_post, and metadata
        """
        
        system_prompt = """You are an expert skincare professional and dermatologist.

Generate a complete content package for a skincare blog and social media.

CRITICAL VIDEO PROMPT REQUIREMENTS:
- Maximum 12 seconds of content (STRICT LIMIT)
- Single continuous shot (no scene changes)
- Expert skincare professional talking directly to camera
- Professional expert in relevant skincare environment (clinic, spa, or professional setup)
- Include exact timing breakdown that totals ≤12 seconds
- Specify: camera angle, lighting, setting, expert appearance
- Expert should look like a real dermatologist/skincare professional
- Visual, actionable skincare demonstration (not just talking)
- Professional attire (lab coat, medical scrubs, or professional clothing)

BLOG POST REQUIREMENTS:
- 800-1500 words
- SEO optimized for skincare niche
- Actionable, practical skincare advice
- Expert dermatologist tone but accessible
- Include introduction, main content sections, conclusion
- Focus on one clear skincare benefit/tip
- Evidence-based when possible
- Engaging headlines and subheadings

SEO REQUIREMENTS:
- Compelling title with skincare keywords
- Meta description (150-160 characters)
- 3-5 relevant skincare tags
- Focus keywords for search
- Category (Cleansing, Moisturizing, Anti-Aging, Acne, Sun Protection, etc.)

Return ONLY valid JSON with this exact structure:
{
  "video_prompt": {
    "prompt": "DETAILED visual description with timing breakdown",
    "duration": 12,
    "timing_breakdown": "Describe how 12 seconds are used",
    "expert_type": "e.g., dermatologist, skincare specialist"
  },
  "blog_post": {
    "title": "SEO-optimized title",
    "content": "Full HTML formatted blog post",
    "excerpt": "150 character teaser",
    "category": "One of: Cleansing, Moisturizing, Anti-Aging, Acne, Sun Protection, etc.",
    "tags": ["tag1", "tag2", "tag3"],
    "meta_description": "150-160 char SEO description",
    "focus_keywords": ["keyword1", "keyword2"]
  },
  "metadata": {
    "unique_id": "unique-slug-identifier",
    "difficulty": "beginner/intermediate/advanced",
    "estimated_read_time": "3 min"
  }
}"""

        # Build user prompt
        if topic:
            user_prompt = f"Generate a skincare content package about: {topic}"
        else:
            user_prompt = "Generate a unique, engaging skincare content package on any relevant topic."
        
        if category:
            user_prompt += f"\nCategory must be: {category}"
        
        user_prompt += "\n\nEnsure video prompt is DETAILED with exact timing that totals ≤12 seconds."
        
        try:
            print("🤖 Generating content with OpenAI...")
            
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
            
            print("✅ Content package generated!")
            print(f"   Topic: {content_data['blog_post']['title']}")
            print(f"   Category: {content_data['blog_post']['category']}")
            print(f"   Video Duration: {content_data['video_prompt']['duration']}s")
            
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
    
    def validate_video_prompt(self, video_prompt: Dict) -> bool:
        """
        Validate video prompt meets requirements.
        
        Args:
            video_prompt: Video prompt dict from generated content
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ['prompt', 'duration', 'timing_breakdown']
        
        # Check required keys
        if not all(key in video_prompt for key in required_keys):
            print("⚠️ Video prompt missing required keys")
            return False
        
        # Check duration constraint
        duration = video_prompt.get('duration', 0)
        if duration > 12:
            print(f"⚠️ Video duration {duration}s exceeds 12 second limit")
            return False
        
        # Check prompt detail
        prompt_text = video_prompt.get('prompt', '')
        if len(prompt_text) < 100:
            print("⚠️ Video prompt too short (needs more detail)")
            return False
        
        return True
    
    def generate_topic_ideas(self, count: int = 5) -> list:
        """
        Generate unique content topic ideas.
        
        Args:
            count: Number of ideas to generate
            
        Returns:
            List of topic strings
        """
        prompt = f"""Generate {count} unique, specific skincare content ideas.

Requirements:
- Practical, actionable skincare tips
- Suitable for 12-second video demonstration
- Engaging for social media
- Mix across categories: Cleansing, Moisturizing, Anti-Aging, Acne, Sun Protection, etc.

Return as JSON array of topic strings.
Example: ["How to properly apply sunscreen for maximum protection", "Quick morning skincare routine for busy professionals"]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a skincare content strategist."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.9
            )
            
            result = json.loads(response.choices[0].message.content)
            topics = result.get('topics', [])
            
            print(f"✅ Generated {len(topics)} topic ideas")
            return topics
            
        except Exception as e:
            print(f"❌ Failed to generate topics: {e}")
            return []


def test_content_generator():
    """Test the content generator."""
    generator = SkincareContentGenerator()
    
    # Test content generation
    print("\n" + "="*70)
    print("🧪 Testing Content Generator")
    print("="*70)
    
    result = generator.generate_content_package(topic="proper sunscreen application technique")
    
    if result['success']:
        data = result['data']
        
        print("\n📹 Video Prompt:")
        print(f"Duration: {data['video_prompt']['duration']}s")
        print(f"Prompt: {data['video_prompt']['prompt'][:200]}...")
        print(f"Timing: {data['video_prompt']['timing_breakdown']}")
        
        print("\n📝 Blog Post:")
        print(f"Title: {data['blog_post']['title']}")
        print(f"Category: {data['blog_post']['category']}")
        print(f"Tags: {', '.join(data['blog_post']['tags'])}")
        print(f"Content length: {len(data['blog_post']['content'])} chars")
        
        print("\n✅ Test successful!")
    else:
        print(f"\n❌ Test failed: {result['error']}")


if __name__ == "__main__":
    test_content_generator()

