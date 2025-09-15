from django.contrib import admin
from .models import TestModel, RelatedTestModel


@admin.register(TestModel)
class TestModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_at', 'updated_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RelatedTestModel)
class RelatedTestModelAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_model', 'value')
    list_filter = ('test_model',)
    search_fields = ('title', 'test_model__name')
