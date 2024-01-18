import time
from vantage6.algorithm.tools.util import info
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.decorators import algorithm_client, data
from itertools import product
import pandas as pd
import numpy as np
import math

from .utils import numpy_array_to_json, json_to_numpy_array

@algorithm_client
def master(client, time_col, censor_col, organization_ids=None):
    """This package does the following:
            2. Calculates the coordinates of the Kaplan Meier curve
    """

    info('Collecting participating organizations')
    if isinstance(organization_ids, list) is False:
        organizations = client.organization.list()
        ids = [organization.get("id") for organization in organizations]
    else:
        ids = organization_ids

    info(f'sending task to organizations {ids}')

    print("CLIENT: ", client)
    km,local_event_tables = calculate_KM(client=client, ids=ids, time_col=time_col, censor_col=censor_col)
    print(km, local_event_tables)
    return {'kaplanMeier': km.to_json(), 'local_event_tables': [t.to_json() for t in local_event_tables]}


def calculate_KM(client, ids, time_col, censor_col):

    info('Collecting unique event times')
    kwargs_dict = {'time_col': time_col}  
    method = 'get_unique_event_times'
    unique_event_times_aggregated = launch_subtask(client, [method, kwargs_dict, ids])
    info(f'Collected unique event times for {len(unique_event_times_aggregated)} organization(s)')

    local_uet = []
    for site_unique_event_times in unique_event_times_aggregated:
        local_uet.append(json_to_numpy_array(site_unique_event_times))

    local_uet.append([0])
    unique_event_times = list(set([item for sublist in local_uet for item in sublist]))

    ##### 2) Ask to calculate local event tables #####

    kwargs_dict = {'time_col': time_col, 'unique_event_times': unique_event_times, "censor_col": censor_col}  
    method = 'get_km_event_table'
    results = launch_subtask(client, [method, kwargs_dict, ids])

    local_event_tables = []
    for output in results:
        local_event_tables.append(pd.read_json(output['event_table']))

    km = pd.concat(local_event_tables).groupby(time_col, as_index=False).sum()
    km['Hazard'] = km['Deaths'] / km['AtRisk']
    km['Surv'] = (1 - km['Hazard']).cumprod()
    km['cdf'] = 1 - km['Surv']
    km['pmf'] = np.diff(km['cdf'], prepend=0)
    return km, local_event_tables

@data(0)
def get_unique_event_times(df: pd.DataFrame, *args, **kwargs):#, data_set, filt, median_lp):
    """Get Unique Event Times
    """
    time_col = kwargs.get("time_col")
    unique_event_times = df[time_col].unique()
    print(type(unique_event_times))
    #df = data_selector(data, data_set,filt, median_lp) #data_set, filt=None, median_lp=None)
    return numpy_array_to_json(unique_event_times)

@data(1)
def get_km_event_table(df: pd.DataFrame, *args, **kwargs):


    # parse kwargs
    time_col = kwargs.get("time_col", "T")
    unique_event_times = kwargs.get("unique_event_times")
    censor_col = kwargs.get("censor_col", "C")

    df = df.copy()
    
    info(str(len(df)))
    death = df.groupby(time_col, as_index=False).sum().rename(columns={'C': 'Deaths'})[[time_col, 'Deaths']]
    death = pd.DataFrame(unique_event_times, columns=[time_col]).merge(death, on=time_col, how='left').fillna(0)

    total = df.groupby(time_col, as_index=False).count().rename(columns={'C': 'Total'})[[time_col, 'Total']]
    total = pd.DataFrame(unique_event_times, columns=[time_col]).merge(total, on=time_col, how='left').fillna(0)

    km = death.merge(total, on=time_col)

    km = km.merge(pd.DataFrame.from_dict({unique_event_times[i]: len(df[df[time_col] >= unique_event_times[i]]) for
                                          i in range(len(unique_event_times))}, orient='index').rename(
        columns={0: 'AtRisk'}).sort_index(), left_on=time_col, right_index=True)
    return {'event_table': km.to_json()}

def launch_subtask(client, task_info):
    method, kwargs_dict, ids = task_info

    info(f'sending task to organizations {ids} with {kwargs_dict}')

    task = client.task.create(
        input_={
            'method': method,
            'kwargs': kwargs_dict
        },
        organizations=ids
    )

    # info("Waiting for results")
    # task_id = task.get("id")
    # task = client.get_task(task_id)
    # while not task.get("complete"):
    #     task = client.get_task(task_id)
    #     info("Waiting for results")
    #     time.sleep(1)
    # # Once we know the partials are complete, we can collect them.
    # info("Obtaining results")
    # results = client.get_results(task_id=task.get("id"))
    info("Waiting for results")
    results = client.wait_for_results(task_id=task.get("id"), interval=1)
    info(f"Results obtained for {task_info[0]}!")
    
    return results
