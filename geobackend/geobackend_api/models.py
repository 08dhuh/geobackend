from django.db import models
#from django.contrib.gis.db import models as gis_models
# Create your models here.

# class DepthQuery(models.Model):
#     query_time = models.DateTimeField(auto_now_add=True)
#     results = models.JSONField()

#     def __str__(self) -> str:
#         return f'Query at {self.query_time}'
    

# class DepthProfileModel(models.Model):
#     profile_name = models.CharField(max_length=100)
#     create_at = models.DateTimeField(auto_now_add=True)
#     def __str__(self):
#         return self.profile_name

# class DepthLayerModel(models.Model):
#     profile = models.ForeignKey(DepthProfileModel, related_name='layers', on_delete=models.CASCADE)
#     aquifer_layer = models.CharField(max_length=100)
#     is_aquifer = models.BooleanField(null=True, blank=True)
#     depth_to_base = models.FloatField(null=True, blank=True)

#     def __str__(self):
#         return f"{self.profile} : {self.aquifer_layer}"


# class UserInputModel(models.Model):
#     required_flow_rate = models.FloatField( verbose_name="Required Flow Rate (L/day)", help_text="The required flow rate in liters per day.")
#     hydraulic_conductivity = models.FloatField( verbose_name="Hydraulic Conductivity (m/day)", help_text="The hydraulic conductivity of the aquifer in meters per day.")
#     average_porosity = models.FloatField( verbose_name="Average Porosity", help_text="The average porosity of the aquifer (0-1).")
#     bore_lifetime_year = models.FloatField(verbose_name="Bore Lifetime (Years)", help_text="The expected lifetime of the bore in years.")
#     groundwater_depth = models.FloatField( verbose_name="Groundwater Depth (m)", help_text="The depth to the groundwater table in meters.")
#     long_term_decline_rate = models.FloatField( verbose_name="Long Term Decline Rate (m/year)", help_text="The long-term decline rate of the water level in meters per year.")
#     allowable_drawdown = models.FloatField(verbose_name="Allowable Drawdown (m)", help_text="The allowable drawdown in meters.")
#     safety_margin = models.FloatField(verbose_name="Safety Margin (m)", help_text="The safety margin in meters.")

#     def __str__(self):
#         return f"User Input {self.pk}"