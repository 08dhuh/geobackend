from rest_framework import serializers
from .models import *

class DepthQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = DepthQuery
        fields = '__all__'

class DepthProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepthProfileModel
        fields = '__all__'

class DepthLayerSerializer(serializers.ModelSerializer):
    profile = DepthProfileSerializer(read_only=True)
    profile_id = serializers.PrimaryKeyRelatedField(
        queryset=DepthProfileModel.objects.all(),
        source='profile',
        write_only=True
    )
    class Meta:
        model = DepthLayerModel
        fields = '__all__'

class UserInputModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInputModel
        fields = '__all__'