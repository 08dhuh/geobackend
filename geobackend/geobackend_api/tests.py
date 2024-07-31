from django.test import TestCase
import json
# Create your tests here.
from geodrillcalc import geodrillcalc as gdc
import pandas as pd

#loads input file
fname = 'inputs.json'
with open(fname, 'r') as f:
    obj = json.load(f)

is_production = True
depth_data = pd.DataFrame(obj.get('depth_data'))
initial_values = obj.get('initial_values')


#print(depth_data,'\n',initial_values)

#create gdc object
geo_interface = gdc.GeoDrillCalcInterface()
wbd = geo_interface.calculate_and_return_wellbore_parameters(
    is_production,
    depth_data,
    initial_values
)

with open('outputs.json', 'w') as output:
    json.dump(wbd.export_results_to_dict(to_json=True), output)