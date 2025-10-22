from django.core.management.base import BaseCommand, CommandError
from sora.utils.sheets_uploader import GoogleSheetsUploader


class Command(BaseCommand):
    help = 'Manage Google Sheets integration for Sora videos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add',
            nargs='+',
            metavar=('URL', 'TITLE'),
            help='Add video: --add "https://s3.../video.mp4" "Video Title" "Prompt" "Duration"'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List recent videos from sheet'
        )
        parser.add_argument(
            '--pending',
            action='store_true',
            help='List pending videos'
        )
        parser.add_argument(
            '--update',
            nargs=2,
            metavar=('ROW', 'STATUS'),
            help='Update status: --update ROW_NUMBER STATUS'
        )

    def handle(self, *args, **options):
        try:
            uploader = GoogleSheetsUploader()
        except ValueError as e:
            raise CommandError(str(e))
        
        # Add video
        if options['add']:
            args_list = options['add']
            if len(args_list) < 2:
                raise CommandError("--add requires at least URL and TITLE")
            
            url = args_list[0]
            title = args_list[1]
            prompt = args_list[2] if len(args_list) > 2 else None
            duration = int(args_list[3]) if len(args_list) > 3 else None
            
            result = uploader.add_video(url, title, prompt, duration)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS('✅ Added to Google Sheets'))
                self.stdout.write(f"   Row: {result['row_number']}")
                self.stdout.write(f"   Sheet: {result['sheet_url']}")
            else:
                raise CommandError(f"Failed: {result['error']}")
        
        # List videos
        elif options['list']:
            self.stdout.write("📋 Recent videos:\n")
            videos = uploader.list_videos(limit=10)
            
            if not videos:
                self.stdout.write(self.style.WARNING("No videos found"))
                return
            
            for video in videos:
                self.stdout.write(f"\n  📹 {video.get('Title', 'N/A')}")
                self.stdout.write(f"     URL: {video.get('Video URL', 'N/A')}")
                self.stdout.write(f"     Status: {video.get('Status', 'N/A')}")
                self.stdout.write(f"     TikTok: {video.get('TikTok Posted', 'No')}")
        
        # List pending
        elif options['pending']:
            self.stdout.write("⏳ Pending videos:\n")
            videos = uploader.get_pending_videos()
            
            if not videos:
                self.stdout.write(self.style.SUCCESS("No pending videos"))
                return
            
            for video in videos:
                self.stdout.write(f"\n  📹 {video.get('Title', 'N/A')}")
                self.stdout.write(f"     URL: {video.get('Video URL', 'N/A')}")
                self.stdout.write(f"     Prompt: {video.get('Prompt', 'N/A')}")
        
        # Update status
        elif options['update']:
            row_number = int(options['update'][0])
            status = options['update'][1]
            
            result = uploader.update_status(row_number, status=status)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'✅ Updated row {row_number}'))
            else:
                raise CommandError(f"Failed: {result['error']}")
        
        else:
            self.stdout.write(self.style.WARNING(
                "No action specified. Use --add, --list, --pending, or --update"
            ))

