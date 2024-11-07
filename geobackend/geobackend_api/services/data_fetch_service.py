import logging
from ..utils.data_fetch_utils import generate_formatted_depth_data, fetch_watertable_depth

logger = logging.getLogger(__name__)


def fetch_depth_data_and_watertable(coordinates, min_resolution, pixels, crs_type):
    """
    Fetches both depth data and watertable depth from WMS sources.
    """
    try:
        depth_data = generate_formatted_depth_data(
            coordinates, min_resolution, pixels, crs_type
        )
        watertable_depth = fetch_watertable_depth(
            coordinates, min_resolution, pixels, crs_type
        )
        #logger.info("Fetched depth data and watertable depth successfully.")
        return depth_data, watertable_depth
    except Exception as e:
        logger.error(f"Error fetching WMS data: {str(e)}")
        raise Exception("Error fetching WMS data") from e