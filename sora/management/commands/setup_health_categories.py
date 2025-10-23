"""
Setup diverse health categories for content generation
Adds categories beyond just skincare to ensure content diversity
"""

from django.core.management.base import BaseCommand
from blog.models import Category


class Command(BaseCommand):
    help = 'Setup diverse health categories for content generation'

    def handle(self, *args, **options):
        """Create diverse health categories if they don't exist."""
        
        # Define diverse health categories
        health_categories = [
            {
                'name': 'Nutrition',
                'description': 'Healthy eating, vitamins, meal planning, dietary tips, and nutritional advice for optimal health.'
            },
            {
                'name': 'Fitness',
                'description': 'Exercise routines, workout tips, physical activity, strength training, and fitness guidance.'
            },
            {
                'name': 'Mental Health',
                'description': 'Stress management, mindfulness, mental wellness, anxiety relief, and emotional wellbeing.'
            },
            {
                'name': 'Sleep',
                'description': 'Sleep hygiene, rest optimization, bedtime routines, and sleep quality improvement.'
            },
            {
                'name': 'Hydration',
                'description': 'Water intake, hydration benefits, fluid balance, and proper hydration for health.'
            },
            {
                'name': 'Skincare',
                'description': 'Natural skincare, skin health, beauty routines, and dermatological wellness.'
            },
            {
                'name': 'Wellness',
                'description': 'General wellness, lifestyle tips, self-care, and holistic health approaches.'
            },
            {
                'name': 'Digestive Health',
                'description': 'Gut health, digestion, digestive wellness, and gastrointestinal health tips.'
            },
            {
                'name': 'Immune System',
                'description': 'Immune support, cold prevention, health defense, and immunity boosting strategies.'
            },
            {
                'name': 'Weight Management',
                'description': 'Healthy weight, metabolism, body composition, and sustainable weight management.'
            }
        ]
        
        self.stdout.write("🏥 Setting up diverse health categories...")
        self.stdout.write("=" * 60)
        
        created_count = 0
        existing_count = 0
        
        for category_data in health_categories:
            category_name = category_data['name']
            category_description = category_data['description']
            
            # Check if category already exists
            category, created = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    'description': category_description
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created: {category_name}")
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠️ Already exists: {category_name}")
                )
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"📊 Summary:")
        self.stdout.write(f"   ✅ Created: {created_count}")
        self.stdout.write(f"   ⚠️ Already existed: {existing_count}")
        self.stdout.write(f"   📝 Total categories: {Category.objects.count()}")
        
        # Display all categories
        self.stdout.write(f"\n📋 All Health Categories:")
        for category in Category.objects.all().order_by('name'):
            self.stdout.write(f"   • {category.name}")
        
        self.stdout.write("\n🎉 Health categories setup completed!")
        self.stdout.write("Content generation will now have access to diverse health topics.")
