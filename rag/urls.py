from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.natural_language_query, name='natural_language_query'),
]