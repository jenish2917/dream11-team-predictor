"""
Serializers for the predictor app
"""
from rest_framework import serializers
from predictor.models import (
    PredictionHistory, UserProfile, Team, Player, Venue, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, required=False, label='Confirm password')
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password2', 'first_name', 'last_name']
        read_only_fields = ['id']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, attrs):
        # If password2 is provided, validate it matches password
        if 'password2' in attrs and attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        # Remove password2 if it exists
        validated_data.pop('password2', None)
        
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'bio', 'preferred_team', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TeamSerializer(serializers.ModelSerializer):
    """
    Serializer for the Team model
    """
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_name', 'logo']
        read_only_fields = ['id']

class VenueSerializer(serializers.ModelSerializer):
    """
    Serializer for the Venue model
    """
    class Meta:
        model = Venue
        fields = ['id', 'name', 'city', 'country']
        read_only_fields = ['id']

class PlayerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Player model
    """
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = Player
        fields = ['id', 'name', 'team', 'role', 'batting_average', 'bowling_average', 'recent_form', 
                 'consistency_index', 'last_5_matches_form', 'venue_performance', 'opposition_performance']
        read_only_fields = ['id']

class PlayerDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Player model with additional stats
    """
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = Player
        fields = '__all__'
        read_only_fields = ['id']

class PredictionPlayerSerializer(serializers.ModelSerializer):
    """
    Serializer for the PredictionPlayer model
    """
    player = PlayerSerializer(read_only=True)
    player_id = serializers.PrimaryKeyRelatedField(queryset=Player.objects.all(), write_only=True, source='player')
    
    class Meta:
        model = PredictionPlayer
        fields = ['id', 'player', 'player_id', 'captain', 'vice_captain', 'expected_points']
        read_only_fields = ['id']

class PredictionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Prediction model
    """
    user = UserSerializer(read_only=True)
    team1 = TeamSerializer(read_only=True)
    team2 = TeamSerializer(read_only=True)
    venue = VenueSerializer(read_only=True)
    
    # For write operations
    team1_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), write_only=True, source='team1')
    team2_id = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all(), write_only=True, source='team2')
    venue_id = serializers.PrimaryKeyRelatedField(queryset=Venue.objects.all(), write_only=True, source='venue')
    
    class Meta:
        model = Prediction
        fields = ['id', 'user', 'title', 'description', 'team1', 'team2', 'venue', 
                 'match_date', 'is_public', 'created_at', 'updated_at', 
                 'team1_id', 'team2_id', 'venue_id']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class PredictionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Prediction model including selected players
    """
    user = UserSerializer(read_only=True)
    team1 = TeamSerializer(read_only=True)
    team2 = TeamSerializer(read_only=True)
    venue = VenueSerializer(read_only=True)
    players = PredictionPlayerSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Prediction
        fields = ['id', 'user', 'title', 'description', 'team1', 'team2', 'venue', 
                 'match_date', 'is_public', 'created_at', 'updated_at', 'players', 'likes_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_likes_count(self, obj):
        return obj.likes.count()

class PlayerCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the PlayerComment model
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PlayerComment
        fields = ['id', 'user', 'player', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class PredictionLikeSerializer(serializers.ModelSerializer):
    """
    Serializer for the PredictionLike model
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PredictionLike
        fields = ['id', 'user', 'prediction', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class PredictionHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for the PredictionHistory model
    """
    user = UserSerializer(read_only=True)
    result = serializers.JSONField()
    
    class Meta:
        model = PredictionHistory
        fields = ['id', 'user', 'team1', 'team2', 'result', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """
        Create a new prediction history entry
        """
        # Extract the result data
        result_data = validated_data.pop('result', {})
        
        # Create the prediction history entry
        prediction = PredictionHistory.objects.create(**validated_data)
        
        # Set the result
        prediction.result = result_data
        prediction.save()
        
        return prediction
