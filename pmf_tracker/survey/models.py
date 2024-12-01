from django.db import models
from django.utils import timezone


class Survey(models.Model):
    OCCUPATION_CHOICES = [
        ('developer', 'Developer'),
        ('designer', 'Designer'),
        ('manager', 'Manager'),
        ('founder', 'Founder'),
        ('video_editor', 'Video Editor'),
        ('marketer', 'Marketer'),
        ('student', 'Student'), 
        ('researcher', 'Researcher'),
        ('other', 'Other'),
    ]

    DISAPPOINTMENT_CHOICES = [
        ('very', 'Very disappointed'),
        ('somewhat', 'Somewhat disappointed'),
        ('not', 'Not disappointed'),
    ]

    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES)
    disappointment_level = models.CharField(max_length=20, choices=DISAPPOINTMENT_CHOICES)
    missing_features = models.TextField()
    most_used_feature = models.CharField(max_length=100)
    satisfaction_score = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    created_at = models.DateTimeField(auto_now_add=True)


class PMFScore(models.Model):
    week_start = models.DateField()
    score = models.FloatField()
    total_responses = models.IntegerField()
    segment_scores = models.JSONField(default=dict)
    missing_features_analysis = models.JSONField(default=dict)
    most_used_features = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']