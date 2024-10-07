from django.core.serializers.json import DjangoJSONEncoder

import numpy as np
import pandas as pd


class GeoDjangoJSONEncoder(DjangoJSONEncoder):
    """
    Helper class for converting python objects to JSON
    """

    def default(self, obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return np.asscalar(obj)
        return super().default(obj)



def check_calculation_feasibility(layer_dict:dict):
    # TODO: implement check
    layers = layer_dict['aquifer_layer']
    if len(layers) == 0:
        return False, {'message': 'Aquifer layer data is empty'}
    top_layer = layers[0]
    if top_layer not in ['100qa', '102utqa']:
        return False, {'message': f'Top layer is {top_layer}, not an aquifer layer.'}
    # TODO: change this logic later: target layer
    # target_layer = next((layer for layer in ('109lmta', '111lta') if layer in layers),
    #                     False)
    target_layer = '111lta' if '111lta' in layers else False

    if not target_layer:
        return False, {'message': 'Target layers not present in the layer list'}
    return True, {'top_aquifer_layer': top_layer, 'target_aquifer_layer': target_layer}
