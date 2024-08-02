from rest_framework import serializers
#from .models import *

class UserProvidedInitialInputValuesSerializer(serializers.Serializer):
    required_flow_rate = serializers.FloatField()
    hydraulic_conductivity = serializers.FloatField()
    average_porosity = serializers.FloatField()
    bore_lifetime_year = serializers.FloatField()
    long_term_decline_rate = serializers.FloatField()
    allowable_drawdown = serializers.FloatField()
    safety_margin = serializers.FloatField()

class UserInputSerializer(serializers.Serializer):
    coordinates = serializers.ListField(
        child = serializers.FloatField(),
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
    initial_input_values = UserProvidedInitialInputValuesSerializer()
    is_production_pump = serializers.CharField(max_length=5)

    def validate_coordinates(self, value):
        if not isinstance(value, (list, tuple)):
            raise serializers.ValidationError("coordinates must be a list or tuple")
        if len(value) != 2:
            raise serializers.ValidationError("coordinates must contain exactly two numbers")
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
    

class DepthDataSerializer(serializers.Serializer):
    aquifer_layer = serializers.ListField(
        child=serializers.CharField(max_length=50)
    )
    is_aquifer = serializers.ListField(
        child=serializers.BooleanField()
    )
    depth_to_base = serializers.ListField(
        child=serializers.FloatField()
    )

class InitialInputSerializer(serializers.Serializer):
    required_flow_rate = serializers.FloatField()
    hydraulic_conductivity = serializers.FloatField()
    average_porosity = serializers.FloatField()
    bore_lifetime_year = serializers.FloatField()
    groundwater_depth = serializers.FloatField()
    long_term_decline_rate = serializers.FloatField()
    allowable_drawdown = serializers.FloatField()
    safety_margin = serializers.FloatField()
    target_aquifer_layer = serializers.CharField(max_length=50)
    top_aquifer_layer = serializers.CharField(max_length=50)
    

class CalculationInputSerializer(serializers.Serializer):
    depth_data = DepthDataSerializer()
    initial_input_values = InitialInputSerializer()
    is_production_pump = serializers.BooleanField()

    def validate(self, data):
        depth_data = data.get('depth_data')
        if not all(len(depth_data['aquifer_layer']) == len(depth_data[key]) for key in depth_data):
            raise serializers.ValidationError("All depth_data lists must have the same length.")
        return data




# class WellBoreCalcInputSerializer(serializers.Serializer):
#     coordinates = serializers.ListField(
#         child = serializers.FloatField(),
#         min_length = 2,
#         max_length = 2
#     )
#     crs_type = serializers.CharField(max_length = 255)
#     min_resolution = serializers.IntegerField()
#     pixels = serializers.ListField(
#         child = serializers.IntegerField(),
#         min_length = 2,
#         max_length = 2
#     )
#     initial_input_values = InitialInputSerializer()
#     is_production_pump = serializers.CharField(max_length=5)

#     def validate_coordinates(self, value):
#         if not isinstance(value, (list, tuple)):
#             raise serializers.ValidationError("coordinates must be a list or tuple")
#         if len(value) != 2:
#             raise serializers.ValidationError("coordinates must contain exactly two numbers")
#         return value
    
#     def validate_pixels(self, value):
#         if not isinstance(value, (list, tuple)):
#             raise serializers.ValidationError("pixels must be a list or tuple")
#         if len(value) != 2:
#             raise serializers.ValidationError("pixels must contain exactly two integers")
#         return value

#     def validate_is_production_pump(self, value):
#         if value.lower() not in ['true', 'false']:
#             raise serializers.ValidationError("is_production_pump must be 'true' or 'false'")
#         return value.lower() == 'true'
    
