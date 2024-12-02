from django import forms
from .models import Survey, PriceSurvey
import logging

logger = logging.getLogger(__name__)


class SurveyForm(forms.ModelForm):
    DISAPPOINTMENT_CHOICES = [
        ('very_disappointed', 'Very disappointed'),
        ('somewhat_disappointed', 'Somewhat disappointed'),
        ('not_disappointed', 'Not disappointed'),
    ]

    disappointment_level = forms.ChoiceField(
        choices=DISAPPOINTMENT_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )

    class Meta:
        model = Survey
        fields = ['occupation', 'disappointment_level', 'missing_features',
                  'most_used_feature', 'satisfaction_score', 'rating']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom styling and placeholders
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        self.fields['missing_features'].widget.attrs.update({
            'rows': '4',
            'placeholder': 'Please tell us what features were missing or disappointing...'
        })
        self.fields['most_used_feature'].widget.attrs.update({
            'placeholder': 'Which feature do you use the most?'
        })

    def clean(self):
        try:
            cleaned_data = super().clean()
            logger.debug(f"Cleaned data: {cleaned_data}")  # Debug log
            return cleaned_data
        except Exception as e:
            logger.error(f"Form cleaning error: {str(e)}")  # Debug log
            raise


class PriceSurveyForm(forms.ModelForm):
    PLAN_CHOICES = [
        ('pay_go', 'Pay As You Go'),
        ('monthly', 'Monthly Unlimited'),
        ('annual', 'Annual Unlimited'),
    ]

    # Pay As You Go pricing
    payg_too_expensive = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (2.99, '$2.99 (~$0.30 per generation)'),
            (3.99, '$3.99 (~$0.40 per generation)'),
            (4.99, '$4.99 (~$0.50 per generation)'),
        ])
    )
    
    payg_too_cheap = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (0.99, '$0.99 (~$0.10 per generation)'),
            (1.49, '$1.49 (~$0.15 per generation)'),
            (1.99, '$1.99 (~$0.20 per generation)'),
        ])
    )
    
    # Monthly plan pricing
    too_expensive = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (49.99, '$49.99/month'),
            (39.99, '$39.99/month'),
            (34.99, '$34.99/month'),
        ])
    )
    
    too_cheap = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (9.99, '$9.99/month'),
            (14.99, '$14.99/month'),
            (19.99, '$19.99/month'),
        ])
    )
    
    expensive = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (29.99, '$29.99/month'),
            (34.99, '$34.99/month'),
            (39.99, '$39.99/month'),
        ])
    )
    
    # Annual plan pricing
    annual_too_expensive = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (299, '$299/year (~$24.92/month)'),
            (349, '$349/year (~$29.08/month)'),
            (399, '$399/year (~$33.25/month)'),
        ])
    )
    
    annual_bargain = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        widget=forms.RadioSelect(choices=[
            (179, '$179/year (~$14.92/month) - 40% off'),
            (210, '$210/year (~$17.50/month) - 30% off'),
            (249, '$249/year (~$20.75/month) - 17% off'),
        ])
    )
    
    preferred_plan = forms.ChoiceField(
        choices=PLAN_CHOICES,
        widget=forms.RadioSelect
    )

    class Meta:
        model = PriceSurvey
        fields = [
            'payg_too_expensive',
            'payg_too_cheap',
            'too_expensive',
            'too_cheap',
            'expensive',
            'annual_too_expensive',
            'annual_bargain',
            'preferred_plan',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = True