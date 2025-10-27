"""
Automated Content Pipeline
Generates video prompts, creates videos, and publishes blog posts
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthyengland.settings')
django.setup()

from django.contrib.auth.models import User
from sora.utils.enhanced_content_generator import EnhancedContentGenerator
from sora.utils.generator import SoraVideoGenerator
from sora.utils.enhanced_duplicate_detection import EnhancedDuplicateDetector
from blog.utils import check_duplicate_post, create_blog_post_from_content


class AutoContentPipeline:
    """Automated pipeline for creating video + blog content."""
    
    def __init__(self):
        """Initialize pipeline."""
        self.content_generator = EnhancedContentGenerator()
        self.video_generator = SoraVideoGenerator()
        self.duplicate_detector = EnhancedDuplicateDetector()
        
        # Get default author (admin user)
        try:
            self.author = User.objects.filter(is_staff=True).first()
            if not self.author:
                raise ValueError("No admin user found. Create one first.")
        except Exception as e:
            raise ValueError(f"Could not get author: {e}")
        
        # Fallback topics and categories for robust generation
        self.fallback_topics = [
            "Energy Boost", "Sleep Better", "Stress Relief", "Hydration Tips", 
            "Healthy Snacks", "Morning Routine", "Evening Routine", "Mental Health",
            "Physical Fitness", "Nutrition Tips", "Immune System", "Digestive Health",
            "Heart Health", "Brain Function", "Skin Care", "Hair Health",
            "Weight Management", "Muscle Building", "Flexibility", "Meditation"
        ]
        
        self.fallback_categories = [
            "Health", "Wellness", "Nutrition", "Fitness", "Mental Health",
            "Sleep", "Hydration", "Stress Management", "Lifestyle", "Prevention"
        ]
    
    def _optimize_video_prompt(self, prompt: str) -> str:
        """
        Use AI to optimize video prompt for 12-second video.
        
        Args:
            prompt: Original video prompt
            
        Returns:
            Optimized prompt that fits 12-second criteria
        """
        try:
            import openai
            from django.conf import settings
            
            # Get OpenAI API key
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                print("   ⚠️ OpenAI API key not found - using fallback optimization")
                return self._fallback_optimize_prompt(prompt)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Create optimization prompt
            optimization_prompt = f"""
You are a video content optimizer. Your task is to shorten this video prompt to fit EXACTLY in a 12-second video.

ORIGINAL PROMPT:
{prompt}

CRITICAL REQUIREMENTS:
- Maximum 80 characters total (STRICT LIMIT)
- Must be spoken in 8-10 seconds maximum (LEAVE 2-4 seconds buffer)
- Keep ONLY the most essential message
- Make it extremely punchy and concise
- Use short, simple words
- Remove all unnecessary words
- A white blonde doctor in her 30s giving home remedy tips for better health
- This video is live in the background full screen showing the actual remedy contents (how to make it, how to use it, how to avoid it)
- NO person should be displayed in this background full screen display
- In the bottom left corner: a white blonde doctor in her 30s should be giving this home remedy tip
- Video timing: wait for half a second before starting, end talking half or one second before 12-second video length
- MUST be a practical health/fitness tip (NOT motivational content)

EXAMPLES OF GOOD 12-SECOND HEALTH/FITNESS TIPS:
- "A white blonde doctor in her 30s in bottom left corner says: 'Low energy? Drink lemon water for instant boost.' Background shows how to make lemon water. Wait 0.5s before speaking, end 0.5s before 12s."
- "A white blonde doctor in her 30s in bottom left corner says: 'Can't sleep? Try chamomile tea before bed.' Background shows how to prepare chamomile tea. Wait 0.5s before speaking, end 0.5s before 12s."
- "A white blonde doctor in her 30s in bottom left corner says: 'Need focus? Take a 5-minute walk outside.' Background shows walking technique. Wait 0.5s before speaking, end 0.5s before 12s."

