from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Main blog views
    path('', views.PostListView.as_view(), name='post_list'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('tag/<slug:slug>/', views.tag_view, name='tag'),
    path('search/', views.search_view, name='search'),
    
    # Interactive views
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # Static pages
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy/', views.privacy_view, name='privacy'),
]
