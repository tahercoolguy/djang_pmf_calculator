from django.views.generic import CreateView, TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from .models import Survey, PMFScore, PriceSurvey
from .utils import PMFAnalytics
import plotly.graph_objects as go
import plotly.utils
import json
from django.db.models import Count, Avg
from django.utils import translation
from django.shortcuts import render


from .forms import SurveyForm, PriceSurveyForm
from django.urls import reverse_lazy
class SurveyView(CreateView):
    form_class = SurveyForm
    template_name = 'survey/survey.html'
    success_url = reverse_lazy('survey_thank_you')

    def form_valid(self, form):
        try:
            self.object = form.save()
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'redirect_url': self.get_success_url()
                })
            return super().form_valid(form)
        except Exception as e:
            print(f"Error saving form: {str(e)}")  # Debug log
            if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Server error occurred',
                    'details': str(e)
                }, status=500)
            raise

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed',
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)

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

def survey_view(request):
    # Get the browser's language
    if 'HTTP_ACCEPT_LANGUAGE' in request.META:
        browser_language = request.META['HTTP_ACCEPT_LANGUAGE'].split(',')[0].split('-')[0]
        
        # Only set language if it hasn't been set in the session
        if not request.session.get('language_set'):
            translation.activate(browser_language)
            request.session['language_set'] = True
            request.session['django_language'] = browser_language

    return render(request, 'survey/survey.html')

class PriceSurveyView(CreateView):
    template_name = 'survey/price-survey.html'
    form_class = PriceSurveyForm  # You'll need to create this form
    success_url = reverse_lazy('survey_thank_you')

