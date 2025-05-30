from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Team, Venue, Player, 
    Prediction, PredictionPlayer, PlayerComment, PredictionLike
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id',)

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'bio', 'preferred_team', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('id', 'name', 'short_name', 'logo')
        read_only_fields = ('id',)

class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('id', 'name', 'city', 'country')
        read_only_fields = ('id',)

class PlayerSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Player
        fields = ('id', 'name', 'team', 'team_name', 'role', 'batting_average', 'bowling_average', 'recent_form')
        read_only_fields = ('id',)
    
    def get_team_name(self, obj):
        return obj.team.name

class PlayerDetailSerializer(PlayerSerializer):
    team = TeamSerializer(read_only=True)
    
    class Meta(PlayerSerializer.Meta):
        fields = PlayerSerializer.Meta.fields + ('team',)

class PredictionPlayerSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    
    class Meta:
        model = PredictionPlayer
        fields = ('id', 'player', 'is_captain', 'is_vice_captain', 'expected_points')
        read_only_fields = ('id',)

class PredictionSerializer(serializers.ModelSerializer):
    team1_name = serializers.SerializerMethodField()
    team2_name = serializers.SerializerMethodField()
    venue_name = serializers.SerializerMethodField()
    pitch_type_display = serializers.CharField(source='get_pitch_type_display', read_only=True)
    prediction_type_display = serializers.CharField(source='get_prediction_type_display', read_only=True)
    
    class Meta:
        model = Prediction
        fields = (
            'id', 'user', 'team1', 'team1_name', 'team2', 'team2_name', 
            'venue', 'venue_name', 'pitch_type', 'pitch_type_display',
            'prediction_type', 'prediction_type_display', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def get_team1_name(self, obj):
        return obj.team1.name
    
    def get_team2_name(self, obj):
        return obj.team2.name
    
    def get_venue_name(self, obj):
        return obj.venue.name

class PredictionDetailSerializer(PredictionSerializer):
    players = PredictionPlayerSerializer(many=True, read_only=True)
    likes_count = serializers.SerializerMethodField()
    dislikes_count = serializers.SerializerMethodField()
    
    class Meta(PredictionSerializer.Meta):
        fields = PredictionSerializer.Meta.fields + ('players', 'likes_count', 'dislikes_count')
    
    def get_likes_count(self, obj):
        return obj.likes.filter(is_like=True).count()
    
    def get_dislikes_count(self, obj):
        return obj.likes.filter(is_like=False).count()

class PlayerCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PlayerComment
        fields = ('id', 'user', 'player', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')

class PredictionLikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = PredictionLike
        fields = ('id', 'user', 'prediction', 'is_like', 'created_at')
        read_only_fields = ('id', 'created_at')

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')
        extra_kwargs = {
            'password': {'write_only': True}
        }
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        
        # Check for existing users with the same username or email
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "A user with this username already exists."})
            
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
            
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        UserProfile.objects.create(user=user)
        return user