Return ONLY the optimized prompt, nothing else.
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a video content optimizer. Shorten prompts to fit 12-second videos while keeping the essential message."},
                    {"role": "user", "content": optimization_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            optimized = response.choices[0].message.content.strip()
            
            # Validate the optimized prompt - MUCH STRICTER for 12-second videos
            if len(optimized) <= 80 and len(optimized) >= 20:
                print(f"   ✅ AI optimization successful: {len(optimized)} chars (within 80 char limit)")
                return optimized
            else:
                print(f"   ⚠️ AI optimization result too long/short: {len(optimized)} chars (must be ≤80)")
                return None
                
        except Exception as e:
            print(f"   ⚠️ AI optimization failed: {e}")
            return self._fallback_optimize_prompt(prompt)
    
    def _extract_remedy_content(self, blog_post: dict) -> str:
        """
        Extract specific remedy content from blog post for video background.
        
        Args:
            blog_post: Blog post content dictionary
            
        Returns:
            String with specific remedy instructions for video background
        """
        try:
            content = blog_post.get('content', [])
            if isinstance(content, list):
                # Look for sections with remedy subsections
                for section in content:
                    if isinstance(section, dict):
                        # Check if this section has remedy subsections
                        subsections = section.get('subsections', [])
                        if subsections:
                            remedy_instructions = []
                            for subsection in subsections[:3]:  # Take first 3 remedies
                                if isinstance(subsection, dict):
                                    title = subsection.get('title', '')
                                    paragraph = subsection.get('paragraph', '')
                                    if title and paragraph:
                                        # Extract key instructions (just first sentence)
                                        instructions = paragraph.split('. ')[:1]  # First sentence only
                                        remedy_instructions.append(f"{title}: {' '.join(instructions)}")
                            
                            if remedy_instructions:
                                return '. '.join(remedy_instructions)
                        
                        # Also check for section_content with remedy_title
                        section_content = section.get('section_content', [])
                        if isinstance(section_content, list):
                            remedy_instructions = []
                            for remedy in section_content[:3]:  # Take first 3 remedies
                                if isinstance(remedy, dict):
                                    title = remedy.get('remedy_title', '')
                                    description = remedy.get('remedy_description', '')
                                    if title and description:
                                        # Extract key instructions (just first sentence)
                                        instructions = description.split('. ')[:1]  # First sentence only
                                        remedy_instructions.append(f"{title}: {' '.join(instructions)}")
                            
                            if remedy_instructions:
                                return '. '.join(remedy_instructions)
            
            # Fallback: look for any content with remedy keywords (very short versions)
            content_str = str(content).lower()
            if 'green tea' in content_str:
                return "Green tea: Boil, steep, drink"
            elif 'smoothie' in content_str:
                return "Smoothie: Blend ingredients"
            elif 'chocolate' in content_str:
                return "Dark chocolate: Small piece"
            elif 'nuts' in content_str:
                return "Nuts: Handful snack"
            elif 'water' in content_str or 'hydration' in content_str:
                return "Hydration: Drink water"
            
            return "Natural remedy preparation and usage demonstration"
            
        except Exception as e:
            print(f"   ⚠️ Error extracting remedy content: {e}")
            return "Natural remedy preparation and usage demonstration"
    
    def _extract_speech_text(self, prompt_obj: dict) -> str:
        """Extract spoken line from various prompt shapes.
        Searches common keys recursively: speech, tip, hook, script.{tip|speech}, content.* variants.
        Returns first plausible short string found, else empty string.
        """
        try:
            from collections import deque
            queue = deque()
            if isinstance(prompt_obj, dict):
                queue.append(prompt_obj)
            elif isinstance(prompt_obj, list):
                for item in prompt_obj:
                    if isinstance(item, dict):
                        queue.append(item)
            
            def extract_from_value(value) -> str:
                if isinstance(value, str):
                    return value.strip()
                if isinstance(value, dict):
                    # Prefer common text fields
                    if 'text' in value and isinstance(value['text'], str):
                        return value['text'].strip()
                    if 'content' in value and isinstance(value['content'], str):
                        return value['content'].strip()
                    # Direct speech/tip fields
                    if 'speech' in value and isinstance(value['speech'], str):
                        return value['speech'].strip()
                    if 'tip' in value and isinstance(value['tip'], str):
                        return value['tip'].strip()
                return ''
            
            seen = set()
            while queue:
                node = queue.popleft()
                node_id = id(node)
                if node_id in seen:
                    continue
                seen.add(node_id)
                
                # Direct fields
                for key in ('speech', 'tip', 'hook'):
                    if key in node:
                        text = extract_from_value(node[key])
                        if text:
                            return text
                
                # Script variants
                if 'script' in node and isinstance(node['script'], (dict, list)):
                    script = node['script']
                    if isinstance(script, dict):
                        for key in ('speech', 'tip', 'hook'):
                            if key in script:
                                text = extract_from_value(script[key])
                                if text:
                                    return text
                    else:
                        for item in script:
                            if isinstance(item, dict):
                                for key in ('speech', 'tip', 'hook', 'text', 'content'):
                                    if key in item:
                                        text = extract_from_value(item[key])
                                        if text:
                                            return text
                
                # Content variants
                if 'content' in node and isinstance(node['content'], (dict, list)):
                    content = node['content']
                    if isinstance(content, dict):
                        # Common nested paths like content.character.speech, content.doctor.speech, content.remedy_details.tip.speech
                        for path in (
                            ('character', 'speech'),
                            ('doctor', 'speech'),
                            ('remedy_details', 'tip', 'speech'),
                            ('remedy', 'tip', 'speech'),
                        ):
                            cur = content
                            ok = True
                            for part in path:
                                if isinstance(cur, dict) and part in cur:
                                    cur = cur[part]
                                else:
                                    ok = False
                                    break
                            if ok:
                                text = extract_from_value(cur)
                                if text:
                                    return text
                        # Fallback: breadth-first through content dict
                        for v in content.values():
                            if isinstance(v, (dict, list)):
                                queue.append(v)
                            else:
                                text = extract_from_value(v)
                                if text:
                                    return text
                    else:
                        for item in content:
                            if isinstance(item, (dict, list)):
                                queue.append(item)
                
                # Enqueue other dict values
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        queue.append(v)
            return ''
        except Exception:
            return ''
    
    def _constrain_speech_length(self, speech_text: str, max_words: int = 10) -> str:
        """Ensure speech fits within target duration by capping words."""
        try:
            words = speech_text.strip().split()
            if len(words) <= max_words:
                return speech_text.strip()
            return ' '.join(words[:max_words]).rstrip(',;:.!')
        except Exception:
            return speech_text.strip()
    
    def _generate_content_with_fallbacks(self, original_topic: Optional[str] = None, original_category: Optional[str] = None, max_attempts: int = 5) -> Dict:
        """
        Generate content with robust fallback system to ensure content is always generated.
        
        Args:
            original_topic: Original topic to try first
            original_category: Original category to try first
            max_attempts: Maximum number of attempts (default 5)
            
        Returns:
            Dict with success status and content data
        """
        import random
        
        # Prepare topic and category lists for fallbacks
        topics_to_try = []
        categories_to_try = []
        
        # Add original topic/category first if provided
        if original_topic:
            topics_to_try.append(original_topic)
        if original_category:
            categories_to_try.append(original_category)
        
        # Add fallback topics and categories
        topics_to_try.extend(self.fallback_topics)
        categories_to_try.extend(self.fallback_categories)
        
        # Remove duplicates while preserving order
        topics_to_try = list(dict.fromkeys(topics_to_try))
        categories_to_try = list(dict.fromkeys(categories_to_try))
        
        print(f"🔄 Robust content generation: Will try up to {max_attempts} combinations")
        print(f"   📝 Topics to try: {len(topics_to_try)}")
        print(f"   📂 Categories to try: {len(categories_to_try)}")
        
        for attempt in range(max_attempts):
            # Select topic and category for this attempt
            if attempt < len(topics_to_try):
                current_topic = topics_to_try[attempt]
            else:
                # Random selection if we've exhausted the list
                current_topic = random.choice(self.fallback_topics)
            
            if attempt < len(categories_to_try):
                current_category = categories_to_try[attempt]
            else:
                # Random selection if we've exhausted the list
                current_category = random.choice(self.fallback_categories)
            
            print(f"\n🎯 Attempt {attempt + 1}/{max_attempts}: Topic='{current_topic}', Category='{current_category}'")
            
            try:
                # Generate content with current topic/category
                content_result = self.content_generator.generate_content_package(
                    topic=current_topic,
                    category=current_category,
                    use_smart_selection=True
                )
                
                if not content_result['success']:
                    print(f"   ❌ Content generation failed: {content_result['error']}")
                    continue
                
                content_data = content_result['data']
                
                if not content_data or 'blog_post' not in content_data:
                    print(f"   ❌ Invalid content data received")
                    continue
                
                blog_post = content_data.get('blog_post', {})
                title = blog_post.get('title', '')
                category = blog_post.get('category', 'Unknown')
                
                print(f"   📝 Generated: '{title}' (Category: {category})")
                
                # Check for similarity
                try:
                    similarity_check = self.duplicate_detector.check_content_similarity(title, title, category)
                    if similarity_check['is_similar']:
                        print(f"   ⚠️ Content too similar: {similarity_check['recommendations']}")
                        continue
                    
                    print(f"   ✅ Content is unique and diverse")
                    
                    # Check for duplicates
                    unique_id = content_data.get('diversity_metadata', {}).get('unique_id')
                    if check_duplicate_post(title=title, unique_id=unique_id):
                        print(f"   ⚠️ Duplicate content detected: {title}")
                        continue
                    
                    print(f"   ✅ No duplicates found")
                    
                    # Success! Return the content
                    print(f"🎉 Successfully generated unique content on attempt {attempt + 1}")
                    return {
                        "success": True,
                        "data": content_data,
                        "attempt": attempt + 1,
                        "topic_used": current_topic,
                        "category_used": current_category
                    }
                    
                except Exception as e:
                    print(f"   ⚠️ Similarity check failed: {e}")
                    # Continue to next attempt
                    continue
                    
            except Exception as e:
                print(f"   ❌ Attempt {attempt + 1} failed: {e}")
                continue
        
        # If we get here, all attempts failed
        return {
            "success": False,
            "error": f"Failed to generate unique content after {max_attempts} attempts",
            "attempts": max_attempts
        }
    
    def _fallback_optimize_prompt(self, prompt: str) -> str:
        """
        Fallback optimization when AI is not available.
        Uses simple text processing to shorten the prompt.
        
        Args:
            prompt: Original video prompt
            
        Returns:
            Optimized prompt that fits 12-second criteria
        """
        try:
            # Handle different prompt formats
            if "Expert says:" in prompt:
                # Extract the quoted content
                start = prompt.find("'") + 1
                end = prompt.rfind("'")
                if start > 0 and end > start:
                    content = prompt[start:end]
                    
                    # Split into sentences and take the most important parts
                    sentences = content.split('. ')
                    if len(sentences) >= 2:
                        # Take first sentence (hook) and shorten second sentence (tip)
                        hook = sentences[0].strip()
                        tip = sentences[1].strip()
                        
                        # Shorten tip if too long - MUCH MORE AGGRESSIVE for 12-second videos
                        if len(tip) > 30:
                            words = tip.split()
                            tip = ' '.join(words[:4])  # Take first 4 words only
                        
                        optimized = f"Expert says: '{hook}. {tip}.'"
                        
                        # Ensure it's within STRICT 80 character limit for 12-second videos
                        if len(optimized) <= 80:
                            return optimized
                        else:
                            # Much more aggressive shortening for 12-second videos
                            hook_words = hook.split()[:3]  # First 3 words of hook
                            tip_words = tip.split()[:3]    # First 3 words of tip
                            return f"Expert says: '{' '.join(hook_words)}. {' '.join(tip_words)}.'"
                    else:
                        # Single sentence - MUCH MORE AGGRESSIVE truncation for 12-second videos
                        words = content.split()
                        if len(words) > 8:  # Much shorter
                            return f"Expert says: '{' '.join(words[:8])}...'"
                        else:
                            return f"Expert says: '{content}'"
                else:
                    # No quotes found, MUCH MORE AGGRESSIVE truncation for 12-second videos
                    if len(prompt) > 80:
                        return prompt[:77] + "..."
                    else:
                        return prompt
            elif "'hook':" in prompt and "'main_tip':" in prompt:
                # Handle dictionary format with hook and main_tip
                try:
                    import re
                    hook_match = re.search(r"'hook':\s*'([^']+)'", prompt)
                    tip_match = re.search(r"'main_tip':\s*'([^']+)'", prompt)
                    
                    if hook_match and tip_match:
                        hook = hook_match.group(1)
                        tip = tip_match.group(1)
                        
                        # Shorten tip if too long - MUCH MORE AGGRESSIVE for 12-second videos
                        if len(tip) > 30:
                            words = tip.split()
                            tip = ' '.join(words[:4])  # Take first 4 words only
                        
                        optimized = f"Expert says: '{hook} {tip}'"
                        
                        # Ensure it's within STRICT 80 character limit for 12-second videos
                        if len(optimized) <= 80:
                            return optimized
                        else:
                            # Much more aggressive shortening for 12-second videos
                            hook_words = hook.split()[:3]  # First 3 words of hook
                            tip_words = tip.split()[:3]    # First 3 words of tip
                            return f"Expert says: '{' '.join(hook_words)} {' '.join(tip_words)}'"
                    else:
                        # Fallback to MUCH MORE AGGRESSIVE truncation for 12-second videos
                        if len(prompt) > 80:
                            return prompt[:77] + "..."
                        else:
                            return prompt
                except:
                    # Fallback to MUCH MORE AGGRESSIVE truncation for 12-second videos
                    if len(prompt) > 80:
                        return prompt[:77] + "..."
                    else:
                        return prompt
            else:
                # No recognized format, MUCH MORE AGGRESSIVE truncation for 12-second videos
                if len(prompt) > 80:
                    return prompt[:77] + "..."
                else:
                    return prompt
                    
        except Exception as e:
            print(f"   ⚠️ Fallback optimization failed: {e}")
            # Last resort - MUCH MORE AGGRESSIVE truncation for 12-second videos
            return prompt[:80] + "..." if len(prompt) > 80 else prompt
    
    def _infer_goal_phrase(self, blog_post: dict) -> str:
        """Infer a short goal phrase like 'to boost energy' or 'to sleep better'."""
        try:
            text = (str(blog_post) or '').lower()
            if 'energy' in text:
                return 'to boost energy'
            if 'sleep' in text:
                return 'to sleep better'
            if 'focus' in text or 'concentrat' in text:
                return 'to improve focus'
            if 'hydration' in text or 'water' in text:
                return 'to stay hydrated'
            return 'for better health'
        except Exception:
            return 'for better health'
    
    def _compose_speech_from_remedy(self, remedy_content: str, max_words: int = 12, lead_in: str = '') -> str:
        """Compose a concise, natural one-sentence speech from remedy content.
        Adds an optional lead-in (e.g., 'For a quick energy boost,').
        Generates a human-sounding cadence with brief connectors.
        """
        text = (remedy_content or '').strip()
        if not text:
            return ''
        import re, random
        # Normalize
        t = re.sub(r"\s+", " ", text)
        # Common cleanup
        t = re.sub(r"(?i)green tea brewing:\s*", "", t)
        t = re.sub(r"(?i)natural remedy preparation and usage demonstration", "", t)
        t = re.sub(r"(?i)how to (make|use|avoid):\s*", "", t)
        t = t.replace("and enjoy", "").replace("enjoy", "")
        # Split into clauses by comma/period
        parts = re.split(r"[\.,;]\s*", t)
        raw_actions = []
        verbs = {
            'boil': 'boil', 'add': 'add', 'steep': 'steep', 'strain': 'strain', 'mix': 'mix',
            'blend': 'blend', 'pour': 'pour', 'squeeze': 'squeeze', 'stir': 'stir', 'drink': 'drink',
            'sip': 'sip', 'use': 'use', 'avoid': 'avoid'
        }
        for p in parts:
            pl = p.strip()
            if not pl:
                continue
            lower = pl.lower()
            if any(v in lower for v in verbs) or len(pl.split()) <= 6:
                raw_actions.append(pl)
            if len(raw_actions) >= 3:
                break
        if not raw_actions:
            raw_actions = [t]
        # Clean and humanize actions
        actions = []
        for a in raw_actions[:3]:
            a = a.strip().rstrip('.')
            # soften steep phrasing
            a = re.sub(r"(?i)\bsteep(\b|\s)", "let it steep ", a)
            # small tidy-ups
            a = a.replace("  ", " ")
            actions.append(a.lower())
        # Choose a natural lead-in
        default_leads = [
            "Quick tip:",
            "Try this:",
            "Simple steps:",
            "Here’s how:",
        ]
        lead_text = lead_in.strip().rstrip(',') if lead_in else random.choice(default_leads)
        # Build with light connectors
        if len(actions) == 1:
            core = actions[0]
        elif len(actions) == 2:
            core = f"{actions[0]}, then {actions[1]}"
        else:
            core = f"{actions[0]}, then {actions[1]}, and {actions[2]}"
        # Add a softener to first action
        core = re.sub(r"^(boil|add|blend|mix|pour|squeeze|stir|drink|sip|use|avoid)", r"just \1", core)
        sentence = f"{lead_text} {core}.".strip()
        # Cap word count
        words = sentence.split()
        if len(words) > max_words:
            sentence = ' '.join(words[:max_words]).rstrip(',;:.') + '.'
        # Capitalize nicely
        if sentence and not sentence[0].isupper():
            sentence = sentence[0].upper() + sentence[1:]
        return sentence
    
    def run(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        publish_immediately: bool = True,
        test_mode: bool = False,
        no_sheets: bool = False
    ) -> Dict:
        """
        Run complete content generation pipeline.
        
        Args:
            topic: Specific topic (optional, auto-generated if None)
            category: Health category filter
            publish_immediately: Publish post immediately (True) or save as draft (False)
            
        Returns:
            Dict with results
        """
        
        print("\n" + "="*70)
        print("🚀 AUTOMATED CONTENT PIPELINE")
        print("="*70)
        print(f"Topic: {topic or 'Auto-generated'}")
        print(f"Category: {category or 'Any'}")
        print(f"Publish: {'Immediately' if publish_immediately else 'As Draft'}")
        print("="*70 + "\n")
        
        # Step 1: Generate content package with diversity optimization
        print("Step 1: Generating diverse content with OpenAI...")
        content_result = self._generate_content_with_fallbacks(
            original_topic=topic,
            original_category=category,
            max_attempts=5
        )
        
        if not content_result['success']:
            return {
                "success": False,
                "error": f"Content generation failed after {content_result.get('attempts', 5)} attempts: {content_result['error']}"
            }
        
        content_data = content_result['data']
        attempt_info = f" (Attempt {content_result['attempt']}, Topic: {content_result['topic_used']}, Category: {content_result['category_used']})"
        
        # Validate content_data structure
        if not content_data:
            return {
                "success": False,
                "error": "No content data received from generator"
            }
        
        # Check for required fields
        if 'blog_post' not in content_data:
            return {
                "success": False,
                "error": "Missing blog_post in content data"
            }
        
        blog_post = content_data.get('blog_post', {})
        if 'category' not in blog_post:
            return {
                "success": False,
                "error": "Missing category in blog_post data"
            }
        
        # Debug: Print content structure
        print(f"\n📋 Content Data Structure:")
        print(f"   Keys: {list(content_data.keys())}")
        if 'blog_post' in content_data:
            print(f"   Blog post keys: {list(content_data['blog_post'].keys())}")
            print(f"   Blog post content: {content_data['blog_post']}")
        if 'video_prompt' in content_data:
            print(f"   Video prompt keys: {list(content_data['video_prompt'].keys())}")
            print(f"   Video prompt content: {content_data['video_prompt']}")
        if 'diversity_metadata' in content_data:
            print(f"   Diversity metadata: {content_data['diversity_metadata']}")
        
        # Step 1.5: Content validation (similarity already checked in fallback method)
        print("\nStep 1.5: Content validation...")
        blog_post = content_data.get('blog_post', {})
        title = blog_post.get('title', '')
        category = blog_post.get('category', 'Unknown')
        
        print(f"   Title: {title}")
        print(f"   Category: {category}")
        print(f"   ✅ Content is unique and diverse{attempt_info}")
        
        # Validate video prompt (skip if method doesn't exist)
        video_prompt_data = content_data.get('video_prompt', {})
        try:
            if hasattr(self.content_generator, 'validate_video_prompt'):
                if not self.content_generator.validate_video_prompt(video_prompt_data):
                    return {
                        "success": False,
                        "error": "Video prompt validation failed"
                    }
            else:
                print("   Video prompt validation skipped (method not available)")
        except Exception as e:
            print(f"   Video prompt validation failed: {e}")
            print("   Continuing without validation...")
        
        print(f"✅ Content generated: {content_data['blog_post']['title']}")
        print(f"   Category: {content_data['blog_post']['category']}")
        print(f"   Diversity Score: N/A (checked in fallback method)")
        
        # Debug: Print video prompt details
        print(f"   Video prompt length: {len(video_prompt) if 'video_prompt' in locals() else 'N/A'}")
        if 'video_prompt' in locals():
            print(f"   Video prompt preview: {video_prompt[:100]}...")
        
        # Step 2: Content validation complete (duplicates already checked in fallback method)
        print("\nStep 2: Content validation complete...")
        print("✅ No duplicates found (verified in fallback method)")
        
        # Step 3: Generate video with Sora (or skip in test mode)
        if test_mode:
            print("\nStep 3: Testing video prompt processing (NO Sora API call)...")
            # Test video prompt processing without expensive API call
            video_prompt_data = content_data.get('video_prompt', {})
            video_prompt_raw = video_prompt_data.get('content') or video_prompt_data.get('prompt') or video_prompt_data.get('script') or video_prompt_data.get('speech') or video_prompt_data
            
            # Extract remedy content from blog post for better video prompts
            remedy_content = self._extract_remedy_content(content_data.get('blog_post', {}))
            if remedy_content:
                print(f"   📋 Extracted remedy content: {remedy_content}")
            
            if video_prompt_raw:
                # Test prompt conversion using the same logic as production
                # Create the final Sora prompt with remedy content
                # Prefer composing speech from remedy content to ensure descriptive guidance
                goal = self._infer_goal_phrase(content_data.get('blog_post', {}))
                composed_from_remedy = self._compose_speech_from_remedy(remedy_content, max_words=14, lead_in=f"To {goal.split('to')[-1].strip()}")
                speech_text = composed_from_remedy or self._extract_speech_text(video_prompt_raw) or "Try this natural remedy for better health"
                speech_text = self._constrain_speech_length(speech_text, max_words=14)
                
                # Optimize ONLY the spoken line to ensure it fits 8-10 seconds
                optimized_speech = speech_text
                try:
                    if len(speech_text) > 80:
                        print("   🤖 Optimizing speech line to fit 8-10 seconds...")
                        maybe_optimized = self._optimize_video_prompt(speech_text)
                        if maybe_optimized and len(maybe_optimized) <= 80:
                            optimized_speech = maybe_optimized
                            print(f"   ✅ Speech optimized: {len(optimized_speech)} chars")
                        else:
                            optimized_speech = speech_text[:80].rstrip() + ('' if len(speech_text) <= 80 else '...')
                            print("   ⚠️ Using truncated speech line (≤80 chars)")
                except Exception as e:
                    print(f"   ⚠️ Speech optimization failed: {e}")
                
                # Create the final Sora prompt with remedy content
                video_prompt = (
                    f"A white blonde doctor in her 30s appears in the bottom left corner of the screen. "
                    f"Deliver a natural, human-sounding tip describing the remedy steps conversationally (no exact script provided). "
                    f"Keep it concise and clear; speak at a faster pace; let the model choose wording and pacing. "
                    f"End the video immediately when the main remedy/tip is completed - no supporting sentences or prolonging. "
                    f"Begin speaking after a 0.5-second silence and finish by ~11 seconds to avoid cutoff. "
                    f"The background shows a full-screen demonstration of {remedy_content}. "
                    f"No person should be visible in the background, only the remedy preparation process."
                )
                
                # Show the exact prompt that would be sent to Sora for validation
                print(f"\n🎬 TEST MODE SORA PROMPT VALIDATION:")
                print(f"   📝 Prompt Length: {len(video_prompt)} characters")
                print(f"   📋 Full Prompt: {video_prompt}")
                print(f"   🎯 Speech: delegated to Sora (natural delivery, concise)")
                print(f"   🔧 Remedy Content: {remedy_content}")
                
                # Remove strict length checks on full prompt; it's descriptive by design
                
                print("✅ Video prompt processing test completed (NO API call made)")
            else:
                print("❌ No video prompt found in content data")
                return {
                    "success": False,
                    "error": "No video prompt found in content data"
                }
            
            # Skip video generation, S3 upload, and blog post creation in test mode
            print("\n🧪 TEST MODE: Skipping video generation, S3 upload, and blog post creation")
            print("✅ Content generation and video prompt processing test completed!")
            
            return {
                "success": True,
                "test_mode": True,
                "content_data": content_data,
                "video_prompt": video_prompt if 'video_prompt' in locals() else None,
                "message": "Test completed successfully - no expensive API calls made"
            }
        
        # Regular mode: Generate video with Sora
        print("\nStep 3: Generating video with Sora...")
        video_prompt_raw = video_prompt_data.get('content') or video_prompt_data.get('prompt') or video_prompt_data.get('script') or video_prompt_data.get('speech') or video_prompt_data
        
        # Extract remedy content from blog post for better video prompts
        remedy_content = self._extract_remedy_content(content_data.get('blog_post', {}))
        if remedy_content:
            print(f"   📋 Extracted remedy content: {remedy_content}")
        
        if not video_prompt_raw:
            return {
                "success": False,
                "error": "No video prompt found in content data"
            }
        
        # Create proper natural language prompt for Sora using remedy content
        # Create the final Sora prompt with remedy content
        # Prefer composing speech from remedy content to ensure descriptive guidance
        goal = self._infer_goal_phrase(content_data.get('blog_post', {}))
        composed_from_remedy = self._compose_speech_from_remedy(remedy_content, max_words=14, lead_in=f"To {goal.split('to')[-1].strip()}")
        speech_text = composed_from_remedy or self._extract_speech_text(video_prompt_raw) or "Try this natural remedy for better health"
        speech_text = self._constrain_speech_length(speech_text, max_words=14)
        
        # Optimize ONLY the spoken line to ensure it fits 8-10 seconds
        optimized_speech = speech_text
        try:
            if len(speech_text) > 80:
                print("   🤖 Optimizing speech line to fit 8-10 seconds...")
                maybe_optimized = self._optimize_video_prompt(speech_text)
                if maybe_optimized and len(maybe_optimized) <= 80:
                    optimized_speech = maybe_optimized
                    print(f"   ✅ Speech optimized: {len(optimized_speech)} chars")
                else:
                    # Aggressive truncate if needed
                    optimized_speech = speech_text[:80].rstrip() + ('' if len(speech_text) <= 80 else '...')
                    print("   ⚠️ Using truncated speech line (≤80 chars)")
        except Exception as e:
            print(f"   ⚠️ Speech optimization failed: {e}")
        
        # Create the final Sora prompt with remedy content
        video_prompt = (
            f"A white blonde doctor in her 30s appears in the bottom left corner of the screen. "
            f"Deliver a natural, human-sounding tip describing the remedy steps conversationally (no exact script provided). "
            f"Keep it concise and clear; speak at a faster pace; let the model choose wording and pacing. "
            f"End the video immediately when the main remedy/tip is completed - no supporting sentences or prolonging. "
            f"Begin speaking after a 0.5-second silence and finish by ~11 seconds to avoid cutoff. "
            f"The background shows a full-screen demonstration of {remedy_content}. "
            f"No person should be visible in the background, only the remedy preparation process."
        )
        
        # Show the exact prompt being sent to Sora for validation
        print(f"\n🎬 FINAL SORA PROMPT VALIDATION:")
        print(f"   📝 Prompt Length: {len(video_prompt)} characters")
        print(f"   📋 Full Prompt: {video_prompt}")
        print(f"   🎯 Speech: delegated to Sora (natural delivery, concise)")
        print(f"   🔧 Remedy Content: {remedy_content}")
        
        # Use .env settings for video generation (not content generator duration)
        video_result = self.video_generator.generate_video(
            prompt=video_prompt
            # duration, quality, aspect_ratio will be loaded from .env settings
        )
        
        if video_result.get('error'):
            return {
                "success": False,
                "error": f"Video generation failed: {video_result['error']}"
            }
        
        video_id = video_result.get('video_id')
        print(f"✅ Video generation started: {video_id}")
        
        # Step 4: Wait for video completion
        print("\nStep 4: Waiting for video completion...")
        status = self.video_generator.wait_for_completion(video_id, max_wait_time=600)
        
        if status.get('status') != 'completed':
            return {
                "success": False,
                "error": f"Video generation failed or timed out: {status.get('status')}"
            }
        
        print("✅ Video completed")
        
        # Step 5: Download and upload to S3
        print("\nStep 5: Downloading and uploading to S3...")
        
        # Prepare video metadata with SEO title
        from django.conf import settings
        video_metadata = {
            'video_id': video_id,
            'prompt': video_prompt,
            'duration': getattr(settings, 'SORA_DEFAULT_DURATION', 4),  # Use .env setting
            'seo_title': content_data['blog_post']['title']  # Add SEO title
        }
        
        video_path = self.video_generator.download_video(
            video_id,
            upload_to_s3=True,
            delete_local_after_s3=True,
            video_metadata=video_metadata,
            add_to_sheets=not no_sheets
        )
        
        if not video_path:
            return {
                "success": False,
                "error": "Failed to download/upload video"
            }
        
        # Extract S3 URL
        if video_path.startswith('http'):
            video_url = video_path
            print(f"✅ Video uploaded to S3: {video_url}")
        else:
            # If local path returned, construct S3 URL (shouldn't happen with delete_local=True)
            video_url = None
            print(f"⚠️ Video saved locally: {video_path}")
        
        # Step 6: Create blog post
        print("\nStep 6: Creating blog post...")
        post_result = create_blog_post_from_content(
            content_data=content_data,
            author=self.author,
            video_url=video_url,
            status='published' if publish_immediately else 'draft'
        )
        
        if not post_result['success']:
            return {
                "success": False,
                "error": f"Blog post creation failed: {post_result['error']}",
                "video_url": video_url  # Video was created, just post failed
            }
        
        post = post_result['post']
        
        # Step 7: Track generated content for diversity analysis
        print("\nStep 7: Tracking content for diversity analysis...")
        try:
            tracked_content = self.content_generator.track_generated_content(
                content_data=content_data,
                video_id=video_id,
                video_url=video_url
            )
            print(f"✅ Content tracked: {tracked_content.title}")
        except Exception as e:
            print(f"⚠️ Content tracking failed: {e}")
            print("   Continuing without content tracking...")
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 DIVERSE CONTENT PIPELINE COMPLETED!")
        print("="*70)
        print(f"Blog Post: {post.title}")
        print(f"   URL: {post.get_absolute_url()}")
        print(f"   Category: {post.category.name}")
        print(f"   Status: {post.status}")
        if video_url:
            print(f"Video URL: {video_url}")
        print(f"Google Sheets: Updated")
        print(f"Diversity: Content tracked for future optimization")
        print("="*70 + "\n")
        
        return {
            "success": True,
            "post": post,
            "video_url": video_url,
            "video_id": video_id,
            "content_data": content_data
        }


def main():
    """Run pipeline from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated health content pipeline")
    parser.add_argument('--topic', help='Specific topic (optional)')
    parser.add_argument('--category', choices=['Nutrition', 'Fitness', 'Mental Health', 'Wellness', 'Sleep'], help='Category filter')
    parser.add_argument('--draft', action='store_true', help='Save as draft instead of publishing')
    
    args = parser.parse_args()
    
    try:
        pipeline = AutoContentPipeline()
        result = pipeline.run(
            topic=args.topic,
            category=args.category,
            publish_immediately=not args.draft
        )
        
        if result['success']:
            print("✅ Success!")
            return 0
        else:
            print(f"❌ Failed: {result['error']}")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

