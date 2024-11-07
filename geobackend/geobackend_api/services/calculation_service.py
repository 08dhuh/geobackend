import pandas as pd
import geodrillcalc.geodrillcalc_interface as gdc
import logging

logger = logging.getLogger(__name__)

def perform_wellbore_calculation(is_production_pump,
                                 depth_data,
                                 initial_input_values):
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
        logger.info(f"Calculation successful.")
        return results
    except ValueError as e:
        logger.error(f"Validation error during calculation: {e}")
        raise ValueError("Calculation validation error.") from e

    except Exception as e:
        logger.exception("Unexpected error during calculation.")
        raise RuntimeError("Unexpected calculation error.") from e
