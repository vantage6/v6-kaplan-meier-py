import json
import numpy as np

def numpy_array_to_json(arr):
    if isinstance(arr, np.ndarray):
        return {
            '__numpy__': True,
            'dtype': str(arr.dtype),
            'data': arr.tolist(),
            'shape': arr.shape
        }
    else:
        return arr

def json_to_numpy_array(obj):
    if isinstance(obj, dict) and '__numpy__' in obj:
        return np.array(obj['data'], dtype=obj['dtype']).reshape(obj['shape'])
    else:
        return obj