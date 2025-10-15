from django.urls import path
from .views import HomeView, CVView, CVDownloadView

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('cv/', CVView.as_view(), name='cv'),
    path('cv/download/', CVDownloadView.as_view(), name='cv_download'),
]