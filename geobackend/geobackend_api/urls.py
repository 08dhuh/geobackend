from django.urls import path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register('depth-profile', views.DepthProfileViewSet)
router.register('depth-layer', views.DepthLayerViewSet)

urlpatterns = [
    path('calculate-profile', views.WellboreCalculationView.as_view()),

] 

#include router urls
urlpatterns += router.urls