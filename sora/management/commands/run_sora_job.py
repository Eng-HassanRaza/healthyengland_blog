from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os

# Import generator utilities from sora app
from sora.utils.generator import SoraVideoGenerator


class Command(BaseCommand):
    help = 'Run Sora 2 video generation job (for cron or manual execution)'

    def add_arguments(self, parser):
        parser.add_argument('prompt', type=str, help='Prompt for video generation')
        parser.add_argument('--duration', type=int, default=4, help='Duration: 4, 8, or 12 seconds')
        parser.add_argument('--aspect-ratio', choices=['16:9', '9:16', '1:1'], default='16:9')
        parser.add_argument('--style', type=str, help='Optional style')
        parser.add_argument('--wait', action='store_true', help='Wait for completion and download')
        parser.add_argument('--download', action='store_true', help='Download video when complete')

    def handle(self, *args, **options):
        prompt = options['prompt']
        generator = SoraVideoGenerator()

        result = generator.generate_video(
            prompt=prompt,
            duration=options['duration'],
            aspect_ratio=options['aspect_ratio'],
            style=options.get('style')
        )

        if result.get('error'):
            raise CommandError(result['error'])

        video_id = result.get('video_id')
        self.stdout.write(self.style.SUCCESS(f"Started video job: {video_id}"))

        if options['wait'] or options['download']:
            status = generator.wait_for_completion(video_id)
            if status.get('status') != 'completed':
                raise CommandError(f"Job did not complete successfully: {status}")
            if options['download']:
                path = generator.download_video(video_id)
                self.stdout.write(self.style.SUCCESS(f"Downloaded to: {path}"))
