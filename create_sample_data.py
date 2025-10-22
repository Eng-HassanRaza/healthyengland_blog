#!/usr/bin/env python3
"""
Create sample data for Healthy England blog
"""

import os
import sys
import django
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthyengland.settings')
django.setup()

from django.contrib.auth.models import User
from blog.models import Category, Post, Comment, Newsletter, Contact
from taggit.models import Tag


def create_sample_data():
    """Create sample data for the blog."""
    
    # Create categories
    categories_data = [
        {'name': 'Nutrition', 'description': 'Healthy eating tips and nutritional advice'},
        {'name': 'Fitness', 'description': 'Exercise routines and fitness guidance'},
        {'name': 'Mental Health', 'description': 'Mental wellness and stress management'},
        {'name': 'Wellness', 'description': 'General health and wellness topics'},
        {'name': 'Sleep', 'description': 'Sleep hygiene and rest optimization'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        categories.append(category)
        print(f"Created category: {category.name}")
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@healthyengland.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("Created admin user")
    
    # Create sample posts
    posts_data = [
        {
            'title': '10 Essential Nutrients for a Healthy Life',
            'content': '''
            <h2>Introduction</h2>
            <p>Proper nutrition is the foundation of good health. In this comprehensive guide, we'll explore the 10 essential nutrients your body needs to function optimally.</p>
            
            <h3>1. Protein</h3>
            <p>Protein is crucial for building and repairing tissues. Include lean meats, fish, beans, and nuts in your diet.</p>
            
            <h3>2. Carbohydrates</h3>
            <p>Choose complex carbohydrates like whole grains, fruits, and vegetables for sustained energy.</p>
            
            <h3>3. Healthy Fats</h3>
            <p>Omega-3 fatty acids from fish, nuts, and seeds support brain health and reduce inflammation.</p>
            
            <h3>4. Vitamins</h3>
            <p>Vitamins A, C, D, E, and K play vital roles in immune function, bone health, and cellular protection.</p>
            
            <h3>5. Minerals</h3>
            <p>Essential minerals like calcium, iron, and zinc support bone strength, oxygen transport, and immune function.</p>
            
            <h2>Conclusion</h2>
            <p>By incorporating these essential nutrients into your daily diet, you'll be well on your way to optimal health and vitality.</p>
            ''',
            'excerpt': 'Discover the 10 essential nutrients your body needs for optimal health and learn how to incorporate them into your daily diet.',
            'category': categories[0],  # Nutrition
            'tags': ['nutrition', 'vitamins', 'minerals', 'healthy-eating']
        },
        {
            'title': 'The Complete Guide to Morning Exercise Routines',
            'content': '''
            <h2>Why Morning Exercise?</h2>
            <p>Starting your day with exercise sets a positive tone and provides numerous health benefits.</p>
            
            <h3>Benefits of Morning Workouts</h3>
            <ul>
                <li>Boosts metabolism for the entire day</li>
                <li>Improves mental clarity and focus</li>
                <li>Enhances sleep quality</li>
                <li>Increases energy levels</li>
            </ul>
            
            <h3>Sample Morning Routine</h3>
            <p>Here's a 30-minute routine you can do at home:</p>
            <ol>
                <li>5-minute warm-up (light stretching)</li>
                <li>10 minutes of cardio (jumping jacks, running in place)</li>
                <li>10 minutes of strength training (push-ups, squats, planks)</li>
                <li>5-minute cool-down (stretching and deep breathing)</li>
            </ol>
            
            <h2>Getting Started</h2>
            <p>Start slowly and gradually increase intensity. Consistency is more important than intensity.</p>
            ''',
            'excerpt': 'Learn how to create an effective morning exercise routine that will energize your day and improve your overall health.',
            'category': categories[1],  # Fitness
            'tags': ['exercise', 'morning-routine', 'fitness', 'workout']
        },
        {
            'title': 'Managing Stress: 5 Proven Techniques',
            'content': '''
            <h2>Understanding Stress</h2>
            <p>Stress is a natural response to challenges, but chronic stress can negatively impact your health.</p>
            
            <h3>Technique 1: Deep Breathing</h3>
            <p>Practice the 4-7-8 breathing technique: inhale for 4 counts, hold for 7, exhale for 8.</p>
            
            <h3>Technique 2: Mindfulness Meditation</h3>
            <p>Spend 10-15 minutes daily focusing on the present moment without judgment.</p>
            
            <h3>Technique 3: Physical Activity</h3>
            <p>Regular exercise releases endorphins, natural mood boosters that reduce stress.</p>
            
            <h3>Technique 4: Time Management</h3>
            <p>Prioritize tasks and break large projects into manageable steps.</p>
            
            <h3>Technique 5: Social Support</h3>
            <p>Connect with friends, family, or support groups to share your concerns.</p>
            
            <h2>When to Seek Help</h2>
            <p>If stress becomes overwhelming, consider speaking with a mental health professional.</p>
            ''',
            'excerpt': 'Discover 5 evidence-based techniques to manage stress effectively and improve your mental well-being.',
            'category': categories[2],  # Mental Health
            'tags': ['stress-management', 'mental-health', 'meditation', 'wellness']
        },
        {
            'title': 'The Science of Quality Sleep',
            'content': '''
            <h2>Why Sleep Matters</h2>
            <p>Quality sleep is essential for physical recovery, mental clarity, and overall health.</p>
            
            <h3>Sleep Cycles Explained</h3>
            <p>Your body goes through 4-6 sleep cycles per night, each lasting about 90 minutes.</p>
            
            <h3>Creating the Perfect Sleep Environment</h3>
            <ul>
                <li>Keep your bedroom cool (18-20°C)</li>
                <li>Use blackout curtains or an eye mask</li>
                <li>Invest in a comfortable mattress and pillows</li>
                <li>Remove electronic devices from the bedroom</li>
            </ul>
            
            <h3>Sleep Hygiene Tips</h3>
            <p>Establish a consistent bedtime routine:</p>
            <ol>
                <li>Go to bed and wake up at the same time daily</li>
                <li>Avoid caffeine after 2 PM</li>
                <li>Limit screen time before bed</li>
                <li>Create a relaxing pre-sleep routine</li>
            </ol>
            
            <h2>Common Sleep Disorders</h2>
            <p>If you consistently struggle with sleep, consult a healthcare provider about potential sleep disorders.</p>
            ''',
            'excerpt': 'Learn about the science of sleep and discover practical tips for improving your sleep quality and overall health.',
            'category': categories[4],  # Sleep
            'tags': ['sleep', 'sleep-hygiene', 'wellness', 'health']
        },
        {
            'title': 'Building Healthy Habits That Last',
            'content': '''
            <h2>The Psychology of Habit Formation</h2>
            <p>Understanding how habits work is the first step to building lasting healthy behaviors.</p>
            
            <h3>The Habit Loop</h3>
            <p>Every habit consists of three components: cue, routine, and reward.</p>
            
            <h3>Start Small</h3>
            <p>Begin with tiny changes that are easy to maintain. Success builds momentum.</p>
            
            <h3>Stack Your Habits</h3>
            <p>Attach new habits to existing ones. For example, do 5 minutes of stretching after brushing your teeth.</p>
            
            <h3>Track Your Progress</h3>
            <p>Use a habit tracker or journal to monitor your consistency and celebrate wins.</p>
            
            <h3>Be Patient</h3>
            <p>Research shows it takes an average of 66 days to form a new habit. Stay consistent!</p>
            
            <h2>Common Pitfalls to Avoid</h2>
            <p>Avoid trying to change too many habits at once. Focus on one or two at a time.</p>
            ''',
            'excerpt': 'Learn the science behind habit formation and discover strategies for building healthy habits that stick.',
            'category': categories[3],  # Wellness
            'tags': ['habits', 'wellness', 'lifestyle', 'self-improvement']
        }
    ]
    
    for post_data in posts_data:
        post, created = Post.objects.get_or_create(
            title=post_data['title'],
            defaults={
                'author': admin_user,
                'category': post_data['category'],
                'content': post_data['content'],
                'excerpt': post_data['excerpt'],
                'status': 'published',
                'published_at': timezone.now()
            }
        )
        
        if created:
            # Add tags
            for tag_name in post_data['tags']:
                post.tags.add(tag_name)
            
            print(f"Created post: {post.title}")
        else:
            print(f"Post already exists: {post.title}")
    
    # Create some sample comments
    comments_data = [
        {
            'post': Post.objects.filter(title__icontains='Essential Nutrients').first(),
            'name': 'Sarah Johnson',
            'email': 'sarah@example.com',
            'content': 'This article was incredibly helpful! I\'ve been trying to improve my nutrition and this gave me a clear roadmap.',
            'is_approved': True
        },
        {
            'post': Post.objects.filter(title__icontains='Morning Exercise').first(),
            'name': 'Mike Chen',
            'email': 'mike@example.com',
            'content': 'I started following this morning routine last week and I can already feel the difference in my energy levels!',
            'is_approved': True
        },
        {
            'post': Post.objects.filter(title__icontains='Managing Stress').first(),
            'name': 'Emma Wilson',
            'email': 'emma@example.com',
            'content': 'The breathing technique really works. Thank you for sharing these practical stress management tips.',
            'is_approved': True
        }
    ]
    
    for comment_data in comments_data:
        if comment_data['post']:
            comment, created = Comment.objects.get_or_create(
                post=comment_data['post'],
                name=comment_data['name'],
                email=comment_data['email'],
                content=comment_data['content'],
                defaults={'is_approved': comment_data['is_approved']}
            )
            if created:
                print(f"Created comment by {comment.name}")
    
    # Create some newsletter subscribers
    newsletter_emails = [
        'subscriber1@example.com',
        'subscriber2@example.com',
        'subscriber3@example.com'
    ]
    
    for email in newsletter_emails:
        newsletter, created = Newsletter.objects.get_or_create(
            email=email,
            defaults={'is_active': True}
        )
        if created:
            print(f"Created newsletter subscriber: {email}")
    
    print("\n✅ Sample data created successfully!")
    print("You can now visit http://127.0.0.1:8000 to see your blog with sample content.")
    print("Admin panel: http://127.0.0.1:8000/admin (username: admin, password: admin123)")


if __name__ == "__main__":
    create_sample_data()
