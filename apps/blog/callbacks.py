import json
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.http import HttpRequest
from decouple import config

from apps.blog.models import Category, Comment, Post

User = get_user_model()


def environment_callback(request: HttpRequest) -> list[str]:
    env_id = config("BLOG_ENV_ID", default="local")
    if env_id == "prod":
        return ["Production", "danger"]
    return ["Local", "warning"]


def drafts_badge(request: HttpRequest) -> int:
    return Post.objects.filter(status=Post.PostStatus.DRAFT).count()


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    total_users = User.objects.count()
    published_posts = Post.objects.filter(status=Post.PostStatus.PUBLISHED).count()
    draft_posts = Post.objects.filter(status=Post.PostStatus.DRAFT).count()
    total_comments = Comment.objects.count()
    total_posts = published_posts + draft_posts

    published_percentage = round((published_posts / total_posts * 100), 1) if total_posts else 0
    draft_percentage = round((draft_posts / total_posts * 100), 1) if total_posts else 0

    # Posts per Category (Bar chart)
    category_data = Category.objects.annotate(posts_count=Count("posts")).order_by("-posts_count")
    cat_labels = [c.name for c in category_data]
    cat_counts = [c.posts_count for c in category_data]

    bar_chart_data = json.dumps(
        {
            "labels": cat_labels,
            "datasets": [
                {
                    "label": "Posts per Category",
                    "data": cat_counts,
                    "backgroundColor": "#0ea5e9",
                }
            ],
        }
    )

    # Top 5 Authors
    top_authors = (
        User.objects.annotate(posts_count=Count("posts"))
        .filter(posts_count__gt=0)
        .order_by("-posts_count")[:5]
    )

    context.update(
        {
            "kpis": [
                {"title": "Total Users", "metric": total_users, "icon": "group"},
                {"title": "Published Posts", "metric": published_posts, "icon": "article"},
                {"title": "Drafts", "metric": draft_posts, "icon": "edit_note"},
                {"title": "Total Comments", "metric": total_comments, "icon": "chat"},
            ],
            "bar_chart_data": bar_chart_data,
            "top_authors": top_authors,
            "published_percentage": published_percentage,
            "draft_percentage": draft_percentage,
        }
    )
    return context