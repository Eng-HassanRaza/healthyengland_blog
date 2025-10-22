from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os

# Import generator utilities from sora app
from sora.utils.generator import SoraVideoGenerator


class Command(BaseCommand):
    help = 'Run Sora 2 video generation job (for cron or manual execution)'

    def add_arguments(self, parser):
        parser.add_argument('prompt', type=str, help='Prompt for video generation')

    def handle(self, *args, **options):
        from django.conf import settings
        
        prompt = options['prompt']
        
        # Get all settings from .env
        duration = settings.SORA_DEFAULT_DURATION
        aspect_ratio = settings.SORA_DEFAULT_ASPECT_RATIO
        delete_local = settings.SORA_DELETE_LOCAL
        upload_s3 = settings.SORA_AUTO_UPLOAD_S3
        add_sheets = settings.SORA_AUTO_ADD_SHEETS
        
        self.stdout.write("="*70)
        self.stdout.write(f"🎬 Generating Sora Video")
        self.stdout.write("="*70)
        self.stdout.write(f"Prompt: {prompt}")
        self.stdout.write(f"Duration: {duration}s")
        self.stdout.write(f"Aspect Ratio: {aspect_ratio} (720x1280)")
        self.stdout.write(f"Upload to S3: {'Yes' if upload_s3 else 'No'}")
        self.stdout.write(f"Add to Sheets: {'Yes' if add_sheets else 'No'}")
        self.stdout.write(f"Delete Local: {'Yes' if delete_local else 'No'}")
        self.stdout.write("="*70 + "\n")
        
        generator = SoraVideoGenerator()

        result = generator.generate_video(
            prompt=prompt,
            duration=duration,
            aspect_ratio=aspect_ratio
        )

        if result.get('error'):
            raise CommandError(result['error'])

        video_id = result.get('video_id')
        self.stdout.write(self.style.SUCCESS(f"✅ Video generation started: {video_id}\n"))

        # Always wait and download
        self.stdout.write("⏳ Waiting for video completion...")
        status = generator.wait_for_completion(video_id)
        
        if status.get('status') != 'completed':
            raise CommandError(f"Video generation failed: {status}")
        
        self.stdout.write(self.style.SUCCESS("✅ Video completed!\n"))
        
        # Download and process
        self.stdout.write("⬇️  Downloading video...")
        path = generator.download_video(
            video_id,
            upload_to_s3=upload_s3,
            delete_local_after_s3=delete_local
        )
        
        # Show results
        self.stdout.write("\n" + "="*70)
        self.stdout.write("🎉 SUCCESS!")
        self.stdout.write("="*70)
        
        if path.startswith('http'):
            self.stdout.write(f"S3 URL: {path}")
            if delete_local:
                self.stdout.write("Local file: Deleted")
            if add_sheets:
                self.stdout.write("Google Sheets: Added")
        else:
            self.stdout.write(f"Local file: {path}")
            if upload_s3:
                self.stdout.write("S3: Uploaded")
            if add_sheets:
                self.stdout.write("Google Sheets: Added")
        
        self.stdout.write("="*70)
