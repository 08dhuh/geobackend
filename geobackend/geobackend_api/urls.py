from django.urls import path
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
# router.register('depth-profile', views.DepthProfileViewSet)
# router.register('depth-layer', views.DepthLayerViewSet)

urlpatterns = [
    path('calculate-wellbore', WellBoreCalcView.as_view()),
    path('calculate-profile', WellboreCalculationView.as_view()),

] 

#include router urls
urlpatterns += router.urls