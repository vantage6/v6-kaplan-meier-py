import os
import warnings
import vtg_km_he
import pandas as pd
from vantage6.tools.mock_client import ClientMockProtocol
warnings.filterwarnings("ignore")

# Partitioning data
data_dir = os.path.join(os.getcwd(), "vtg_km_he", "local")
data_path = os.path.join(data_dir, "data_test.csv")
data1_path = os.path.join(data_dir, "data1.csv")
data2_path = os.path.join(data_dir, "data2.csv")
if not os.path.exists(data1_path):
    df = pd.read_csv(data_path)
    df = df.sample(frac=1) # Shaffle data
    df[0:int(len(df)/2)].to_csv(data1_path)
    df[int(len(df)/2):].to_csv(data2_path)


# Initialize the mock server. The datasets simulate the local datasets from
# the node. In this case we have two parties having two different datasets:
# a.csv and b.csv. The module name needs to be the name of your algorithm
# package. This is the name you specified in `setup.py`, in our case that
# would be v6-correlation-matrix-py.
client = ClientMockProtocol(
    datasets=[os.path.join(data_dir, "data1.csv"),
              os.path.join(data_dir, "data2.csv")],
#    datasets=["./local/TR_Maastricht_data (1).csv", "./local/TR_Maastricht_data (1).csv"],
    module="vtg_km_he"
)


org_ids = ids = [1,2]



# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.create_new_task(
    input_={
        'master': 1,
        'method': 'master',
        'kwargs': {
            'time_col': 'T',
            'censor_col': 'C',
            'method': 'binning',
            'bins': {'maxtime': 92, 'size': 5}
        }
    },
    organization_ids=[org_ids[0]]
)

results = client.get_results(average_task.get("id"))
print(results)
df_km = results[0]['kaplanMeier']
try:
    results[0]['kaplanMeier'].to_csv('pippo.csv')
except:
    results[0]['kaplanMeierLR'].to_csv('pippo_lr.csv')
    results[0]['kaplanMeierHR'].to_csv('pippo_hr.csv')

