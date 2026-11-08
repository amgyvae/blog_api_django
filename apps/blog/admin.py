from typing import Any

from django.contrib import admin
from django.db import models
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display

from apps.blog.models import Category, Comment, Post, Tag

COMMENT_BODY_MAX_LEN: int = 50


class CommentInline(TabularInline):
    model = Comment
    tab = True
    per_page = 10
    extra = 0
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return super().get_queryset(request).annotate(total_posts=Count("posts"))

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Any) -> int:
        return obj.total_posts


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug", "posts_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(total_posts=Count("posts"))

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Any) -> int:
        return obj.total_posts


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post", "author", "short_body", "created_at")
    list_filter_submit = True
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")

    @display(description="Body")
    def short_body(self, obj: Comment) -> str:
        if len(obj.body) > COMMENT_BODY_MAX_LEN:
            return f"{obj.body[:COMMENT_BODY_MAX_LEN]}..."
        return obj.body


@admin.register(Post)
class PostAdmin(ModelAdmin):
    warn_unsaved_form = True
    inlines = [CommentInline]
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    readonly_fields = ("created_at", "updated_at")

    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }

    list_select_related = ("author", "category")
    list_display = (
        "header_col",
        "status_label",
        "category",
        "tags_dropdown",
        "comments_count",
        "created_at",
    )
    list_filter_submit = True
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("title", "body", "author__email")

    actions_list = ["publish_all_drafts"]
    actions_row = ["toggle_publish_row"]
    actions_detail = ["open_post_comments"]
    actions_submit_line = ["save_and_publish"]
    actions = ["publish_selected", "draft_selected"]

    fieldsets = (
        ("Content", {"fields": ("title", "slug", "body")}),
        ("Classification", {"fields": ("category", "tags", "status")}),
        ("Meta", {"fields": ("author", "created_at", "updated_at")}),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .prefetch_related("tags")
            .annotate(total_comments=Count("comments"))
        )

    @display(description="Post", header=True)
    def header_col(self, obj: Post) -> list[str]:
        return [obj.title, obj.author.email]

    @display(description="Status", label={"published": "success", "draft": "warning"})
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> list[str]:
        return [tag.name for tag in obj.tags.all()]

    @display(description="Comments", ordering="total_comments")
    def comments_count(self, obj: Any) -> int:
        return obj.total_comments

    # Bulk actions
    @action(description="Publish selected posts")
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.PostStatus.PUBLISHED)

    @action(description="Move selected posts to drafts")
    def draft_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        queryset.update(status=Post.PostStatus.DRAFT)

    # Actions list (above table)
    @action(description="Publish all drafts")
    def publish_all_drafts(self, request: HttpRequest) -> HttpResponseRedirect:
        Post.objects.filter(status=Post.PostStatus.DRAFT).update(status=Post.PostStatus.PUBLISHED)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse("admin:blog_post_changelist")))

    # Actions row (inside every row)
    @action(description="Publish / Unpublish")
    def toggle_publish_row(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        post = Post.objects.get(pk=object_id)
        if post.status == Post.PostStatus.PUBLISHED:
            post.status = Post.PostStatus.DRAFT
        else:
            post.status = Post.PostStatus.PUBLISHED
        post.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", reverse("admin:blog_post_changelist")))

    # Actions detail (on edit page)
    @action(description="Open this post's comments")
    def open_post_comments(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        return HttpResponseRedirect(f"{reverse('admin:blog_comment_changelist')}?post__id__exact={object_id}")

    # Actions submit line (next to save)
    @action(description="Save & publish")
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.PostStatus.PUBLISHED
        obj.save()