@method_decorator(staff_member_required, name='dispatch')
class PriceDashboardView(TemplateView):
    template_name = 'survey/price-dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pay As You Go Analysis
        payg_analysis = self.create_price_sensitivity_chart(
            'payg_too_expensive', 
            'payg_too_cheap',
            'Pay As You Go Price Sensitivity',
            per_generation=True
        )

        # Monthly Plan Analysis
        monthly_analysis = self.create_price_sensitivity_chart(
            'too_expensive', 
            'too_cheap',
            'Monthly Plan Price Sensitivity'
        )

        # Annual Plan Analysis
        annual_analysis = self.create_price_sensitivity_chart(
            'annual_too_expensive', 
            'annual_bargain',
            'Annual Plan Price Sensitivity',
            show_monthly_equiv=True
        )

        # Preferred Plan Distribution
        preferred_plan_data = PriceSurvey.objects.values('preferred_plan').annotate(
            count=Count('preferred_plan')
        ).order_by('-count')

        preferred_plan_chart = go.Figure(data=[
            go.Pie(
                labels=[self.get_plan_label(item['preferred_plan']) for item in preferred_plan_data],
                values=[item['count'] for item in preferred_plan_data],
                hole=.3
            )
        ])
        preferred_plan_chart.update_layout(title='Preferred Plan Distribution')

        # Price-Value Perception
        value_perception = self.create_enhanced_value_perception_chart()

        context.update({
            'payg_analysis': json.dumps(payg_analysis, cls=plotly.utils.PlotlyJSONEncoder),
            'monthly_analysis': json.dumps(monthly_analysis, cls=plotly.utils.PlotlyJSONEncoder),
            'annual_analysis': json.dumps(annual_analysis, cls=plotly.utils.PlotlyJSONEncoder),
            'preferred_plan_chart': json.dumps(preferred_plan_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'value_perception': json.dumps(value_perception, cls=plotly.utils.PlotlyJSONEncoder),
            'total_responses': PriceSurvey.objects.count(),
        })

        return context

    def create_price_sensitivity_chart(self, too_expensive_field, too_cheap_field, title, per_generation=False, show_monthly_equiv=False):
        # Get the data from the database
        expensive_data = PriceSurvey.objects.values(too_expensive_field).annotate(
            count=Count(too_expensive_field)
        ).order_by(too_expensive_field)
        
        cheap_data = PriceSurvey.objects.values(too_cheap_field).annotate(
            count=Count(too_cheap_field)
        ).order_by(too_cheap_field)

        # Create the figure
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=[d[too_expensive_field] for d in expensive_data],
            y=[d['count'] for d in expensive_data],
            name='Too Expensive',
            mode='lines+markers',
            line=dict(color='red'),
            hovertemplate='Price: $%{x}<br>Responses: %{y}<extra></extra>'
        ))

        fig.add_trace(go.Scatter(
            x=[d[too_cheap_field] for d in cheap_data],
            y=[d['count'] for d in cheap_data],
            name='Too Cheap',
            mode='lines+markers',
            line=dict(color='blue'),
            hovertemplate='Price: $%{x}<br>Responses: %{y}<extra></extra>'
        ))

        # Calculate intersection point
        optimal_price = self.calculate_price_points(expensive_data, cheap_data)['optimal_price']
        if optimal_price:
            fig.add_vline(
                x=optimal_price,
                line_dash="dash",
                annotation_text="Optimal Price Point",
                annotation_position="top right"
            )

        x_title = 'Price per Generation ($)' if per_generation else 'Price ($)'
        if show_monthly_equiv:
            x_title += ' (with monthly equivalent)'

        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center'
            ),
            xaxis_title=x_title,
            yaxis_title='Number of Responses',
            showlegend=True,
            hovermode='x unified',
            annotations=[
                dict(
                    text="Intersection point suggests optimal pricing",
                    xref="paper",
                    yref="paper",
                    x=0,
                    y=-0.2,
                    showarrow=False
                )
            ]
        )

        return fig

    def create_enhanced_value_perception_chart(self):
        value_data = PriceSurvey.objects.values('preferred_plan').annotate(
            avg_payg=Avg('payg_too_expensive'),
            avg_monthly=Avg('too_expensive'),
            avg_annual=Avg('annual_too_expensive'),
            response_count=Count('preferred_plan'),
            # Add satisfaction or value metric if available
            satisfaction=Avg('satisfaction_score')  # If you have this field
        ).order_by('preferred_plan')

        fig = go.Figure()

        # Color scheme for different plan types
        colors = {
            'pay_go': '#1f77b4',    # Blue
            'monthly': '#2ca02c',   # Green
            'annual': '#ff7f0e'     # Orange
        }

        for plan_data in value_data:
            plan_type = plan_data['preferred_plan']
            
            # Get appropriate price
            price_mapping = {
                'pay_go': 'avg_payg',
                'monthly': 'avg_monthly',
                'annual': 'avg_annual'
            }
            avg_price = plan_data[price_mapping[plan_type]]

            if avg_price is not None:
                # Calculate relative metrics
                max_price = max(d[price_mapping[plan_type]] 
                              for d in value_data 
                              if d[price_mapping[plan_type]] is not None)
                
                relative_position = (avg_price / max_price * 5) if max_price else 0
                
                # Enhanced hover text
                hover_text = (
                    f"Plan: {self.get_plan_label(plan_type)}<br>"
                    f"Average Price: ${avg_price:.2f}<br>"
                    f"Responses: {plan_data['response_count']}<br>"
                    f"Value Score: {relative_position:.1f}/5"
                )

                fig.add_trace(go.Scatter(
                    x=[avg_price],
                    y=[relative_position],
                    mode='markers',
                    marker=dict(
                        size=[plan_data['response_count'] * 2],  # Adjusted size multiplier
                        sizemode='area',
                        sizeref=2.*max(d['response_count'] for d in value_data)/(40.**2),
                        sizemin=4,
                        color=colors.get(plan_type, '#808080'),  # Use color scheme
                        line=dict(color='white', width=1)  # Add white border
                    ),
                    text=[hover_text],
                    name=self.get_plan_label(plan_type),
                    hoverinfo='text'
                ))

        # Enhanced layout
        fig.update_layout(
            title=dict(
                text='Price-Value Analysis by Plan Type',
                x=0.5,
                xanchor='center',
                font=dict(size=20)
            ),
            xaxis=dict(
                title='Price Point ($)',
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='Value Score (1-5)',
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="right",
                x=0.99
            ),
            # Add quadrant lines
            shapes=[
                # Vertical middle line
                dict(
                    type='line',
                    x0=sum(d[price_mapping[d['preferred_plan']]] or 0 
                        for d in value_data)/len(value_data),
                    y0=0,
                    x1=sum(d[price_mapping[d['preferred_plan']]] or 0 
                        for d in value_data)/len(value_data),
                    y1=5,
                    line=dict(color='gray', dash='dash')
                ),
                # Horizontal middle line
                dict(
                    type='line',
                    x0=0,
                    y0=2.5,
                    x1=max(d[price_mapping[d['preferred_plan']]] or 0 
                        for d in value_data),
                    y1=2.5,
                    line=dict(color='gray', dash='dash')
                )
            ],
            annotations=[
                # Quadrant labels
                dict(
                    x=0.25, y=0.25,
                    xref="paper", yref="paper",
                    text="Low Price<br>Low Value",
                    showarrow=False
                ),
                dict(
                    x=0.25, y=0.75,
                    xref="paper", yref="paper",
                    text="Low Price<br>High Value",
                    showarrow=False
                ),
                dict(
                    x=0.75, y=0.25,
                    xref="paper", yref="paper",
                    text="High Price<br>Low Value",
                    showarrow=False
                ),
                dict(
                    x=0.75, y=0.75,
                    xref="paper", yref="paper",
                    text="High Price<br>High Value",
                    showarrow=False
                )
            ]
        )

        return fig

    def get_plan_label(self, key):
        labels = {
            'pay_go': 'Pay As You Go',
            'monthly': 'Monthly Unlimited',
            'annual': 'Annual Unlimited'
        }
        return labels.get(key, key)

    def calculate_price_points(self, expensive_data, cheap_data):
        def find_intersection(line1_x, line1_y, line2_x, line2_y):
            # Find where two lines intersect
            for i in range(len(line1_x)-1):
                for j in range(len(line2_x)-1):
                    if (line1_x[i] <= line2_x[j] <= line1_x[i+1] or 
                        line1_x[i+1] <= line2_x[j] <= line1_x[i]):
                        # Linear interpolation
                        return (line1_x[i] + line2_x[j]) / 2
            return None

        # Get the field names from the first items
        expensive_field = list(expensive_data[0].keys())[0]  # Gets the price field name
        cheap_field = list(cheap_data[0].keys())[0]  # Gets the price field name

        expensive_x = [d[expensive_field] for d in expensive_data]
        expensive_y = [d['count'] for d in expensive_data]
        cheap_x = [d[cheap_field] for d in cheap_data]
        cheap_y = [d['count'] for d in cheap_data]

        try:
            return {
                'optimal_price': find_intersection(expensive_x, expensive_y, cheap_x, cheap_y),
                'pmc': min(expensive_x),  # Point of Marginal Cheapness
                'pme': max(cheap_x),      # Point of Marginal Expensiveness
            }
        except (IndexError, ValueError):
            # Return default values if there's not enough data
            return {
                'optimal_price': None,
                'pmc': None,
                'pme': None,
            }