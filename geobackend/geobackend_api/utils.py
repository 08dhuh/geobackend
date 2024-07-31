from django.core.serializers.json import DjangoJSONEncoder

from pyproj import Transformer
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import urllib
import re

import logging
from .reference_data import *

# caching
import requests
import redis
import pickle
from hashlib import md5


# global variables
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_timeout = 3600*24  # 1 day
logger = logging.getLogger('geobackend_api')


class GeoDjangoJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return np.asscalar(obj)
        return super().default(obj)


def process_depth_data(coordinates, min_resolution: int | float = 100, pixels=(100, 100), crs_type: str = 'wgs84'):
    bbox_params = get_bbox_params(
        coordinates, min_resolution, pixels, crs_type)
    layer_request = wms_layer_request(bbox_params)
    layers = parse_wms_layers(layer_request)
    layers_as_string = stringify_layers(layers)
    depth_request = wms_aquifer_info_request(layers_as_string, bbox_params)
    layer_data = parse_layer_info(depth_request)
    formatted_depth_data = format_data_depth_table(layer_data)
    return formatted_depth_data


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


def generate_cache_key(params):
    # Generate a unique cache key based on the request parameters
    key_string = str(params)
    return md5(key_string.encode('utf-8')).hexdigest()


def load_or_get_results(url, params):
    cache_key = generate_cache_key(params)
    cached_result = redis_client.get(cache_key)
    if cached_result:
        logger.info(f'cache hit for {cache_key}')
        return pickle.loads(cached_result)
    try:
        response = requests.get(url)
        response.raise_for_status()
        redis_client.setex(cache_key, redis_timeout, pickle.dumps(response))
        return response
    except requests.exceptions.RequestException as e:
        logger.error(e)


def wms_layer_request(bbox_params):
    """
    bbox_params: bbox, width, height, x, y in order
    """
    bbox, width, height, x, y = bbox_params
    base_url = "https://geo.cerdi.edu.au/geoserver/vvg/wms"
    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetFeatureInfo",
        "layers": "vvg:vaf_primary_group",
        "query_layers": "vvg:vaf_outlines_3857",
        "styles": "",
        "bbox": bbox,
        "width": width,
        "height": height,
        "srs": "EPSG:3857",
        "format": "image/png",
        "info_format": "text/html",
        "x": x,
        "y": y,
        "FEATURE_COUNT": 50
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    # caching
    return load_or_get_results(url, params)
    # cache_key = generate_cache_key(params)

    # cached_result = redis_client.get(cache_key)
    # if cached_result:
    #     return pickle.loads(cached_result)

    # try:
    #     response = requests.get(url)
    #     response.raise_for_status()
    #     redis_client.setex(cache_key, 3600, pickle.dumps(response))
    #     return response
    # except requests.exceptions.RequestException as e:
    #     logger.error(e)


def parse_wms_layers(response: requests.Response) -> list:
    soup = BeautifulSoup(response.text, 'html.parser')
    if response.status_code == 200:
        layers = sorted([code.text.lower()
                        for code in soup.find_all('div', class_='aquifer-id')])
        layers += ['114bse']  # basement layer at the bottom
        return layers
    else:
        logger.error(f"Error in parse_wms_layers: {response.status_code}, {response.text}")
        raise requests.exceptions.HTTPError(
            f"Error: {response.status_code}, {response.text}")


def stringify_layers(layers: list):
    prefix, suffix = 'vaf_', '_group'
    keys = list(vaf_mapping)
    keys.pop(14)
    layers_as_string = ",".join([prefix+layer+suffix for layer in layers])
    return layers_as_string


def wms_aquifer_info_request(layer_string: str, bbox_params):
    """
    layer_string: stringified representation of the requested layers
    bbox_params: same params as wms_layer_request
    """
    bbox, width, height, x, y = bbox_params
    base_url = "https://geo.cerdi.edu.au/geoserver/vvg/wms"
    params = {
        "service": "WMS",
        "version": "1.1.1",
        "request": "GetFeatureInfo",
        "layers": layer_string,
        "query_layers": layer_string,
        "styles": "",
        "bbox": bbox,
        "width": width,
        "height": height,
        "srs": "EPSG:3857",
        "format": "image/png",
        "info_format": "text/html",
        "x": x,
        "y": y,
        "FEATURE_COUNT": 50
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    # caching
    return load_or_get_results(url, params)


def parse_layer_info(response):
    if response.status_code != 200:
        logger.error(f"Error in parse_layer_info: {response.status_code}, {response.text}")
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
                            logger.info(f"Aqdepth for {layer_code} is -9999, treating as 0")
                            float_value = 0
                        data[layer_code][field] = float_value
                    except ValueError:
                        logger.error(f"Could not convert {value} to float for {key}")
    return data


def format_data_depth_table(layer_data: list):
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


def check_feasibility(layer_dict):
    # TODO: implement check
    layers = layer_dict['aquifer_layer']
    if len(layers) == 0:
        return False, {'message': 'Aquifer layer is empty'}
    top_layer = layers[0]
    if top_layer not in ['100qa', '102utqa']:
        return False, {'message': 'Top layer is not aquifer'}
    # TODO: change this logic later
    target_layer = next((layer for layer in ('109lmta', '111lta') if layer in layers),
                        False)
    if not target_layer:
        return False, {'message': 'Target layers not present in the layer list'}
    return True, {'top_aquifer_layer': top_layer, 'target_aquifer_layer': target_layer}
