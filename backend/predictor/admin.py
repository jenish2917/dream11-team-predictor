from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import (
    UserProfile, Team, Venue, Player, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)
from .admin_actions import BulkPlayerActionsAdmin

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

def reset_player_statistics(modeladmin, request, queryset):
    """Admin action to reset player statistics while keeping player records"""
    count = 0
    for player in queryset:
        # Store original name and team for messaging
        player_name = player.name
        team_name = player.team.short_name if player.team else "Unknown"
        
        # Reset statistics but keep core player data
        player.batting_average = 0.0
        player.bowling_average = 0.0
        player.recent_form = 0.0
        player.consistency_index = 0.0
        player.last_5_matches_form = 0.0
        player.venue_performance = None
        player.opposition_performance = None
        player.save()
        count += 1
    
    messages.success(request, f"Statistics reset for {count} player(s)")
reset_player_statistics.short_description = "Reset selected players' statistics"

@admin.register(Player)
class PlayerAdmin(BulkPlayerActionsAdmin):
    list_display = ('name', 'team', 'role', 'batting_average', 'bowling_average', 'show_stats_status')
    list_filter = ('team', 'role')
    search_fields = ('name', 'team__name')
    actions = [reset_player_statistics]
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']  # Remove default delete action for safety
        return actions
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_reset_url'] = 'bulk-reset-stats/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def show_stats_status(self, obj):
        """Show a visual indicator of whether player has statistics data"""
        has_stats = (
            obj.batting_average > 0 or 
            obj.bowling_average > 0 or 
            obj.recent_form > 0 or 
            obj.consistency_index > 0 or
            obj.last_5_matches_form > 0 or
            obj.venue_performance is not None or
            obj.opposition_performance is not None
        )
        
        if has_stats:
            return format_html(
                '<span style="color: green; font-weight: bold;">●</span> Has Stats'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">○</span> No Stats'
            )
    show_stats_status.short_description = "Statistics Status"

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
