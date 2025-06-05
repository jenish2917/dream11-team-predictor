from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *  # Import all views from the current modul

urlpatterns = [
    path('register/', views.RegisterView.view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('user/profile/', views.UserProfileView.as_view(), name='user-profile'),

    path('status/', views.api_status, name='api-status'),
    path('predict/team/', views.predict_team, name='predict-team'),
    path('load/csv-data/', views.load_csv_data, name='load-csv-data'),
    path('predict/player-performance/', views.predict_player_performance, name='predict-player-performance'),
   
]

