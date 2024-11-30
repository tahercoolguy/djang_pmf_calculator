from django.contrib import admin
from .models import Survey, PMFScore

@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ('occupation', 'disappointment_level', 'created_at')
    list_filter = ('occupation', 'disappointment_level', 'created_at')
    search_fields = ('missing_features', 'most_used_feature')

@admin.register(PMFScore)
class PMFScoreAdmin(admin.ModelAdmin):
    list_display = ('week_start', 'score', 'total_responses', 'created_at')
    list_filter = ('week_start', 'created_at')