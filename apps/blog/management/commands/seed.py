import random
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.text import slugify

from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()

# Constants
DEFAULT_USERS: int = 20
DEFAULT_POSTS: int = 100
DEFAULT_COMMENTS: int = 500

SEED_PASSWORD: str = "password123"

INACTIVE_USER_RATIO: float = 0.15
STAFF_USER_RATIO: float = 0.10

POST_PUBLISHED_RATIO: float = 0.70
POST_WITHOUT_CATEGORY_RATIO: float = 0.10

MIN_TAGS_PER_POST: int = 0
MAX_TAGS_PER_POST: int = 5

MIN_COMMENT_SENTENCES: int = 1
MAX_COMMENT_SENTENCES: int = 3
NB_POST_PARAGRAPHS: int = 3

CATEGORY_NAMES: list[str] = [
    "Python",
    "Django",
    "DevOps",
    "Frontend",
    "Databases",
    "Architecture",
    "Security",
    "Testing",
]

TAG_NAMES: list[str] = [
    "DRF",
    "PostgreSQL",
    "Docker",
    "Redis",
    "Celery",
    "Kubernetes",
    "CI/CD",
    "GraphQL",
    "FastAPI",
    "Asyncio",
    "Pytest",
    "Tailwind",
    "Unfold",
    "ORM",
    "Git",
    "Linux",
    "Nginx",
    "REST",
    "WebSockets",
    "AWS",
]


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--users",
            type=int,
            default=DEFAULT_USERS,
            help="Number of users to create",
        )
        parser.add_argument(
            "--posts",
            type=int,
            default=DEFAULT_POSTS,
            help="Number of posts to create",
        )
        parser.add_argument(
            "--comments",
            type=int,
            default=DEFAULT_COMMENTS,
            help="Number of comments to create",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing data before seeding",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        start_time: float = time.time()
        fake = Faker()

        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        if users_count < 0 or posts_count < 0 or comments_count < 0:
            raise CommandError("Counts for users, posts, and comments cannot be negative.")

        if clear:
            self.stdout.write("Clearing existing data...")
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.WARNING("Existing data cleared (superusers preserved)."))

        # Validation checks
        total_users_available = User.objects.count() + users_count
        if (posts_count > 0 or comments_count > 0) and total_users_available == 0:
            raise CommandError("Cannot create posts or comments without any users.")

        # 1. Users
        created_users_count: int = 0
        used_emails: set[str] = set(User.objects.values_list("email", flat=True))
        hashed_password: str = make_password(SEED_PASSWORD)
        users_to_create: list[User] = []

        for _ in range(users_count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            base_email = f"{slugify(first_name)}.{slugify(last_name)}@{fake.free_email_domain()}"
            email = base_email
            counter = 1
            while email in used_emails:
                email = f"{slugify(first_name)}.{slugify(last_name)}{counter}@{fake.free_email_domain()}"
                counter += 1
            used_emails.add(email)

            is_active = random.random() >= INACTIVE_USER_RATIO
            is_staff = random.random() < STAFF_USER_RATIO

            users_to_create.append(
                User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=is_active,
                    is_staff=is_staff,
                )
            )

        if users_to_create:
            created_users = User.objects.bulk_create(users_to_create)
            created_users_count = len(created_users)

        all_users: list[User] = list(User.objects.all())

        # 2. Categories
        existing_categories: set[str] = set(Category.objects.values_list("name", flat=True))
        cats_to_create: list[Category] = [
            Category(name=name, slug=slugify(name))
            for name in CATEGORY_NAMES
            if name not in existing_categories
        ]
        created_cats = Category.objects.bulk_create(cats_to_create)
        created_cats_count = len(created_cats)
        all_categories: list[Category] = list(Category.objects.all())

        # 3. Tags
        existing_tags: set[str] = set(Tag.objects.values_list("name", flat=True))
        tags_to_create: list[Tag] = [
            Tag(name=name, slug=slugify(name))
            for name in TAG_NAMES
            if name not in existing_tags
        ]
        created_tags = Tag.objects.bulk_create(tags_to_create)
        created_tags_count = len(created_tags)
        all_tags: list[Tag] = list(Tag.objects.all())

        # 4. Posts
        used_post_slugs: set[str] = set(Post.objects.values_list("slug", flat=True))
        posts_to_create: list[Post] = []
        tags_per_post: list[list[Tag]] = []

        for _ in range(posts_count):
            author = random.choice(all_users)
            title = fake.sentence(nb_words=6).rstrip(".")
            base_slug = slugify(title)
            slug = base_slug
            counter = 2
            while slug in used_post_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            used_post_slugs.add(slug)

            category = None
            if all_categories and random.random() >= POST_WITHOUT_CATEGORY_RATIO:
                category = random.choice(all_categories)

            status = (
                Post.PostStatus.PUBLISHED
                if random.random() < POST_PUBLISHED_RATIO
                else Post.PostStatus.DRAFT
            )

            body = "\n\n".join(fake.paragraphs(nb=NB_POST_PARAGRAPHS))

            posts_to_create.append(
                Post(
                    author=author,
                    title=title,
                    slug=slug,
                    body=body,
                    category=category,
                    status=status,
                )
            )

            num_tags = random.randint(MIN_TAGS_PER_POST, min(MAX_TAGS_PER_POST, len(all_tags)))
            tags_per_post.append(random.sample(all_tags, num_tags) if all_tags else [])

        created_posts = Post.objects.bulk_create(posts_to_create)
        created_posts_count = len(created_posts)

        # Set tags for posts (ManyToMany relationship)
        for post, tags in zip(created_posts, tags_per_post):
            if tags:
                post.tags.set(tags)

        # 5. Comments
        published_posts: list[Post] = list(Post.objects.filter(status=Post.PostStatus.PUBLISHED))
        if comments_count > 0 and not published_posts:
            raise CommandError("Cannot create comments because there are no published posts.")

        comments_to_create: list[Comment] = []
        for _ in range(comments_count):
            post = random.choice(published_posts)
            author = random.choice(all_users)
            body = " ".join(fake.sentences(nb=random.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES)))
            comments_to_create.append(
                Comment(
                    post=post,
                    author=author,
                    body=body,
                )
            )

        created_comments = Comment.objects.bulk_create(comments_to_create)
        created_comments_count = len(created_comments)

        elapsed: float = time.time() - start_time

        self.stdout.write(f"Users:      {created_users_count:>4} created")
        self.stdout.write(f"Categories: {created_cats_count:>4} created")
        self.stdout.write(f"Tags:       {created_tags_count:>4} created")
        self.stdout.write(f"Posts:      {created_posts_count:>4} created")
        self.stdout.write(f"Comments:   {created_comments_count:>4} created")
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed:.2f} seconds"))