import time
from pyproj import Transformer
import numpy as np
import requests
import urllib
import re
from bs4 import BeautifulSoup
# caching
import redis
import pickle
from hashlib import md5

import logging
from .reference_data import *


# global variables
wms_request_dict = {
    'layers': {
        "version": "1.1.1",
        "layers": "vvg:vaf_primary_group",
        "query_layers": "vvg:vaf_outlines_3857",
    },
    'aquifer_info': {
        "version": "1.1.1",
    },
    'watertable_depth': {
        "version": "1.3.0",
        "layers": "vvg:vaf_depth_watertable_swl100_raw_3857",
        "query_layers": "vvg:vaf_depth_watertable_swl100_raw_3857",
    }
}
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_timeout = 3600*24  # 1 day

logging.basicConfig(
            filename='api_requests.log',
            level=logging.INFO, 
            format="%(asctime)s %(levelname)s %(message)s", 
            #datefmt="%H:%M:%S %d-%m-%Y")
            datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger('geobackend_api')

#exported methods
def generate_formatted_depth_data(coordinates, 
                                  min_resolution: int | float = 100, 
                                  pixels=(100, 100), 
                                  crs_type: str = 'wgs84'):
    try:
        bbox_params = get_bbox_params(
            coordinates, min_resolution, pixels, crs_type)
        layer_request = request_wms_layers(bbox_params)
        layers = parse_wms_layers(layer_request)
        layers_as_string = stringify_layers(layers)
        depth_request = request_wms_aquifer_info(layers_as_string, bbox_params)
        layer_data = parse_aquifer_info(depth_request)
        formatted_depth_data = format_data_depth_table(layer_data)
        return formatted_depth_data
    except Exception as e:
        logger.error(f"Error generating formatted depth data: {str(e)}")
        raise Exception(f"Error generating formatted depth data: {str(e)}")


def fetch_watertable_depth(coordinates, 
                         min_resolution: int | float = 100, 
                         pixels=(100, 100), 
                         crs_type: str = 'wgs84') -> float:
    try:
        bbox_params = get_bbox_params(
            coordinates, min_resolution, pixels, crs_type)
        wd_request = request_watertable_depth(bbox_params)
        return parse_watertable_depth(wd_request)
    except Exception as e:
        logger.error(f"Error retrieving watertable depth: {str(e)}")
        raise Exception(f"Error retrieving watertable depth: {str(e)}")
    

#requests
def load_or_get_results(url, params):
    cache_key = generate_cache_key(params)
    cached_result = redis_client.get(cache_key)
    # log reqeut start
    if cached_result:
        logger.info(f'cache hit for {cache_key}')
        return pickle.loads(cached_result)
    try:
        start_time = time.time()
        logger.info(f'Request started at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time))}.{int((start_time % 1) * 1000):03d}, url: {url}')
       
        #implement logging here
        
        response = requests.get(url)
        response.raise_for_status()
        
        end_time = time.time()
        logger.info(f'Request completed at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}.{int((end_time % 1) * 1000):03d}, url: {url}, status: {response.status_code}, time_taken: {end_time - start_time:.2f} seconds')

        return response
    except requests.exceptions.RequestException as e:
        logger.error(e)
        return {
            "status": "error",
            "error": {
                "message": str(e)
            }
        }
    finally:
        redis_client.setex(cache_key, redis_timeout, pickle.dumps(response))




def _request_wms(request_type: str, **request_params):
    """
    abstracted WMS request method
    request_type: 'layers', 'aquifer_info', 'watertable_depth'
    """
    params = generate_wms_request_params(**request_params,
                                         **wms_request_dict[request_type])
    url = generate_wms_request_url(params)
    return load_or_get_results(url, params)



def request_wms_layers(bbox_params):
    """
    bbox_params: bbox, width, height, x, y in order
    """
    return _request_wms('layers', bbox_params=bbox_params)



def request_wms_aquifer_info(layer_string: str, bbox_params) -> requests.Response:
    """
    layer_string: stringified representation of the requested layers
    bbox_params: same params as wms_layer_request
    """
    return _request_wms('aquifer_info', layers=layer_string, query_layers=layer_string, bbox_params=bbox_params)



def request_watertable_depth(bbox_params):
    return _request_wms('watertable_depth', bbox_params=bbox_params)


#parsing the request response
def parse_wms_layers(response: requests.Response) -> list:
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        layers = sorted([code.text.lower()
                        for code in soup.find_all('div', class_='aquifer-id')])
        layers += ['114bse']  # basement layer at the bottom
        return layers
    else:
        logger.error(
            f"Error in parse_wms_layers: {response.status_code}, {response.text}")
        raise requests.exceptions.HTTPError(
            f"Error: {response.status_code}, {response.text}")


def parse_aquifer_info(response: requests.Response) -> dict:
    if response.status_code != 200:
        logger.error(
            f"Error in parse_layer_info: {response.status_code}, {response.text}")
        raise requests.exceptions.HTTPError(
            f"Error: {response.status_code}, {response.text}")

    data = {}
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.find_all('div', class_='row')

    for row in rows:
        cols = row.find_all('div')
        if len(cols) == 2:
            key = cols[0].text.strip()
            value = cols[1].text.strip()

            match = re.match(r"(\w+)\s+(\d+)", key)
            if match:
                field, num_part = match.groups()
                if num_part in num_to_code_mapping:
                    layer_code = num_to_code_mapping[num_part]
                    if layer_code not in data:
                        data[layer_code] = {}
                    try:
                        # Handle the -9999 value
                        float_value = float(value.replace(',', ''))
                        if float_value == -9999:
                            logger.info(
                                f"Aqdepth for {layer_code} is -9999, treating as 0")
                            float_value = 0
                        data[layer_code][field] = float_value
                    except ValueError:
                        logger.error(
                            f"Could not convert {value} to float for {key}")
    return data


def parse_watertable_depth(response: requests.Response) -> float:
    if response.status_code != 200:
        logger.error(
            f"Error in parse_layer_info: {response.status_code}, {response.text}")
        raise requests.exceptions.HTTPError(
            f"Error: {response.status_code}, {response.text}")
    try:

        soup = BeautifulSoup(response.text, 'html.parser')
        depth_row = soup.find('td', string='Depth to watertable').find_next('td')
    

        match = re.search(r"(\d+\.?\d*)", depth_row.text)
        return float(match.group())
    except AttributeError as e:
        logger.error("AttributeError: Depth value not available")
        raise AttributeError("Error: Depth value not available") from e
    except ValueError as e:
        logger.error("ValueError: No numeric value found")
        raise ValueError("Error: No numeric value found") from e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise Exception("An unexpected error occurred") from e


#formatters and helpers
def generate_cache_key(params):
    # Generate a unique cache key based on the request parameters
    key_string = str(params)
    return md5(key_string.encode('utf-8')).hexdigest()


def get_bbox_params(coordinates, min_resolution: int | float = 100, pixels=(100, 100), crs_type: str = 'wgs84'):
    """
    transforms provided coordinates into web mercator coordinate system
    and returns the bbox range as a string

    inputs: coorindates:tuple or list, 
    crs_type(string), 
    minimum resolution of the queried data in metre
    pixels: (width, height) as tuple or list
    output: 
    f'{bbox_xy}'.strip('()')
    """
    x, y = Transformer.from_crs(crs_type, 'epsg:3857').transform(
        *coordinates)  # EPSG:3857 for mercator
    incre = np.array(pixels) * min_resolution / 2
    bbox_xy = x-incre[0], y-incre[1], x+incre[0], y+incre[1]
    return f'{bbox_xy}'.strip('()'), *_get_bbox_pixel_params(pixels)


def _get_bbox_pixel_params(pixels):
    """
    pixels = (100,100)
    returns width, height, x, y = get_bbox_params(pixels)
    """
    return *pixels, int(pixels[0] / 2), int(pixels[1] / 2)


def generate_wms_request_params(bbox_params,
                                layers,
                                query_layers,
                                request="GetFeatureInfo",
                                version="1.1.1",
                                feature_count=50):
    bbox, width, height, x, y = bbox_params
    params = {
        "service": "WMS",
        "version": version,
        "request": request,
        "layers": layers,
        "query_layers": query_layers,
        "styles": "",
        "bbox": bbox,
        "width": width,
        "height": height,
        "srs": "EPSG:3857",
        "format": "image/png",
        "info_format": "text/html",
        "x": x,
        "y": y,
        "FEATURE_COUNT": feature_count
    }
    return params


def generate_wms_request_url(params,
                             base_url="https://geo.cerdi.edu.au/geoserver/vvg/wms"):
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def stringify_layers(layers: list):
    prefix, suffix = 'vaf_', '_group'
    keys = list(vaf_mapping)
    keys.pop(14)
    layers_as_string = ",".join([prefix+layer+suffix for layer in layers])
    return layers_as_string


def format_data_depth_table(layer_data: list) -> dict:
    layer_dict = {'aquifer_layer': [],
                  "is_aquifer": [],
                  "depth_to_base": []}
    for key, item in layer_data.items():
        layer_dict['aquifer_layer'].append(key)
        layer_dict['is_aquifer'].append(is_aquifer[key])
        aquidepth = item.get('Aqdepth', 0)
        if aquidepth == -9999:
            aquidepth = 0  # ensure -9999 is treated as 0
        thickness = 200 if 'bse' in key else item.get(
            'Thickness', 0)  # basement thickness fixed at 200
        depth = aquidepth + thickness
        layer_dict['depth_to_base'].append(depth)
    return layer_dict


