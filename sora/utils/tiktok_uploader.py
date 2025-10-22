#!/usr/bin/env python3
"""
TikTok Uploader
Automatically upload generated videos to TikTok.
"""

import os
import time
import json
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
import hashlib
import hmac
import base64
from urllib.parse import urlencode


class TikTokUploader:
    """TikTok video uploader using TikTok Research API."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize TikTok uploader with access token."""
        self.access_token = access_token or os.getenv('TIKTOK_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("TikTok access token is required. Set TIKTOK_ACCESS_TOKEN environment variable.")
        
        self.base_url = "https://open-api.tiktok.com"
        self.upload_url = f"{self.base_url}/share/video/upload/"
        self.publish_url = f"{self.base_url}/share/video/publish/"
        
        # Upload settings
        self.max_retries = 3
        self.retry_delay = 5  # seconds
    
    def _make_request(self, url: str, method: str = "POST", data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to TikTok API."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(self.max_retries):
            try:
                if method.upper() == "POST":
                    if files:
                        # Remove Content-Type for file uploads
                        headers.pop("Content-Type", None)
                        response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
                    else:
                        response = requests.post(url, headers=headers, json=data, timeout=30)
                else:
                    response = requests.get(url, headers=headers, timeout=30)
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to make request after {self.max_retries} attempts: {e}")
    
    def upload_video(
        self,
        video_path: str,
        caption: str = "",
        privacy_level: str = "PUBLIC_TO_EVERYONE",
        allow_duet: bool = True,
        allow_comment: bool = True,
        allow_stitch: bool = True,
        video_cover_timestamp_ms: int = 1000,
        brand_content_toggle: bool = False,
        brand_organic_toggle: bool = False
    ) -> Dict[str, Any]:
        """
        Upload video to TikTok.
        
        Args:
            video_path: Path to the video file
            caption: Video caption/description
            privacy_level: Privacy setting (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIEND, SELF_ONLY)
            allow_duet: Allow duets
            allow_comment: Allow comments
            allow_stitch: Allow stitches
            video_cover_timestamp_ms: Timestamp for video cover (in milliseconds)
            brand_content_toggle: Brand content toggle
            brand_organic_toggle: Brand organic toggle
            
        Returns:
            Dictionary containing upload result
        """
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            print(f"Uploading video: {video_file.name}")
            print(f"Caption: {caption[:50]}..." if len(caption) > 50 else f"Caption: {caption}")
            
            # Step 1: Initialize upload
            init_data = {
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_file.stat().st_size,
                    "chunk_size": 10000000,  # 10MB chunks
                    "total_chunk_count": 1
                }
            }
            
            print("Initializing upload...")
            init_response = self._make_request(self.upload_url, data=init_data)
            
            if init_response.get("error"):
                raise Exception(f"Upload initialization failed: {init_response['error']}")
            
            upload_url = init_response["data"]["upload_url"]
            upload_session_id = init_response["data"]["upload_session_id"]
            
            # Step 2: Upload video file
            print("Uploading video file...")
            with open(video_file, 'rb') as f:
                files = {"video": (video_file.name, f, "video/mp4")}
                upload_data = {
                    "upload_session_id": upload_session_id,
                    "chunk_index": 0
                }
                
                upload_response = requests.post(
                    upload_url,
                    data=upload_data,
                    files=files,
                    timeout=300  # 5 minutes for large files
                )
                upload_response.raise_for_status()
            
            # Step 3: Publish video
            print("Publishing video...")
            publish_data = {
                "post_info": {
                    "title": caption,
                    "privacy_level": privacy_level,
                    "disable_duet": not allow_duet,
                    "disable_comment": not allow_comment,
                    "disable_stitch": not allow_stitch,
                    "video_cover_timestamp_ms": video_cover_timestamp_ms,
                    "brand_content_toggle": brand_content_toggle,
                    "brand_organic_toggle": brand_organic_toggle
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "video_size": video_file.stat().st_size,
                    "chunk_size": 10000000,
                    "total_chunk_count": 1
                },
                "upload_session_id": upload_session_id
            }
            
            publish_response = self._make_request(self.publish_url, data=publish_data)
            
            if publish_response.get("error"):
                raise Exception(f"Video publishing failed: {publish_response['error']}")
            
            result = {
                "success": True,
                "video_id": publish_response["data"].get("id"),
                "share_url": publish_response["data"].get("share_url"),
                "upload_session_id": upload_session_id,
                "caption": caption,
                "privacy_level": privacy_level,
                "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            print("✅ Video uploaded successfully to TikTok!")
            print(f"Video ID: {result['video_id']}")
            print(f"Share URL: {result['share_url']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error uploading to TikTok: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "video_path": video_path
            }
    
    def get_upload_status(self, upload_session_id: str) -> Dict[str, Any]:
        """Get the status of an upload."""
        try:
            status_url = f"{self.base_url}/share/video/status/"
            data = {"upload_session_id": upload_session_id}
            
            response = self._make_request(status_url, data=data)
            return response
            
        except Exception as e:
            return {
                "error": f"Error checking upload status: {str(e)}",
                "upload_session_id": upload_session_id
            }
    
    def delete_video(self, video_id: str) -> Dict[str, Any]:
        """Delete a video from TikTok."""
        try:
            delete_url = f"{self.base_url}/share/video/delete/"
            data = {"video_id": video_id}
            
            response = self._make_request(delete_url, data=data)
            
            if response.get("error"):
                return {
                    "success": False,
                    "error": response["error"]
                }
            
            return {
                "success": True,
                "video_id": video_id,
                "deleted_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error deleting video: {str(e)}",
                "video_id": video_id
            }
    
    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get information about a video."""
        try:
            info_url = f"{self.base_url}/share/video/info/"
            data = {"video_id": video_id}
            
            response = self._make_request(info_url, data=data)
            return response
            
        except Exception as e:
            return {
                "error": f"Error getting video info: {str(e)}",
                "video_id": video_id
            }


class TikTokConfig:
    """Configuration for TikTok uploader."""
    
    def __init__(self):
        """Initialize TikTok configuration."""
        self.config_file = Path("tiktok_config.json")
        self.settings = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load TikTok configuration."""
        default_settings = {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "allow_duet": True,
            "allow_comment": True,
            "allow_stitch": True,
            "video_cover_timestamp_ms": 1000,
            "brand_content_toggle": False,
            "brand_organic_toggle": False,
            "auto_upload": False,
            "default_caption_template": "AI Generated Video: {prompt}",
            "hashtags": ["#AI", "#Generated", "#Sora2"]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    default_settings.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load TikTok config: {e}")
        
        return default_settings
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save TikTok config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.settings[key] = value
    
    def generate_caption(self, prompt: str, custom_caption: str = "") -> str:
        """Generate caption for video."""
        if custom_caption:
            return custom_caption
        
        template = self.get("default_caption_template", "AI Generated Video: {prompt}")
        caption = template.format(prompt=prompt)
        
        hashtags = self.get("hashtags", [])
        if hashtags:
            caption += " " + " ".join(hashtags)
        
        return caption


def main():
    """Test TikTok uploader."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload video to TikTok")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--caption", help="Video caption")
    parser.add_argument("--privacy", choices=["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIEND", "SELF_ONLY"], 
                       default="PUBLIC_TO_EVERYONE", help="Privacy level")
    parser.add_argument("--no-duet", action="store_true", help="Disable duets")
    parser.add_argument("--no-comment", action="store_true", help="Disable comments")
    parser.add_argument("--no-stitch", action="store_true", help="Disable stitches")
    
    args = parser.parse_args()
    
    try:
        uploader = TikTokUploader()
        config = TikTokConfig()
        
        caption = args.caption or config.generate_caption("AI Generated Video")
        
        result = uploader.upload_video(
            video_path=args.video_path,
            caption=caption,
            privacy_level=args.privacy,
            allow_duet=not args.no_duet,
            allow_comment=not args.no_comment,
            allow_stitch=not args.no_stitch
        )
        
        if result.get("success"):
            print("✅ Upload successful!")
            print(f"Video ID: {result['video_id']}")
            print(f"Share URL: {result['share_url']}")
        else:
            print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
