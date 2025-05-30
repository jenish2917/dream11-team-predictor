"""
Custom admin actions for the Dream11 Team Predictor.
These provide bulk operations for data management in the admin interface.
"""

from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction

from .models import Player, Team


class BulkPlayerActionsAdmin(admin.ModelAdmin):
    """Mixin for bulk player actions in the admin"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'bulk-reset-stats/',
                self.admin_site.admin_view(self.bulk_reset_stats_view),
                name='bulk-reset-stats',
            ),
        ]
        return custom_urls + urls
    
    def bulk_reset_stats_view(self, request):
        """View for bulk resetting player statistics"""
        teams = Team.objects.all()
        
        if request.method == 'POST':
            action = request.POST.get('action')
            team_ids = request.POST.getlist('teams')
            
            if not team_ids and action != 'reset_all':
                messages.error(request, "Please select at least one team")
                return HttpResponseRedirect(request.path)
                
            try:
                with transaction.atomic():
                    if action == 'reset_all':
                        # Reset stats for all players
                        count = Player.objects.all().update(
                            batting_average=0.0,
                            bowling_average=0.0,
                            recent_form=0.0,
                            consistency_index=0.0,
                            last_5_matches_form=0.0,
                            venue_performance=None,
                            opposition_performance=None
                        )
                        messages.success(request, f"Statistics reset for all {count} players")
                    
                    elif action == 'reset_selected':
                        # Reset stats for players in selected teams
                        count = Player.objects.filter(team__id__in=team_ids).update(
                            batting_average=0.0,
                            bowling_average=0.0,
                            recent_form=0.0,
                            consistency_index=0.0,
                            last_5_matches_form=0.0,
                            venue_performance=None,
                            opposition_performance=None
                        )
                        messages.success(request, f"Statistics reset for {count} players in the selected teams")
                        
            except Exception as e:
                messages.error(request, f"Error resetting player data: {str(e)}")
                
            return HttpResponseRedirect('../')
            
        context = {
            'title': 'Bulk Reset Player Statistics',
            'teams': teams,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }
        
        return render(request, 'admin/bulk_reset_stats.html', context)
