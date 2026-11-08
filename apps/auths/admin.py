from typing import Any

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display

User = get_user_model()

# Re-register Group with Unfold
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(
        help_text=(
            "Raw passwords are not stored, so there is no way to see this user’s password."
        )
    )

    class Meta:
        model = User
        fields = "__all__"


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password_repeat = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")

    def clean_password_repeat(self) -> str:
        password = self.cleaned_data.get("password")
        password_repeat = self.cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            raise forms.ValidationError("Passwords do not match.")
        return password_repeat

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


@admin.register(User)
class UserAdmin(ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = (
        "display_header",
        "is_active_label",
        "is_staff_label",
        "posts_count",
    )
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    actions = ["activate_users", "deactivate_users"]

    fieldsets = (
        ("Personal info", {"fields": ("email", "password", "first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password",
                    "password_repeat",
                ),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return super().get_queryset(request).annotate(total_posts=Count("posts"))

    @display(description="User", header=True)
    def display_header(self, obj: User) -> list[str]:
        full_name = f"{obj.first_name} {obj.last_name}".strip() or "Unnamed"
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper() or "U"
        return [full_name, obj.email, initials]

    @display(description="Active", label={True: "success", False: "danger"})
    def is_active_label(self, obj: User) -> bool:
        return obj.is_active

    @display(description="Staff", label={True: "info", False: "secondary"})
    def is_staff_label(self, obj: User) -> bool:
        return obj.is_staff

    @display(description="Posts", ordering="total_posts")
    def posts_count(self, obj: Any) -> int:
        return obj.total_posts

    @action(description="Activate selected users")
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        queryset.update(is_active=True)

    @action(description="Deactivate selected users")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        queryset.update(is_active=False)