from django.urls import path
from . import views

app_name = 'weather'  # optional but useful for namespacing

urlpatterns = [
    path('', views.home, name='home'),  # Home page with search bar
]
