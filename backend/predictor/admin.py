from django.contrib import admin
from .models import (
    UserProfile, Team, Venue, Player, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'preferred_team', 'created_at')
    search_fields = ('user__username', 'preferred_team')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name')
    search_fields = ('name', 'short_name')

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'country')
    search_fields = ('name', 'city', 'country')

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'team', 'role', 'batting_average', 'bowling_average')
    list_filter = ('team', 'role')
    search_fields = ('name', 'team__name')

class PredictionPlayerInline(admin.TabularInline):
    model = PredictionPlayer
    extra = 0

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'venue', 'pitch_type', 'prediction_type', 'created_at')
    list_filter = ('team1', 'team2', 'venue', 'pitch_type', 'prediction_type')
    search_fields = ('user__username', 'team1__name', 'team2__name', 'venue__name')
    inlines = [PredictionPlayerInline]

@admin.register(PredictionPlayer)
class PredictionPlayerAdmin(admin.ModelAdmin):
    list_display = ('player', 'prediction', 'is_captain', 'is_vice_captain', 'expected_points')
    list_filter = ('is_captain', 'is_vice_captain')
    search_fields = ('player__name', 'prediction__team1__name', 'prediction__team2__name')

@admin.register(PlayerComment)
class PlayerCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'player', 'comment', 'created_at')
    search_fields = ('user__username', 'player__name', 'comment')

@admin.register(PredictionLike)
class PredictionLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'prediction', 'is_like', 'created_at')
    list_filter = ('is_like',)
    search_fields = ('user__username', 'prediction__team1__name', 'prediction__team2__name')
