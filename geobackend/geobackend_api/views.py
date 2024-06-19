from django.shortcuts import render

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
# Create your views here.
from geodrillcalc import geodrillcalc as gdc
import pandas as pd
import numpy as np

from .models import *
from .serializers import *


class WellboreCalculationView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data

        # extract parameters from request
        is_production_pump = data["is_production_pump"]
        depth_data = data["depth_data"]
        initial_input_values = data["initial_input_values"]

        # convert depth data to pandas dataframe
        depth_data_df = pd.DataFrame(depth_data)


        # initialize and use the calculation object
        geo_interface = gdc.GeoDrillCalcInterface()
        result_wbd = geo_interface.calculate_and_return_wellbore_parameters(
            is_production_pump=is_production_pump,
            depth_data=depth_data_df,
            initial_input_data=initial_input_values
        )

        # #retrieve the result as dictionary
        results = geo_interface.export_results_to_dict()
        print(results)
        #results = results.replace(np.nan, None) #np.nan not serializable
        #results = results.to_json()
        # #store the results in the database
        # depth_query = DepthQuery(results)
        # depth_query.save()

        # #serialize and return the results
        # serializer = DepthQuerySerializer(depth_query)
        #print(results)
        
        return Response({'data':results}, status=status.HTTP_200_OK)
    

class DepthProfileViewSet(ModelViewSet):
    queryset = DepthProfileModel.objects.all()
    serializer_class = DepthProfileSerializer
    #permission_classes = []

class DepthLayerViewSet(ModelViewSet):
    queryset = DepthLayerModel.objects.select_related('profile').all()
    serializer_class = DepthLayerSerializer


@api_view(['GET'])
def test_view(request):
    return Response({'message': 'ok'},
                    status=status.HTTP_200_OK)
