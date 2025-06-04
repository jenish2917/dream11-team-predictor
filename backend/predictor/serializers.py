"""
Serializers for the predictor app
"""
from rest_framework import serializers
from predictor.models import PredictionHistory
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

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
