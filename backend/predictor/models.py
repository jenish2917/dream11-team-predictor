from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    preferred_team = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class Team(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10)
    logo = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Venue(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Player(models.Model):
    ROLE_CHOICES = (
        ('BAT', 'Batsman'),
        ('BWL', 'Bowler'),
        ('AR', 'All-Rounder'),
        ('WK', 'Wicket-Keeper'),
    )
    
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    role = models.CharField(max_length=3, choices=ROLE_CHOICES)
    batting_average = models.FloatField(default=0.0)
    bowling_average = models.FloatField(default=0.0)
    recent_form = models.FloatField(default=0.0)  # A calculated field for recent performance
    
    # Enhanced player statistics fields
    consistency_index = models.FloatField(default=0.0)  # Measure of player consistency
    last_5_matches_form = models.FloatField(default=0.0)  # Performance in last 5 matches
    venue_performance = models.JSONField(null=True, blank=True)  # Performance by venue
    opposition_performance = models.JSONField(null=True, blank=True)  # Performance against teams
    
    def __str__(self):
        return f"{self.name} ({self.team.short_name})"

class Prediction(models.Model):
    PITCH_CHOICES = (
        ('BAT', 'Batting-friendly'),
        ('BWL', 'Bowling-friendly'),
        ('BAL', 'Balanced'),
        ('SPIN', 'Spin-friendly'),
    )
    
    PREDICTION_TYPE = (
        ('AGG', 'Aggressive'),
        ('BAL', 'Balanced'),
        ('RISK', 'Risk-averse'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1_predictions')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2_predictions')
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    pitch_type = models.CharField(max_length=4, choices=PITCH_CHOICES)
    prediction_type = models.CharField(max_length=4, choices=PREDICTION_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.team1.short_name} vs {self.team2.short_name} - {self.get_prediction_type_display()}"

class PredictionPlayer(models.Model):
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    is_captain = models.BooleanField(default=False)
    is_vice_captain = models.BooleanField(default=False)
    expected_points = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.player.name} - {self.prediction}"

class PlayerComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.player.name}"

class PredictionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='likes')
    is_like = models.BooleanField(default=True)  # True for like, False for dislike
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'prediction')
    
    def __str__(self):
        return f"{self.user.username} {'liked' if self.is_like else 'disliked'} {self.prediction}"
