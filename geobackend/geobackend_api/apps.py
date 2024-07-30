from django.apps import AppConfig


class GeobackendApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "geobackend_api"

    def ready(self):
        import geobackend_api.signals
