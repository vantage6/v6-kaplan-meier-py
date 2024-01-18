from vantage6.algorithm.tools.mock_client import MockAlgorithmClient
import vtg_km_he
import numpy as np
import warnings
import pandas as pd
warnings.filterwarnings("ignore")

# Initialize the mock server. The datasets simulate the local datasets from
# the node. In this case we have two parties having two different datasets:
# a.csv and b.csv. The module name needs to be the name of your algorithm
# package. This is the name you specified in `setup.py`, in our case that
# would be v6-correlation-matrix-py.
dataset_1 = {"database": "./vtg_km_he/local/data_test.csv", "db_type": "csv"}
dataset_2 = {"database": "./vtg_km_he/local/data_test.csv", "db_type": "csv"}
org_ids = ids = [0, 1]

client = MockAlgorithmClient(
    datasets = [[dataset_1], [dataset_2]],
    organization_ids=org_ids,
    module="vtg_km_he"
)

organizations = client.organization.list()
org_ids = ids = [organization["id"] for organization in organizations]

# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.task.create(
    input_={
        'master': 1,
        'method': 'master',
        'kwargs': {'time_col': 'T','censor_col':'C'}#,'data_set': 'all' } #'coef':[{'0': 0.1, '1': 0.2, '2': -0.1}]
    },
    organizations=[org_ids[0]]
)

results = client.result.get(average_task.get("id"))
results['kaplanMeier'] = pd.read_json(results['kaplanMeier'])
results['local_event_tables'] = [pd.read_json(value) for value in results['local_event_tables']]
try:
    results['kaplanMeier'].to_csv('pippo.csv')
except:
    results['kaplanMeierLR'].to_csv('pippo_lr.csv')
    results['kaplanMeierHR'].to_csv('pippo_hr.csv')

