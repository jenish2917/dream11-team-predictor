from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'teams', views.TeamViewSet)
router.register(r'venues', views.VenueViewSet)
router.register(r'players', views.PlayerViewSet)
router.register(r'predictions', views.PredictionViewSet, basename='prediction')

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # API endpoints
    path('', include(router.urls)),
    path('predict-team/', views.predict_team, name='predict-team'),
      # ESPNCricinfo integration endpoints
    path('scrape/match/<str:match_id>/', views.scrape_match, name='scrape-match'),
    path('scrape/player/<str:player_id>/', views.scrape_player, name='scrape-player'),
    path('scrape/season/<int:year>/', views.scrape_season, name='scrape-season'),
    path('update-stats/', views.update_player_stats, name='update-player-stats'),
      # Enhanced player statistics endpoints
    path('enhance-player-stats/', views.enhance_player_stats, name='enhance-player-stats'),    path('predict-player-performance/', views.predict_player_performance, name='predict-player-performance'),
]

# Import prediction views for ML functionality
from .prediction_views import predict_player_performance

# Add additional API endpoints
urlpatterns += [
    path('api/predict-player-performance/', predict_player_performance, name='predict-player-ml'),
]

