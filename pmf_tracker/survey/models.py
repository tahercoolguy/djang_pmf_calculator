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
        ('very_disappointed', 'Very disappointed'),
        ('somewhat_disappointed', 'Somewhat disappointed'),
        ('not_disappointed', 'Not disappointed'),
    ]

    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES)
    disappointment_level = models.CharField(max_length=50, choices=DISAPPOINTMENT_CHOICES)
    missing_features = models.TextField()
    most_used_feature = models.TextField()
    satisfaction_score = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
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


class PriceSurvey(models.Model):
    # Pay As You Go pricing
    payg_too_expensive = models.DecimalField(max_digits=5, decimal_places=2)
    payg_too_cheap = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Monthly plan pricing
    too_expensive = models.DecimalField(max_digits=5, decimal_places=2)
    too_cheap = models.DecimalField(max_digits=5, decimal_places=2)
    expensive = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Annual plan pricing
    annual_too_expensive = models.DecimalField(max_digits=6, decimal_places=2)
    annual_bargain = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Plan preference
    preferred_plan = models.CharField(
        max_length=20,  # Changed from max_choices to max_length
        choices=[
            ('pay_go', 'Pay As You Go'),
            ('monthly', 'Monthly Unlimited'),
            ('annual', 'Annual Unlimited'),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']