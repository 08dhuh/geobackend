from rest_framework import serializers
#from .models import *


class InitialInputSerializer(serializers.Serializer):
    required_flow_rate = serializers.FloatField()
    hydraulic_conductivity = serializers.FloatField()
    average_porosity = serializers.FloatField()
    bore_lifetime_year = serializers.IntegerField()
    groundwater_depth = serializers.FloatField()
    long_term_decline_rate = serializers.FloatField()
    allowable_drawdown = serializers.FloatField()
    safety_margin = serializers.FloatField()
    target_aquifer_layer = serializers.CharField(max_length=50,
                                                  required=False, allow_null=True)
    top_aquifer_layer = serializers.CharField(max_length=50,
                                               required=False, allow_null=True)
    
    def validate(self, data):
        target_aquifer_layer = data.get('target_aquifer_layer')
        top_aquifer_layer = data.get('top_aquifer_layer')
        
        # Custom validation logic for target_aquifer_layer and top_aquifer_layer
        if target_aquifer_layer is not None and target_aquifer_layer not in ['109lmta', '111lta']:
            raise serializers.ValidationError({'target_aquifer_layer': 'Invalid target aquifer layer'})
        
        if top_aquifer_layer is not None and top_aquifer_layer not in ['100qa', '102utqa']:
            raise serializers.ValidationError({'top_aquifer_layer': 'Invalid top aquifer layer'})
        
        return data


class WellBoreCalcInputSerializer(serializers.Serializer):
    loc_vicgrid = serializers.ListField(
        child = serializers.IntegerField(),
        min_length = 2,
        max_length = 2
    )
    crs_type = serializers.CharField(max_length = 255)
    min_resolution = serializers.IntegerField()
    pixels = serializers.ListField(
        child = serializers.IntegerField(),
        min_length = 2,
        max_length = 2
    )
    initial_input_values = InitialInputSerializer()
    is_production_pump = serializers.CharField(max_length=5)

    def validate_loc_vicgrid(self, value):
        if not isinstance(value, (list, tuple)):
            raise serializers.ValidationError("loc_vicgrid must be a list or tuple")
        if len(value) != 2:
            raise serializers.ValidationError("loc_vicgrid must contain exactly two integers")
        return value
    
    def validate_pixels(self, value):
        if not isinstance(value, (list, tuple)):
            raise serializers.ValidationError("pixels must be a list or tuple")
        if len(value) != 2:
            raise serializers.ValidationError("pixels must contain exactly two integers")
        return value

    def validate_is_production_pump(self, value):
        if value.lower() not in ['true', 'false']:
            raise serializers.ValidationError("is_production_pump must be 'true' or 'false'")
        return value.lower() == 'true'
    

# class DepthQuerySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DepthQuery
#         fields = '__all__'

# class DepthProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DepthProfileModel
#         fields = '__all__'

# class DepthLayerSerializer(serializers.ModelSerializer):
#     profile = DepthProfileSerializer(read_only=True)
#     profile_id = serializers.PrimaryKeyRelatedField(
#         queryset=DepthProfileModel.objects.all(),
#         source='profile',
#         write_only=True
#     )
#     class Meta:
#         model = DepthLayerModel
#         fields = '__all__'

# class UserInputModelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserInputModel
#         fields = '__all__'