#!/usr/bin/env python3
"""
Sora 2 Video Generator
A Python script to generate AI videos using OpenAI's Sora 2 model.
"""

import os
import json
import time
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI library not found. Please install it with: pip install openai")
    exit(1)

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file automatically
except ImportError:
    # Fallback to manual .env loading if python-dotenv is not available
    def load_env_file():
        """Load environment variables from .env file."""
        env_file = Path('.env')
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
            except Exception as e:
                print(f"Warning: Could not load .env file: {e}")
    
    load_env_file()

# Import TikTok uploader if available
try:
    from tiktok_uploader import TikTokUploader, TikTokConfig
    TIKTOK_AVAILABLE = True
except ImportError:
    TIKTOK_AVAILABLE = False


class SoraVideoGenerator:
    """Main class for generating videos with Sora 2."""
    
    def __init__(self, api_key: Optional[str] = None, tiktok_token: Optional[str] = None):
        """Initialize the video generator with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it directly.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.output_dir = Path("generated_videos")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize TikTok uploader if available
        self.tiktok_uploader = None
        self.tiktok_config = None
        if TIKTOK_AVAILABLE:
            try:
                tiktok_token = tiktok_token or os.getenv('TIKTOK_ACCESS_TOKEN')
                if tiktok_token:
                    self.tiktok_uploader = TikTokUploader(tiktok_token)
                    self.tiktok_config = TikTokConfig()
                    print("✅ TikTok uploader initialized")
                else:
                    print("⚠️ TikTok uploader not available - TIKTOK_ACCESS_TOKEN not set")
            except Exception as e:
                print(f"⚠️ TikTok uploader initialization failed: {e}")
                self.tiktok_uploader = None
    
    def generate_video(
        self,
        prompt: str,
        duration: int = 4,
        quality: str = "standard",
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
        save_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a video using Sora 2.
        
        Args:
            prompt: Text description of the video to generate
            duration: Video duration in seconds (4, 8, or 12)
            quality: Video quality ("standard" or "hd")
            aspect_ratio: Video aspect ratio ("16:9", "9:16", "1:1")
            style: Optional style description
            save_metadata: Whether to save generation metadata
            
        Returns:
            Dictionary containing video ID and metadata
        """
        try:
            # Validate duration (Sora 2 only supports 4, 8, 12 seconds)
            valid_durations = [4, 8, 12]
            if duration not in valid_durations:
                # Find closest valid duration
                closest_duration = min(valid_durations, key=lambda x: abs(x - duration))
                print(f"Warning: Duration {duration}s not supported. Using {closest_duration}s instead.")
                duration = closest_duration
            
            # Map aspect ratio to size format
            size_map = {
                "16:9": "1280x720",
                "9:16": "720x1280", 
                "1:1": "1024x1024"
            }
            size = size_map.get(aspect_ratio, "1280x720")
            
            # Prepare the generation request
            generation_params = {
                "model": "sora-2",
                "prompt": prompt,
                "seconds": str(duration),
                "size": size
            }
            
            if style:
                generation_params["style"] = style
            
            print(f"Generating video with prompt: '{prompt}'")
            print(f"Parameters: {generation_params}")
            
            # Make the API call using the correct Sora 2 API
            video = self.client.videos.create(**generation_params)
            
            # Extract video information
            video_data = {
                "video_id": video.id,
                "object": video.object,
                "model": video.model,
                "status": video.status,
                "progress": getattr(video, "progress", 0),
                "created_at": video.created_at,
                "size": video.size,
                "seconds": video.seconds,
                "prompt": prompt,
                "parameters": generation_params,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save metadata if requested
            if save_metadata:
                self._save_metadata(video_data)
            
            print(f"✅ Video generation started!")
            print(f"Video ID: {video_data['video_id']}")
            print(f"Status: {video_data['status']}")
            
            return video_data
            
        except Exception as e:
            error_msg = f"Error generating video: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "error": error_msg,
                "status": "failed",
                "prompt": prompt
            }
    
    def _save_metadata(self, video_data: Dict[str, Any]) -> None:
        """Save video generation metadata to a JSON file."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        metadata_file = self.output_dir / f"video_metadata_{timestamp}.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(video_data, f, indent=2)
        
        print(f"Metadata saved to: {metadata_file}")
    
    def list_generated_videos(self) -> list:
        """List all generated videos and their metadata."""
        metadata_files = list(self.output_dir.glob("video_metadata_*.json"))
        videos = []
        
        for file_path in metadata_files:
            try:
                with open(file_path, 'r') as f:
                    video_data = json.load(f)
                    videos.append(video_data)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
        
        return sorted(videos, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get the status of a video generation job."""
        try:
            video = self.client.videos.retrieve(video_id)
            
            return {
                "video_id": video.id,
                "object": video.object,
                "model": video.model,
                "status": video.status,
                "progress": getattr(video, "progress", 0),
                "created_at": video.created_at,
                "size": getattr(video, "size", None),
                "seconds": getattr(video, "seconds", None),
                "completed_at": getattr(video, "completed_at", None),
                "expires_at": getattr(video, "expires_at", None),
                "error": getattr(video, "error", None)
            }
            
        except Exception as e:
            return {
                "error": f"Error retrieving video status: {str(e)}",
                "video_id": video_id
            }
    
    def wait_for_completion(self, video_id: str, max_wait_time: int = 300, check_interval: int = 10) -> Dict[str, Any]:
        """Wait for video generation to complete."""
        print(f"Waiting for video {video_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_video_status(video_id)
            
            if status.get("error"):
                return status
            
            current_status = status.get("status", "unknown")
            progress = status.get("progress", 0)
            
            print(f"Status: {current_status}, Progress: {progress}%")
            
            if current_status == "completed":
                print("✅ Video generation completed!")
                return status
            elif current_status == "failed":
                print("❌ Video generation failed!")
                return status
            
            time.sleep(check_interval)
        
        print(f"⏰ Timeout waiting for video completion after {max_wait_time} seconds")
        return self.get_video_status(video_id)
    
    def download_video(self, video_id: str, filename: Optional[str] = None, variant: str = "video") -> str:
        """Download video content from OpenAI."""
        try:
            if not filename:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                extension = "mp4" if variant == "video" else "webp" if variant == "thumbnail" else "jpg"
                filename = f"sora_video_{video_id}_{timestamp}.{extension}"
            
            file_path = self.output_dir / filename
            
            print(f"Downloading {variant} for video {video_id} to: {file_path}")
            
            # Download content using the correct API method
            content = self.client.videos.download_content(video_id, variant=variant)
            
            with open(file_path, 'wb') as f:
                f.write(content.read())
            
            print(f"✅ Video downloaded successfully: {file_path}")
            return str(file_path)
            
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return ""
    
    def upload_to_tiktok(
        self,
        video_path: str,
        caption: Optional[str] = None,
        prompt: Optional[str] = None,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        allow_duet: bool = True,
        allow_comment: bool = True,
        allow_stitch: bool = True
    ) -> Dict[str, Any]:
        """Upload video to TikTok."""
        if not self.tiktok_uploader:
            return {
                "success": False,
                "error": "TikTok uploader not available. Set TIKTOK_ACCESS_TOKEN environment variable."
            }
        
        try:
            # Generate caption if not provided
            if not caption and self.tiktok_config:
                caption = self.tiktok_config.generate_caption(prompt or "AI Generated Video")
            
            print(f"Uploading to TikTok: {Path(video_path).name}")
            
            result = self.tiktok_uploader.upload_video(
                video_path=video_path,
                caption=caption,
                privacy_level=privacy_level,
                allow_duet=allow_duet,
                allow_comment=allow_comment,
                allow_stitch=allow_stitch
            )
            
            if result.get("success"):
                print("✅ Video uploaded to TikTok successfully!")
                print(f"TikTok Video ID: {result['video_id']}")
                print(f"Share URL: {result['share_url']}")
            else:
                print(f"❌ TikTok upload failed: {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error uploading to TikTok: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "video_path": video_path
            }
    
    def generate_and_upload_to_tiktok(
        self,
        prompt: str,
        duration: int = 4,
        quality: str = "standard",
        aspect_ratio: str = "16:9",
        style: Optional[str] = None,
        tiktok_caption: Optional[str] = None,
        wait_for_completion: bool = True,
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        allow_duet: bool = True,
        allow_comment: bool = True,
        allow_stitch: bool = True
    ) -> Dict[str, Any]:
        """Generate video and automatically upload to TikTok."""
        # Generate video
        result = self.generate_video(
            prompt=prompt,
            duration=duration,
            quality=quality,
            aspect_ratio=aspect_ratio,
            style=style
        )
        
        if result.get('error'):
            return result
        
        video_id = result.get('video_id')
        if not video_id:
            return {
                "error": "No video ID returned",
                "status": "failed"
            }
        
        print(f"✅ Video generation started! Video ID: {video_id}")
        
        # Wait for completion if requested
        if wait_for_completion:
            print("Waiting for video completion...")
            final_status = self.wait_for_completion(video_id)
            
            if final_status.get('status') != 'completed':
                return {
                    "error": f"Video generation failed: {final_status.get('status', 'unknown')}",
                    "status": "failed",
                    "video_id": video_id
                }
            
            print("✅ Video generation completed!")
            
            # Download video
            video_path = self.download_video(video_id)
            if not video_path:
                return {
                    "error": "Failed to download video",
                    "status": "failed",
                    "video_id": video_id
                }
            
            # Upload to TikTok
            tiktok_result = self.upload_to_tiktok(
                video_path=video_path,
                caption=tiktok_caption,
                prompt=prompt,
                privacy_level=privacy_level,
                allow_duet=allow_duet,
                allow_comment=allow_comment,
                allow_stitch=allow_stitch
            )
            
            # Combine results
            combined_result = {
                "sora_video_id": video_id,
                "video_path": video_path,
                "tiktok_upload": tiktok_result
            }
            
            if tiktok_result.get("success"):
                combined_result["status"] = "completed"
                combined_result["tiktok_video_id"] = tiktok_result.get("video_id")
                combined_result["tiktok_share_url"] = tiktok_result.get("share_url")
            else:
                combined_result["status"] = "video_ready_upload_failed"
                combined_result["tiktok_error"] = tiktok_result.get("error")
            
            return combined_result
        
        else:
            # Return without waiting
            return {
                "status": "generating",
                "video_id": video_id,
                "message": "Video is generating. Use wait_for_completion() to wait for completion before uploading to TikTok."
            }


def main():
    """Main function to run the video generator from command line."""
    parser = argparse.ArgumentParser(description="Generate AI videos using Sora 2")
    parser.add_argument("prompt", help="Text description of the video to generate")
    parser.add_argument("--duration", type=int, default=4, help="Video duration in seconds (4, 8, or 12)")
    parser.add_argument("--quality", choices=["standard", "hd"], default="standard", help="Video quality")
    parser.add_argument("--aspect-ratio", choices=["16:9", "9:16", "1:1"], default="16:9", help="Video aspect ratio")
    parser.add_argument("--style", help="Optional style description")
    parser.add_argument("--download", action="store_true", help="Download the generated video")
    parser.add_argument("--wait", action="store_true", help="Wait for video completion before returning")
    parser.add_argument("--status", help="Check status of a video by ID")
    parser.add_argument("--list", action="store_true", help="List all generated videos")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    
    # TikTok upload options
    parser.add_argument("--upload-tiktok", action="store_true", help="Upload video to TikTok after generation")
    parser.add_argument("--tiktok-caption", help="Custom caption for TikTok upload")
    parser.add_argument("--tiktok-privacy", choices=["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIEND", "SELF_ONLY"], 
                       default="PUBLIC_TO_EVERYONE", help="TikTok privacy level")
    parser.add_argument("--no-tiktok-duet", action="store_true", help="Disable duets on TikTok")
    parser.add_argument("--no-tiktok-comment", action="store_true", help="Disable comments on TikTok")
    parser.add_argument("--no-tiktok-stitch", action="store_true", help="Disable stitches on TikTok")
    parser.add_argument("--tiktok-token", help="TikTok access token (or set TIKTOK_ACCESS_TOKEN env var)")
    
    args = parser.parse_args()
    
    try:
        # Initialize the generator
        generator = SoraVideoGenerator(api_key=args.api_key, tiktok_token=args.tiktok_token)
        
        if args.status:
            # Check status of a specific video
            status = generator.get_video_status(args.status)
            if status.get('error'):
                print(f"❌ Error: {status['error']}")
            else:
                print(f"Video ID: {status['video_id']}")
                print(f"Status: {status['status']}")
                print(f"Progress: {status.get('progress', 0)}%")
                print(f"Created: {status.get('created_at', 'Unknown')}")
                if status.get('completed_at'):
                    print(f"Completed: {status['completed_at']}")
            return
        
        if args.list:
            # List generated videos
            videos = generator.list_generated_videos()
            if videos:
                print(f"\n📹 Generated Videos ({len(videos)} total):")
                for i, video in enumerate(videos, 1):
                    print(f"{i}. {video.get('prompt', 'Unknown')[:50]}...")
                    print(f"   Video ID: {video.get('video_id', 'Unknown')}")
                    print(f"   Status: {video.get('status', 'Unknown')}")
                    print(f"   Created: {video.get('created_at', 'Unknown')}")
                    print()
            else:
                print("No generated videos found.")
            return
        
        # Generate video with TikTok upload if requested
        if args.upload_tiktok:
            if not generator.tiktok_uploader:
                print("❌ TikTok uploader not available. Set TIKTOK_ACCESS_TOKEN environment variable.")
                return 1
            
            print("🎬 Generating video and uploading to TikTok...")
            result = generator.generate_and_upload_to_tiktok(
                prompt=args.prompt,
                duration=args.duration,
                quality=args.quality,
                aspect_ratio=args.aspect_ratio,
                style=args.style,
                tiktok_caption=args.tiktok_caption,
                wait_for_completion=args.wait,
                privacy_level=args.tiktok_privacy,
                allow_duet=not args.no_tiktok_duet,
                allow_comment=not args.no_tiktok_comment,
                allow_stitch=not args.no_tiktok_stitch
            )
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
                return 1
            
            if result.get('status') == 'completed':
                print("✅ Video generated and uploaded to TikTok successfully!")
                print(f"Sora Video ID: {result['sora_video_id']}")
                print(f"TikTok Video ID: {result['tiktok_video_id']}")
                print(f"TikTok Share URL: {result['tiktok_share_url']}")
            elif result.get('status') == 'video_ready_upload_failed':
                print("✅ Video generated but TikTok upload failed!")
                print(f"Sora Video ID: {result['sora_video_id']}")
                print(f"Video Path: {result['video_path']}")
                print(f"TikTok Error: {result['tiktok_error']}")
            else:
                print(f"⏳ Video is generating: {result['message']}")
        else:
            # Regular video generation
            result = generator.generate_video(
                prompt=args.prompt,
                duration=args.duration,
                quality=args.quality,
                aspect_ratio=args.aspect_ratio,
                style=args.style
            )
            
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
                return 1
            
            video_id = result.get('video_id')
            if not video_id:
                print("❌ No video ID returned")
                return 1
            
            print(f"✅ Video generation started! Video ID: {video_id}")
            
            # Wait for completion if requested
            if args.wait:
                print("Waiting for video completion...")
                final_status = generator.wait_for_completion(video_id)
                if final_status.get('status') == 'completed':
                    print("✅ Video generation completed!")
                    if args.download:
                        generator.download_video(video_id)
                else:
                    print(f"❌ Video generation failed or timed out: {final_status.get('status', 'unknown')}")
            elif args.download:
                print("Note: Video is still processing. Use --wait flag to wait for completion before downloading.")
                print(f"Check status with: python sora_video_generator.py --status {video_id}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
