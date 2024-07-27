from pyproj import Transformer
import numpy as np
import requests
from bs4 import BeautifulSoup
import urllib
import re

from .reference_data import *


def get_bbox_params(coordinates, min_resolution:int|float=100, pixels=(100,100), crs_type:str='wgs84' ):
    """
    transforms provided coordinates into web mercator coordinate system
    and returns the bbox range as a string
    
    inputs: coorindates:tuple or list, 
    crs_type(string), 
    minimum resolution of the queried data in metre
    pixels: (width, height) as tuple
    output: 
    f'{bbox_xy}'.strip('()')
    """
    x, y = Transformer.from_crs(crs_type, 'epsg:3857').transform(*coordinates) #EPSG:3857 for mercator
    incre = np.array(pixels) * min_resolution / 2
    bbox_xy =x-incre[0], y-incre[1], x+incre[0], y+incre[1]
    return f'{bbox_xy}'.strip('()'), *_get_bbox_pixel_params(pixels)

def _get_bbox_pixel_params(pixels):
    """
    pixels = (100,100)
    returns width, height, x, y = get_bbox_params(pixels)
    """
    return *pixels, int(pixels[0] / 2), int(pixels[1] / 2)


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

    response = requests.get(url)    
    return response


def parse_wms_layers(response:requests.Response) -> list:
    soup = BeautifulSoup(response.text, 'html.parser')
    if response.status_code == 200:
        layers = sorted([code.text.lower() for code in soup.find_all('div',class_='aquifer-id')])
        layers += ['114bse'] #basement layer at the bottom
        return layers
    else:
        raise requests.exceptions.HTTPError(f"Error: {response.status_code}, {response.text}")
    

def stringify_layers(layers:list):
    prefix, suffix = 'vaf_', '_group'
    keys = list(vaf_mapping)
    keys.pop(14)
    layers_as_string = ",".join([ prefix+layer+suffix for layer in layers])
    return layers_as_string


def wms_aquifer_info_request(layer_string:str, bbox_params):
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
    response = requests.get(url)
    return response


def parse_layer_info(response):
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(f"Error: {response.status_code}, {response.text}")
    data = {}
    soup = BeautifulSoup(response.text)
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
                    data[layer_code][field] = float(value)
    return data


def format_data_depth_table(layer_data:list):
    layer_dict = {'aquifer_layer':[],
                "is_aquifer":[],
                "depth_to_base":[]}
    for key, item in layer_data.items():
        layer_dict['aquifer_layer'].append(key)
        layer_dict['is_aquifer'].append(is_aquifer[key])
        depth = (item['Aqdepth'] if 'Aqdepth' in item else 0) + (item['Thickness'] if 'Thickness' in item else 200)
        layer_dict['depth_to_base'].append(depth)
    return layer_dict