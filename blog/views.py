from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json

from .models import Post, Category, Comment, Newsletter, Contact
from .forms import CommentForm, NewsletterForm, ContactForm


class PostListView(ListView):
    """Main blog post list view."""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        """Get published posts with related data."""
        return Post.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Add extra context data."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_posts'] = Post.objects.filter(
            status='published',
            featured_image__isnull=False
        )[:3]
        return context


class PostDetailView(DetailView):
    """Individual blog post detail view."""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        """Get published posts."""
        return Post.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Add extra context data."""
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Increment view count
        post.increment_views()
        
        # Get related posts
        context['related_posts'] = Post.objects.filter(
            status='published',
            category=post.category
        ).exclude(id=post.id)[:3]
        
        # Get comments
        context['comments'] = Comment.objects.filter(
            post=post,
            is_approved=True
        ).order_by('-created_at')
        
        # Comment form
        context['comment_form'] = CommentForm()
        
        return context


def category_view(request, slug):
    """View posts by category."""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(
        category=category,
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author').prefetch_related('tags')
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'posts': posts,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/category.html', context)


def tag_view(request, slug):
    """View posts by tag."""
    posts = Post.objects.filter(
        tags__slug=slug,
        status='published',
        published_at__lte=timezone.now()
    ).select_related('author', 'category').prefetch_related('tags').distinct()
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'tag_slug': slug,
        'posts': posts,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/tag.html', context)


def search_view(request):
    """Search posts."""
    query = request.GET.get('q', '')
    posts = Post.objects.none()
    
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query),
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'posts': posts,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/search.html', context)


@require_POST
def add_comment(request, post_id):
    """Add a comment to a post."""
    post = get_object_or_404(Post, id=post_id, status='published')
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        messages.success(request, 'Your comment has been submitted and is awaiting approval.')
    else:
        messages.error(request, 'There was an error with your comment.')
    
    return redirect('blog:post_detail', slug=post.slug)


@require_POST
def newsletter_signup(request):
    """Handle newsletter signup."""
    form = NewsletterForm(request.POST)
    
    if form.is_valid():
        email = form.cleaned_data['email']
        newsletter, created = Newsletter.objects.get_or_create(
            email=email,
            defaults={'is_active': True}
        )
        
        if created:
            messages.success(request, 'Thank you for subscribing to our newsletter!')
        else:
            if newsletter.is_active:
                messages.info(request, 'You are already subscribed to our newsletter.')
            else:
                newsletter.is_active = True
                newsletter.save()
                messages.success(request, 'Welcome back! You have been resubscribed.')
    else:
        messages.error(request, 'Please enter a valid email address.')
    
    return redirect(request.META.get('HTTP_REFERER', 'blog:post_list'))


def contact_view(request):
    """Contact form view."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()

            # Send email notification to admin
            subject = f'New Contact Form Submission: {contact.subject}'
            message = f"""
You have received a new message from the contact form on Healthy England.

Name: {contact.name}
Email: {contact.email}
Subject: {contact.subject}

Message:
{contact.message}

---
This email was sent from the Healthy England contact form.
"""

            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['info@healthyengland.com'],
                    fail_silently=False,
                )
                messages.success(request, 'Thank you for your message. We will get back to you soon!')
            except Exception as e:
                # Still save the form but notify about email issue
                messages.warning(request, 'Your message has been saved, but there was an issue sending the email notification.')

            return redirect('blog:contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/contact.html', context)


def about_view(request):
    """About page view."""
    context = {
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/about.html', context)


@csrf_exempt
@require_POST
def like_post(request, post_id):
    """Like a post (AJAX)."""
    post = get_object_or_404(Post, id=post_id)
    post.likes += 1
    post.save(update_fields=['likes'])
    
    return JsonResponse({
        'likes': post.likes,
        'success': True
    })


def privacy_view(request):
    """Privacy policy page view."""
    context = {
        'categories': Category.objects.all(),
    }
    return render(request, 'blog/privacy.html', context)