from django.contrib import admin

from .models import HeroSlide, PageSection


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("title",)


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("section_type",)
