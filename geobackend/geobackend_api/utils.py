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




