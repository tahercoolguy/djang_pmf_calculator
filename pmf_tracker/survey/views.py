from django.views.generic import CreateView, TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import Survey, PMFScore
from .utils import PMFAnalytics
import plotly.graph_objects as go
import plotly.utils
import json
from django.db.models import Count, Avg


from .forms import SurveyForm
from django.urls import reverse_lazy
class SurveyView(CreateView):
    form_class = SurveyForm
    template_name = 'survey/survey.html'
    success_url = reverse_lazy('survey_thank_you')

class ThankYouView(TemplateView):
    template_name = 'survey/thank_you.html'


class DashboardView(TemplateView):
    template_name = 'survey/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Initialize empty charts
        pmf_trend = go.Figure()
        segment_chart = go.Figure()
        missing_chart = go.Figure()
        most_used_chart = go.Figure()
        disappointment_chart = go.Figure()

        # Get weekly PMF scores
        weekly_scores = PMFScore.objects.order_by('-week_start')[:12]

        if weekly_scores.exists():
            latest_score = weekly_scores.first()

            # 1. PMF Trend Line Chart
            pmf_trend.add_trace(go.Scatter(
                x=[score.week_start for score in weekly_scores],
                y=[score.score for score in weekly_scores],
                mode='lines+markers',
                name='PMF Score'
            ))
            pmf_trend.add_hline(y=40, line_dash="dash", annotation_text="PMF Target (40%)")
            pmf_trend.update_layout(
                title='PMF Score Trend Over Time',
                xaxis_title='Week',
                yaxis_title='PMF Score (%)'
            )

            # 2. Segment Analysis Chart
            if latest_score.segment_scores:
                segment_chart = go.Figure(data=[
                    go.Bar(
                        x=list(latest_score.segment_scores.keys()),
                        y=list(latest_score.segment_scores.values()),
                        text=[f'{v:.1f}%' for v in latest_score.segment_scores.values()],
                        textposition='auto',
                    )
                ])
                segment_chart.update_layout(
                    title='PMF Score by Segment',
                    xaxis_title='Segment',
                    yaxis_title='PMF Score (%)'
                )

            # 3. Missing Features Chart (from Survey data)
            missing_features = Survey.objects.values('missing_features').annotate(
                count=Count('missing_features')
            ).order_by('-count')[:10]

            if missing_features:
                missing_chart = go.Figure(data=[
                    go.Bar(
                        x=[item['missing_features'] for item in missing_features],
                        y=[item['count'] for item in missing_features],
                        text=[item['count'] for item in missing_features],
                        textposition='auto',
                    )
                ])
                missing_chart.update_layout(
                    title='Top Missing Features',
                    xaxis_title='Feature',
                    yaxis_title='Mentions'
                )

            # 4. Most Used Features Chart
            most_used = Survey.objects.values('most_used_feature').annotate(
                count=Count('most_used_feature')
            ).order_by('-count')[:10]

            if most_used:
                most_used_chart = go.Figure(data=[
                    go.Pie(
                        labels=[item['most_used_feature'] for item in most_used],
                        values=[item['count'] for item in most_used],
                        hole=.3
                    )
                ])
                most_used_chart.update_layout(title='Most Used Features Distribution')

            # 5. Disappointment Level Distribution
            disappointment_data = Survey.objects.values('disappointment_level').annotate(
                count=Count('disappointment_level')
            )

            if disappointment_data:
                disappointment_chart = go.Figure(data=[
                    go.Pie(
                        labels=[self.get_disappointment_label(d['disappointment_level'])
                                for d in disappointment_data],
                        values=[d['count'] for d in disappointment_data],
                        hole=.3
                    )
                ])
                disappointment_chart.update_layout(title='User Disappointment Distribution')

            # 6. Rating Distribution
            rating_data = Survey.objects.values('rating').annotate(
                count=Count('rating')
            ).order_by('rating')

            if rating_data:
                rating_chart = go.Figure(data=[
                    go.Bar(
                        x=[f"{d['rating']} Stars" for d in rating_data],
                        y=[d['count'] for d in rating_data],
                        text=[d['count'] for d in rating_data],
                        textposition='auto',
                    )
                ])
                rating_chart.update_layout(
                    title='Product Rating Distribution',
                    xaxis_title='Rating',
                    yaxis_title='Number of Responses'
                )
            else:
                rating_chart = go.Figure()

            # 7. Satisfaction Levels
            satisfaction_data = Survey.objects.values('satisfaction_score').annotate(
                count=Count('satisfaction_score')
            ).order_by('satisfaction_score')

            if satisfaction_data:
                satisfaction_chart = go.Figure(data=[
                    go.Bar(
                        x=[self.get_satisfaction_label(d['satisfaction_score']) for d in satisfaction_data],
                        y=[d['count'] for d in satisfaction_data],
                        text=[d['count'] for d in satisfaction_data],
                        textposition='auto',
                    )
                ])
                satisfaction_chart.update_layout(
                    title='Satisfaction Level Distribution',
                    xaxis_title='Satisfaction Level',
                    yaxis_title='Number of Responses'
                )
            else:
                satisfaction_chart = go.Figure()

        # Update context with all charts and data
        context.update({
            'pmf_trend_chart': json.dumps(pmf_trend, cls=plotly.utils.PlotlyJSONEncoder),
            'segment_chart': json.dumps(segment_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'missing_chart': json.dumps(missing_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'most_used_chart': json.dumps(most_used_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'disappointment_chart': json.dumps(disappointment_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'rating_chart': json.dumps(rating_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'satisfaction_chart': json.dumps(satisfaction_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'current_score': latest_score.score if weekly_scores.exists() else 0,
            'total_responses': Survey.objects.count(),
            'has_data': weekly_scores.exists(),
        })

        return context

    def get_disappointment_label(self, key):
        labels = {
            'very': 'Very Disappointed',
            'somewhat': 'Somewhat Disappointed',
            'not': 'Not Disappointed'
        }
        return labels.get(key, key)

    def get_satisfaction_label(self, key):
        labels = {
            'very_satisfied': 'Very Satisfied',
            'satisfied': 'Satisfied',
            'neutral': 'Neutral',
            'dissatisfied': 'Dissatisfied',
            'very_dissatisfied': 'Very Dissatisfied'
        }
        return labels.get(key, key)


@staff_member_required
def calculate_pmf(request):
    analytics = PMFAnalytics()
    score = analytics.calculate_weekly_pmf()
    return JsonResponse({'success': True, 'score': score})