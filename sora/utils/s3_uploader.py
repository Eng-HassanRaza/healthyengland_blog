"""S3 uploader for Sora videos."""

import os
import boto3
from pathlib import Path
from typing import Optional, Dict
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings


class S3VideoUploader:
    """Upload videos to S3 bucket."""
    
    def __init__(self):
        """Initialize S3 client."""
        # Check if AWS credentials are configured
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            raise ValueError(
                "AWS credentials not configured. "
                "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file"
            )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.location = settings.AWS_SORA_LOCATION
        self.region = settings.AWS_S3_REGION_NAME
    
    def upload_video(
        self, 
        local_path: str, 
        s3_key: Optional[str] = None,
        delete_local: bool = False,
        add_to_sheets: bool = True,
        video_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Upload video to S3.
        
        Args:
            local_path: Path to local video file
            s3_key: S3 object key (filename in bucket). If None, uses original filename
            delete_local: Whether to delete local file after successful upload
            
        Returns:
            Dict with success status, S3 URL, and other metadata
        """
        local_file = Path(local_path)
        
        if not local_file.exists():
            return {
                "success": False,
                "error": f"File not found: {local_path}"
            }
        
        # Generate S3 key (path in bucket)
        if not s3_key:
            s3_key = f"{self.location}/{local_file.name}"
        elif not s3_key.startswith(self.location):
            s3_key = f"{self.location}/{s3_key}"
        
        try:
            print(f"⬆️  Uploading {local_file.name} to S3 bucket: {self.bucket_name}")
            
            # Extra arguments for upload
            # Note: ACL removed - use bucket policy for public access instead
            extra_args = {
                'ContentType': 'video/mp4',
                'CacheControl': 'max-age=86400',  # 1 day cache
                'ContentDisposition': 'inline',  # Display in browser, not download
            }
            
            # Upload file with progress
            file_size = local_file.stat().st_size
            print(f"   File size: {file_size / (1024*1024):.2f} MB")
            
            self.s3_client.upload_file(
                str(local_file),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Generate public URL
            s3_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            print(f"✅ Uploaded successfully!")
            print(f"   S3 URL: {s3_url}")
            
            # Delete local file if requested
            if delete_local:
                local_file.unlink()
                print(f"🗑️  Deleted local file: {local_file}")
            
            result = {
                "success": True,
                "s3_url": s3_url,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "size_mb": file_size / (1024*1024),
                "local_path": str(local_file) if not delete_local else None
            }
            
            # Add to Google Sheets if requested
            if add_to_sheets:
                try:
                    from sora.utils.sheets_uploader import add_to_sheets as sheets_add
                    
                    # Extract metadata - use SEO title if available, otherwise filename
                    seo_title = video_metadata.get('seo_title') if video_metadata else None
                    title = seo_title if seo_title else local_file.name
                    prompt = video_metadata.get('prompt') if video_metadata else None
                    duration = video_metadata.get('duration') if video_metadata else None
                    
                    print(f"\n📊 Adding to Google Sheets...")
                    print(f"   Using title: {title}")
                    if seo_title:
                        print(f"   SEO title from blog post: {seo_title}")
                    else:
                        print(f"   Using filename as title: {local_file.name}")
                    
                    sheets_result = sheets_add(
                        video_url=s3_url,
                        title=title,
                        prompt=prompt,
                        duration=duration
                    )
                    
                    if sheets_result['success']:
                        result['sheets_row'] = sheets_result.get('row_number')
                        result['sheet_url'] = sheets_result.get('sheet_url')
                    else:
                        print(f"⚠️ Google Sheets update failed: {sheets_result.get('error')}")
                        result['sheets_error'] = sheets_result.get('error')
                        
                except Exception as e:
                    print(f"⚠️ Could not add to Google Sheets: {e}")
                    result['sheets_error'] = str(e)
            else:
                # Print URL and title instead of adding to sheets
                seo_title = video_metadata.get('seo_title') if video_metadata else None
                title = seo_title if seo_title else local_file.name
                
                print(f"\n📋 Video Information (No Google Sheets):")
                print(f"   S3 URL: {s3_url}")
                print(f"   Title: {title}")
                if seo_title:
                    print(f"   SEO Title: {seo_title}")
                print(f"   File Size: {file_size / (1024*1024):.2f} MB")
            
            return result
            
        except NoCredentialsError:
            error_msg = "AWS credentials not found or invalid"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print(f"❌ S3 upload failed: {error_code} - {error_msg}")
            return {
                "success": False,
                "error": f"{error_code}: {error_msg}"
            }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def delete_video(self, s3_key: str) -> Dict:
        """
        Delete video from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            Dict with success status
        """
        try:
            print(f"🗑️  Deleting {s3_key} from S3...")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            print("✅ Deleted successfully")
            return {"success": True, "s3_key": s3_key}
        except ClientError as e:
            error_msg = f"Delete failed: {e.response['Error']['Message']}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def list_videos(self, prefix: Optional[str] = None, max_keys: int = 100) -> list:
        """
        List videos in S3 bucket.
        
        Args:
            prefix: Prefix to filter videos (default: AWS_SORA_LOCATION)
            max_keys: Maximum number of videos to return
            
        Returns:
            List of video metadata dicts
        """
        try:
            prefix = prefix or self.location
            print(f"📋 Listing videos in s3://{self.bucket_name}/{prefix}")
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            videos = []
            for obj in response.get('Contents', []):
                videos.append({
                    'key': obj['Key'],
                    'filename': obj['Key'].split('/')[-1],
                    'size_mb': obj['Size'] / (1024*1024),
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                })
            
            print(f"✅ Found {len(videos)} video(s)")
            return videos
            
        except ClientError as e:
            print(f"❌ Error listing videos: {e}")
            return []
    
    def get_video_url(self, s3_key: str) -> str:
        """
        Get public URL for a video.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Public URL string
        """
        if not s3_key.startswith(self.location):
            s3_key = f"{self.location}/{s3_key}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"


def upload_to_s3(video_path: str, delete_local: bool = False, add_to_sheets: bool = True) -> Dict:
    """
    Convenience function to upload video to S3.
    
    Args:
        video_path: Path to local video file
        delete_local: Whether to delete local file after upload
        add_to_sheets: Whether to add to Google Sheets
        
    Returns:
        Dict with upload result
    """
    try:
        uploader = S3VideoUploader()
        return uploader.upload_video(
            video_path, 
            delete_local=delete_local,
            add_to_sheets=add_to_sheets
        )
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

