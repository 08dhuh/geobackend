from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from .models import WellBoreCalculationResult

@receiver(post_delete, sender=Session)
def delete_calculation_results(sender, instance, **kwargs):
    WellBoreCalculationResult.objects.filter(session_key=instance.session_key).delete()
