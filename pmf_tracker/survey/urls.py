from django.urls import path
from .views import SurveyView, DashboardView, calculate_pmf, ThankYouView

urlpatterns = [
    path('survey/', SurveyView.as_view(), name='survey'),
    path('thank-you/', ThankYouView.as_view(), name='survey_thank_you'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('calculate-pmf/', calculate_pmf, name='calculate_pmf'),
]