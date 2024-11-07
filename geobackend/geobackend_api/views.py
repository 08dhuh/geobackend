from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
import logging

import geodrillcalc.geodrillcalc_interface as gdc
import pandas as pd

from .models import *
from .serializers import *
from .wms_requests import generate_formatted_depth_data, fetch_watertable_depth
from .utils import GeoDjangoJSONEncoder

import json


logger = logging.getLogger(__name__)


class WellBoreCalcView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data
        session_key = self.get_or_create_session_key(request=request)

        logger.info(f"Session {session_key} - Received data: {data}")
        serializer = UserInputSerializer(data=data)
        if not serializer.is_valid():
            logger.error(
                f"Session {session_key} - User input validation failed: {serializer.errors}")
            return self.create_response("Invalid input data.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        coodinates = validated_data['coordinates']
        crs_type = validated_data['crs_type']
        min_resolution = validated_data['min_resolution']
        pixels = validated_data['pixels']
        initial_input_values = validated_data['initial_input_values']
        is_production_pump = validated_data['is_production_pump']

        # query WMS data
        try:
            depth_data = generate_formatted_depth_data(coodinates,
                                                       min_resolution,
                                                       pixels,
                                                       crs_type)
            watertable_depth = fetch_watertable_depth(coodinates,
                                                      min_resolution,
                                                      pixels,
                                                      crs_type)
            logger.info(
                f"Session {session_key} - Fetched depth data and watertable depth")
        except Exception as e:
            logger.error(
                f"Session {session_key} - Error fetching WMS data: {e}")
            return self.create_response("Error fetching data.", str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)
        # logger.info(f'Session {session_key} - {depth_data}')
        # logger.info(f'Session {session_key} - WMS depth: {watertable_depth}')

        initial_input_values['groundwater_depth'] = watertable_depth
        initial_input_values['top_aquifer_layer'] = depth_data['aquifer_layer'][0]
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
            logger.error(
                f"Session {session_key} - Calculation input serialization failed: {calculation_input_serializer.errors}")
            return self.create_response(
                message='Failed serialization.',
                details=calculation_input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        depth_data_df = pd.DataFrame(depth_data)

        # initialise the calculation module
        geo_interface = gdc.GeoDrillCalcInterface()

        try:
            geo_interface.calculate_and_return_wellbore_parameters(
                is_production_well=is_production_pump,
                aquifer_layer_table=depth_data_df,
                initial_input_params=initial_input_values
            )
            results = geo_interface.export_results_to_dict()
            logger.info(f"Session {session_key} - Calculation successful.")
        except ValueError as e:
            logger.error(
                f"Session {session_key} - Validation error in geodrillcalc: {e}")
            return self.create_response(
                message='Error during calculation:\n',
                details=str(e), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(
                f"Session {session_key} - Unexpected error in calculation.")
            return self.create_response('An error occurred during calculation.',
                                        str(e),
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                                        )

        # TODO: exporting the results to dict format
        json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)

        # Save the results to the model
        _, created = WellBoreCalculationResult.objects.update_or_create(
            session_key=session_key, result_data=json_results)

        logger.info(
            f"Session {session_key} - {'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")
        return self.create_response(message='Calculation successful',
                                    details=results,
                                    is_data=True)

    def get_or_create_session_key(self, request):
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    def create_response(self,
                        message,
                        details=None,
                        status=status.HTTP_200_OK,
                        is_data=False):
        return Response({
            'message': message,
            'data' if is_data else 'details': details
        }, status=status)


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
