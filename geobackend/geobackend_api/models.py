from django.db import models
#from django.contrib.gis.db import models as gis_models
# Create your models here.


class WellBoreCalculationResult(models.Model):
    session_key = models.CharField(max_length=40)
    result_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Calculation result for session {self.session_key}"

