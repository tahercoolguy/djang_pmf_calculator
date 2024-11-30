from django import forms
from .models import Survey


class SurveyForm(forms.ModelForm):
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