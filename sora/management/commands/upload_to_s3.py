from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from sora.utils.s3_uploader import S3VideoUploader


class Command(BaseCommand):
    help = 'Upload video files to S3 bucket'

    def add_arguments(self, parser):
        parser.add_argument(
            'video_path',
            type=str,
            help='Path to video file or directory'
        )
        parser.add_argument(
            '--delete-local',
            action='store_true',
            help='Delete local file after successful upload'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all videos in S3 bucket'
        )

    def handle(self, *args, **options):
        uploader = S3VideoUploader()
        
        # List videos in S3
        if options['list']:
            self.stdout.write("📋 Listing videos in S3...")
            videos = uploader.list_videos()
            
            if not videos:
                self.stdout.write(self.style.WARNING("No videos found in S3"))
                return
            
            self.stdout.write(self.style.SUCCESS(f"\nFound {len(videos)} video(s):\n"))
            for video in videos:
                self.stdout.write(f"  📹 {video['filename']}")
                self.stdout.write(f"     Size: {video['size_mb']:.2f} MB")
                self.stdout.write(f"     URL: {video['url']}")
                self.stdout.write(f"     Modified: {video['last_modified']}\n")
            return
        
        # Upload video(s)
        video_path = Path(options['video_path'])
        
        if not video_path.exists():
            raise CommandError(f"Path not found: {video_path}")
        
        # Handle directory
        if video_path.is_dir():
            videos = list(video_path.glob('*.mp4'))
            if not videos:
                raise CommandError(f"No .mp4 files found in: {video_path}")
            
            self.stdout.write(f"Found {len(videos)} video(s) to upload\n")
            
            success_count = 0
            for video_file in videos:
                self.stdout.write(f"\n📤 Uploading: {video_file.name}")
                result = uploader.upload_video(
                    str(video_file),
                    delete_local=options['delete_local']
                )
                
                if result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ {video_file.name} uploaded"))
                    self.stdout.write(f"   URL: {result['s3_url']}")
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ {video_file.name} failed: {result['error']}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ Uploaded {success_count}/{len(videos)} videos")
            )
        
        # Handle single file
        else:
            if not video_path.suffix == '.mp4':
                raise CommandError("File must be a .mp4 video")
            
            self.stdout.write(f"📤 Uploading: {video_path.name}")
            result = uploader.upload_video(
                str(video_path),
                delete_local=options['delete_local']
            )
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS("✅ Upload successful!"))
                self.stdout.write(f"   S3 URL: {result['s3_url']}")
                self.stdout.write(f"   S3 Key: {result['s3_key']}")
                self.stdout.write(f"   Size: {result['size_mb']:.2f} MB")
                
                if options['delete_local']:
                    self.stdout.write(self.style.WARNING("🗑️  Local file deleted"))
            else:
                raise CommandError(f"Upload failed: {result['error']}")

