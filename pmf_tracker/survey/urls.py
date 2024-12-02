from django.urls import path
from .views import (
    SurveyView, 
    ThankYouView, 
    DashboardView,
    PriceDashboardView,
    PriceSurveyView,
    calculate_pmf,
)

urlpatterns = [
    path('survey/', SurveyView.as_view(), name='survey_submit'),
    path('thank-you/', ThankYouView.as_view(), name='survey_thank_you'),
    path('calculate-pmf/', calculate_pmf, name='calculate_pmf'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('price-survey/', PriceSurveyView.as_view(), name='price_survey'),
    path('price-dashboard/', PriceDashboardView.as_view(), name='price_dashboard'),
]