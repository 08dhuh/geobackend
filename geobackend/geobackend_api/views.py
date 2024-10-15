from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle

import geodrillcalc.geodrillcalc_interface as gdc
import pandas as pd

from .models import *
from .serializers import *
from .wms_requests import generate_formatted_depth_data, fetch_watertable_depth
from .utils import GeoDjangoJSONEncoder

import json
import logging


logger = logging.getLogger('geobackend_api')


class WellBoreCalcView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data
        if not request.session.session_key:
            request.session.create()
        logging.info(f"Received data: {data}")
        serializer = UserInputSerializer(data=data)
        if not serializer.is_valid():
            logging.error("User input validation failed: {serializer.errors)")
            return Response({
                'message': 'Invalid input data.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        coodinates = validated_data['coordinates']
        crs_type = validated_data['crs_type']
        min_resolution = validated_data['min_resolution']
        pixels = validated_data['pixels']
        initial_input_values = validated_data['initial_input_values']
        is_production_pump = validated_data['is_production_pump']

        # query WMS data
        depth_data = generate_formatted_depth_data(coodinates,
                                                   min_resolution,
                                                   pixels,
                                                   crs_type)
        watertable_depth = fetch_watertable_depth(coodinates,
                                                  min_resolution,
                                                  pixels,
                                                  crs_type)

        logging.info(depth_data)
        logging.info(f'WMS depth: {watertable_depth}')

        # TODO: move this into gdc package
        # is_feasible, response_feasible = check_calculation_feasibility(
        #     depth_data)
        # if not is_feasible:
        #     logging.error(
        #         f"Calculation feasibility check failed")
        #     return Response({
        #         'message': 'Calculation cannot be performed at the selected location.',
        #         'details': response_feasible
        #     }, status=status.HTTP_400_BAD_REQUEST)

        initial_input_values['groundwater_depth'] = watertable_depth
        initial_input_values['top_aquifer_layer'] = depth_data['aquifer_layer'][0]
        # lower tertiary aquifer
        initial_input_values['target_aquifer_layer'] = '111lta'

        # serialize and validate the input
        calculation_input_serializer = CalculationInputSerializer(
            data={
                "is_production_pump": is_production_pump,
                "depth_data": depth_data,
                "initial_input_values": initial_input_values,
            }
        )
        if not calculation_input_serializer.is_valid():
            logging.error(
                f"Calculation input serialization failed: {calculation_input_serializer.errors}")
            return Response({
                'message': 'Failed serialization.',
                'details': calculation_input_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        depth_data_df = pd.DataFrame(depth_data)

        logging.info(depth_data)
        logging.info(initial_input_values)

        # initialise the calculation module
        geo_interface = gdc.GeoDrillCalcInterface()

        try:
            geo_interface.calculate_and_return_wellbore_parameters(
                is_production_well=is_production_pump,
                aquifer_layer_table=depth_data_df,
                initial_input_params=initial_input_values
            )
        except ValueError as e:
            logging.error(f"Validation error in geodrillcalc: {e}")
            return Response({
                'message': 'Error during calculation:\n',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'message': 'An error occurred during calculation.',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # TODO: save the depth data as well

        # TODO: exporting the results to dict format
        results = geo_interface.export_results_to_dict()
        json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)

        # Save the results to the model
        session_key = request.session.session_key
        _, created = WellBoreCalculationResult.objects.update_or_create(
            session_key=session_key, result_data=json_results)
        logging.info(
            f"{'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")

        return Response({'message': 'Calculation successful',
                         'data': results}, status=status.HTTP_200_OK)


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
            is_production_well=is_production_pump,
            aquifer_layer_table=depth_data_df,
            initial_input_params=initial_input_values
        )

        # #retrieve the result as dictionary
        results = geo_interface.export_results_to_dict()
        json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)
        # Save the results to the model

        session_key = request.session.session_key
        _, created = WellBoreCalculationResult.objects.update_or_create(
            session_key=session_key, result_data=json_results)
        logging.info(
            f"{'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")

        return Response({'data': results}, status=status.HTTP_200_OK)
