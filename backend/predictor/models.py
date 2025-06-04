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
        return f"{self.name} ({self.get_role_display()}) - {self.team.name}"

class PredictionHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1_predictions')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2_predictions')
    result = models.JSONField()  # Store the prediction result as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Prediction: {self.team1.name} vs {self.team2.name} by {self.user.username}"
        
    class Meta:
        verbose_name_plural = "Prediction histories"
        ordering = ['-created_at']

class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_predictions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team1_user_predictions')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team2_user_predictions')
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True, related_name='predictions')
    match_date = models.DateTimeField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.team1.name} vs {self.team2.name}"
    
    class Meta:
        ordering = ['-created_at']

class PredictionPlayer(models.Model):
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='prediction_selections')
    captain = models.BooleanField(default=False)
    vice_captain = models.BooleanField(default=False)
    expected_points = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.player.name} in {self.prediction.title}"
    
    class Meta:
        unique_together = ('prediction', 'player')

class PlayerComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='player_comments')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment on {self.player.name} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

class PredictionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prediction_likes')
    prediction = models.ForeignKey(Prediction, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Like on {self.prediction.title} by {self.user.username}"
    
    class Meta:
        unique_together = ('user', 'prediction')
