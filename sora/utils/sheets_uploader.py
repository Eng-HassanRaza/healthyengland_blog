"""Google Sheets uploader for Sora video metadata."""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Dict, Optional
from django.conf import settings


class GoogleSheetsUploader:
    """Upload video metadata to Google Sheets."""
    
    def __init__(self):
        """Initialize Google Sheets client."""
        if not settings.GOOGLE_SHEET_ID:
            raise ValueError(
                "Google Sheet ID not configured. "
                "Please set GOOGLE_SHEET_ID in your .env file"
            )
        
        # Define the scope
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Authenticate
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                settings.GOOGLE_CREDENTIALS_FILE,
                scope
            )
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(settings.GOOGLE_SHEET_ID)
            self.worksheet_name = settings.GOOGLE_SHEET_NAME
        except FileNotFoundError:
            raise ValueError(
                f"Google credentials file not found: {settings.GOOGLE_CREDENTIALS_FILE}"
            )
        except Exception as e:
            raise ValueError(f"Failed to authenticate with Google Sheets: {e}")
    
    def add_video(
        self,
        video_url: str,
        title: str,
        prompt: Optional[str] = None,
        duration: Optional[int] = None,
        status: str = "Pending"
    ) -> Dict:
        """
        Add video to Google Sheet.
        
        Args:
            video_url: S3 URL of the video
            title: Video title/filename
            prompt: Original Sora prompt
            duration: Video duration in seconds
            status: Upload status (Pending, Uploaded, Failed)
            
        Returns:
            Dict with success status
        """
        try:
            # Get or create worksheet
            try:
                worksheet = self.sheet.worksheet(self.worksheet_name)
            except gspread.exceptions.WorksheetNotFound:
                # Create worksheet with headers
                worksheet = self.sheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=1000,
                    cols=2
                )
                # Add headers
                headers = ['Video URL', 'Title']
                worksheet.append_row(headers)
                # Format header row
                worksheet.format('A1:B1', {
                    'textFormat': {'bold': True, 'fontSize': 12},
                    'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
                    'horizontalAlignment': 'CENTER'
                })
            
            # Prepare row data (only URL and Title)
            row_data = [
                video_url,
                title
            ]
            
            # Append to sheet
            worksheet.append_row(row_data)
            
            row_number = len(worksheet.get_all_values())
            
            print(f"✅ Added to Google Sheets (Row {row_number})")
            print(f"   Title: {title}")
            print(f"   URL: {video_url}")
            
            return {
                "success": True,
                "row_number": row_number,
                "sheet_url": f"https://docs.google.com/spreadsheets/d/{settings.GOOGLE_SHEET_ID}"
            }
            
        except Exception as e:
            error_msg = f"Failed to add to Google Sheets: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def update_status(
        self,
        row_number: int,
        status: str = None,
        tiktok_posted: bool = None,
        instagram_posted: bool = None,
        youtube_posted: bool = None,
        notes: str = None
    ) -> Dict:
        """
        Update video status in Google Sheet.
        
        Args:
            row_number: Row number to update
            status: New status
            tiktok_posted: Whether posted to TikTok
            instagram_posted: Whether posted to Instagram
            youtube_posted: Whether posted to YouTube
            notes: Additional notes
            
        Returns:
            Dict with success status
        """
        try:
            worksheet = self.sheet.worksheet(self.worksheet_name)
            
            # Update cells
            if status:
                worksheet.update_cell(row_number, 6, status)
            if tiktok_posted is not None:
                worksheet.update_cell(row_number, 7, 'Yes' if tiktok_posted else 'No')
            if instagram_posted is not None:
                worksheet.update_cell(row_number, 8, 'Yes' if instagram_posted else 'No')
            if youtube_posted is not None:
                worksheet.update_cell(row_number, 9, 'Yes' if youtube_posted else 'No')
            if notes:
                worksheet.update_cell(row_number, 10, notes)
            
            print(f"✅ Updated Google Sheets row {row_number}")
            
            return {"success": True, "row_number": row_number}
            
        except Exception as e:
            error_msg = f"Failed to update Google Sheets: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_pending_videos(self) -> list:
        """
        Get all videos with 'Pending' status.
        
        Returns:
            List of pending video dicts
        """
        try:
            worksheet = self.sheet.worksheet(self.worksheet_name)
            all_records = worksheet.get_all_records()
            
            pending = [
                record for record in all_records
                if record.get('Status', '').lower() == 'pending'
            ]
            
            return pending
            
        except Exception as e:
            print(f"❌ Failed to get pending videos: {e}")
            return []
    
    def list_videos(self, limit: int = 10) -> list:
        """
        List recent videos from Google Sheet.
        
        Args:
            limit: Maximum number of videos to return
            
        Returns:
            List of video dicts
        """
        try:
            worksheet = self.sheet.worksheet(self.worksheet_name)
            all_records = worksheet.get_all_records()
            
            # Return most recent videos
            return all_records[-limit:] if len(all_records) > limit else all_records
            
        except Exception as e:
            print(f"❌ Failed to list videos: {e}")
            return []


def add_to_sheets(video_url: str, title: str, prompt: str = None, duration: int = None) -> Dict:
    """
    Convenience function to add video to Google Sheets.
    
    Args:
        video_url: S3 URL of video
        title: Video title
        prompt: Original prompt
        duration: Video duration
        
    Returns:
        Dict with result
    """
    try:
        uploader = GoogleSheetsUploader()
        return uploader.add_video(video_url, title, prompt, duration)
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

