from collections import Counter
from datetime import timedelta
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from .models import Survey, PMFScore
from django.utils import timezone
from django.db.models import Count


class PMFAnalytics:
    def __init__(self):
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            print(f"Error downloading NLTK data: {e}")
            
        self.stop_words = set(stopwords.words('english'))

    def calculate_pmf_score(self, start_date=None, end_date=None):
        # Get surveys for the period
        surveys = Survey.objects.all()
        if start_date:
            surveys = surveys.filter(created_at__gte=start_date)
        if end_date:
            surveys = surveys.filter(created_at__lte=end_date)

        total_responses = surveys.count()
        if total_responses == 0:
            return 0

        very_disappointed = surveys.filter(
            disappointment_level='very'
        ).count()

        return (very_disappointed / total_responses) * 100

    def analyze_segments(self, surveys):
        segment_scores = {}
        for occupation, _ in Survey.OCCUPATION_CHOICES:
            segment_surveys = surveys.filter(occupation=occupation)
            total = segment_surveys.count()
            if total > 0:
                very_disappointed = segment_surveys.filter(
                    disappointment_level='very'
                ).count()
                segment_scores[occupation] = (very_disappointed / total) * 100
            else:
                segment_scores[occupation] = 0
        return segment_scores

    def analyze_features(self, surveys):
        # Analyze missing features
        missing_features = []
        for survey in surveys:
            if survey.missing_features:  # Check if missing_features exists
                try:
                    words = word_tokenize(survey.missing_features.lower())
                    words = [w for w in words if w not in self.stop_words and w.isalnum()]
                    missing_features.extend(words)
                except Exception as e:
                    print(f"Error processing missing features: {e}")
                    continue

        missing_features_count = dict(Counter(missing_features).most_common(10))

        # Analyze most used features
        most_used = surveys.values('most_used_feature').annotate(
            count=Count('most_used_feature')
        ).order_by('-count')[:10]
        most_used_dict = {item['most_used_feature']: item['count'] for item in most_used}

        return missing_features_count, most_used_dict

    def calculate_weekly_pmf(self):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        surveys = Survey.objects.filter(
            created_at__range=(start_date, end_date)
        )

        score = self.calculate_pmf_score(start_date, end_date)
        segment_scores = self.analyze_segments(surveys)
        missing_features, most_used = self.analyze_features(surveys)

        PMFScore.objects.create(
            week_start=start_date.date(),
            score=score,
            total_responses=surveys.count(),
            segment_scores=segment_scores,
            missing_features_analysis=missing_features,
            most_used_features=most_used
        )

        return score