from django.shortcuts import render
# DRF
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from geodrillcalc import geodrillcalc as gdc
import pandas as pd

from .models import *
from .serializers import *
from .utils import process_depth_data, check_feasibility, GeoDjangoJSONEncoder, generate_cache_key

import json
import logging


logger = logging.getLogger('geobackend_api')


class WellBoreCalcView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        if not request.session.session_key:
            request.session.create()

        # validate and extract parameters from request
        serializer = WellBoreCalcInputSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            coodinates = validated_data['coordinates']
            crs_type = validated_data['crs_type']
            min_resolution = validated_data['min_resolution']
            pixels = validated_data['pixels']
            initial_input_values = validated_data['initial_input_values']
            is_production_pump = validated_data['is_production_pump']

            # query WMS data
            depth_data = process_depth_data(coodinates,
                                            min_resolution,
                                            pixels,
                                            crs_type)

            # check if the calculation can be performed on the queried data
            is_feasible, response_feasible = check_feasibility(depth_data)
            if not is_feasible:
                return Response(response_feasible,
                                status=status.HTTP_400_BAD_REQUEST)

            # update and validate initial_input_values object
            initial_input_values['top_aquifer_layer'] = response_feasible['top_aquifer_layer']
            initial_input_values['target_aquifer_layer'] = response_feasible['target_aquifer_layer']

            input_serializer = InitialInputSerializer(
                data=initial_input_values)
            if not input_serializer.is_valid():
                return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # convert depth data to pandas dataframe
            depth_data_df = pd.DataFrame(depth_data)

            # initialize and use the calculation object
            geo_interface = gdc.GeoDrillCalcInterface()
            geo_interface.calculate_and_return_wellbore_parameters(
                is_production_pump=is_production_pump,
                depth_data=depth_data_df,
                initial_input_data=initial_input_values
            )
            results = geo_interface.export_results_to_dict()
            json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)


            # Save the results to the model
            session_key = request.session.session_key
            _, created = WellBoreCalculationResult.objects.update_or_create(
                session_key=session_key, result_data=json_results)
            logging.info(f"{'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")

            return Response({'message': 'Calculation successful',
                             'data': results}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TestWellboreCalculationView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        if not request.session.session_key:
            request.session.create()

        # extract parameters from request
        is_production_pump = data["is_production_pump"]
        depth_data = data["depth_data"]
        initial_input_values = data["initial_input_values"]

        # convert depth data to pandas dataframe
        depth_data_df = pd.DataFrame(depth_data)

        # initialize and use the calculation object
        geo_interface = gdc.GeoDrillCalcInterface()
        geo_interface.calculate_and_return_wellbore_parameters(
            is_production_pump=is_production_pump,
            depth_data=depth_data_df,
            initial_input_data=initial_input_values
        )

        # #retrieve the result as dictionary
        results = geo_interface.export_results_to_dict()
        json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)
        # Save the results to the model


        session_key = request.session.session_key
        _, created = WellBoreCalculationResult.objects.update_or_create(
            session_key=session_key, result_data=json_results)
        logging.info(f"{'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")
        

        return Response({'data': results}, status=status.HTTP_200_OK)
