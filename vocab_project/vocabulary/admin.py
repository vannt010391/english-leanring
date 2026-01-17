from django.contrib import admin
from .models import Vocabulary, VocabularyTopic


class VocabularyTopicInline(admin.TabularInline):
    model = VocabularyTopic
    extra = 1


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ['word', 'phonetics', 'word_type', 'level', 'meaning', 'source', 'is_system', 'owner', 'learning_status', 'created_at']
    list_filter = ['is_system', 'source', 'learning_status', 'created_by_role', 'word_type', 'level']
    search_fields = ['word', 'meaning', 'meaning_vi', 'phonetics']
    inlines = [VocabularyTopicInline]
    ordering = ['-created_at']

    fieldsets = (
        ('Word Information', {
            'fields': ('word', 'phonetics', 'word_type', 'level')
        }),
        ('Meanings', {
            'fields': ('meaning', 'meaning_vi')
        }),
        ('Additional Info', {
            'fields': ('example_sentence', 'note')
        }),
        ('Metadata', {
            'fields': ('source', 'is_system', 'owner', 'created_by_role', 'learning_status')
        }),
    )
