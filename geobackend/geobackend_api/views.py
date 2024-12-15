from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle
import logging


from .models import *
from .serializers import *
# from .utils.data_fetch_utils import generate_formatted_depth_data, fetch_watertable_depth
from .utils.serialization_utils import GeoDjangoJSONEncoder

from .services.calculation_service import perform_wellbore_calculation
from .services.data_fetch_service import fetch_depth_data_and_watertable

import json


logger = logging.getLogger(__name__)


class WellBoreCalcView(APIView):
    throttle_classes = [AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        data = request.data
        session_key = self.get_or_create_session_key(request=request)
        depth_data = {}  # initialise depth data
        logger.info(f"Session {session_key} - Received data: {data}")

        # stage 1. validate the user input
        serializer = UserInputSerializer(data=data)
        if not serializer.is_valid():
            logger.error(
                f"Session {session_key} - User input validation failed: {serializer.errors}")
            return self.create_response(message="Invalid input data.",
                                        details=serializer.errors,
                                        status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        # stage 2. fetch WMS aquifer/groundwater data
        coordinates = validated_data['coordinates']
        crs_type = validated_data['crs_type']
        min_resolution = validated_data['min_resolution']
        pixels = validated_data['pixels']
        initial_input_values = validated_data['initial_input_values']
        is_production_pump = validated_data['is_production_pump']

        # query WMS data
        try:
            depth_data, watertable_depth = fetch_depth_data_and_watertable(coordinates=coordinates,
                                                                           min_resolution=min_resolution,
                                                                           pixels=pixels,
                                                                           crs_type=crs_type)
            logger.info(
                f"Session {session_key} - Fetched depth data and watertable depth")
            logger.info(
                depth_data)
            logger.info(f"watertable depth: {watertable_depth} m")
        except Exception as e:
            # logger.error(
            #     f"Session {session_key} - Error fetching WMS data: {e}")
            return self.create_response(message="Error fetching data.",
                                        details=str(e),
                                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # logger.info(f'Session {session_key} - {depth_data}')
        # logger.info(f'Session {session_key} - WMS depth: {watertable_depth}')

        # stage 3. validate calculation input
        initial_input_values['groundwater_depth'] = watertable_depth
        initial_input_values['top_aquifer_layer'] = depth_data['aquifer_layer'][0]

        # lower tertiary aquifer
        initial_input_values['target_aquifer_layer'] = '111lta'

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
                data={"aquifer_table": depth_data},
                details=calculation_input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)

        try:
            results = perform_wellbore_calculation(
                is_production_pump, depth_data, initial_input_values)
            logger.info(f"Session {session_key} - Calculation successful.")
        except ValueError as e:
            return self.create_response(
                message='Error during calculation:\n',
                data={"aquifer_table": depth_data},
                details=str(e),
                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return self.create_response('An error occurred during calculation.',
                                        data={"aquifer_table": depth_data},
                                        details=str(e),
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
                                    data={
                                        "aquifer_table": depth_data,
                                        "installation_results": results.get("installation_results"),
                                        "cost_results": results.get("cost_results")
                                    },
                                    status=status.HTTP_200_OK)

    def get_or_create_session_key(self, request):
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key

    def create_response(self,
                        message,
                        data=None,
                        details=None,  # metadata or error details
                        status=status.HTTP_200_OK,
                        # is_data=False):
                        ):
        return Response({
            'message': message,
            'data': data,
            'details': details,
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
        results = perform_wellbore_calculation(
            is_production_pump, depth_data, initial_input_values)
        json_results = json.dumps(results, cls=GeoDjangoJSONEncoder)
        # Save the results to the model

        session_key = request.session.session_key
        _, created = WellBoreCalculationResult.objects.update_or_create(
            session_key=session_key, result_data=json_results)
        logging.info(
            f"{'Created' if created else 'Updated'} WellBoreCalculationResult results for {session_key}")

        return Response({'data': results}, status=status.HTTP_200_OK)
