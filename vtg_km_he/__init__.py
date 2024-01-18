import pandas as pd
import numpy as np
from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client, data

@algorithm_client
def master(client, time_column, censor_column, organization_ids=None):
    """Compute Kaplan-Meier curve in a federated environment.

    Parameters:
    - client: Vantage6 client object
    - time_column: Name of the column representing time
    - censor_column: Name of the column representing censoring
    - organization_ids: List of organization IDs to include (default: None, includes all)

    Returns:
    - Dictionary containing Kaplan-Meier curve and local event tables
    """
    info('Collecting information on participating organizations')
    if not isinstance(organization_ids, list):
        organizations = client.organization.list()
        ids = [organization.get("id") for organization in organizations]
    else:
        ids = organization_ids
    info(f'Sending task to organizations {ids}')

    km, local_event_tables = calculate_km(
        client=client,
        ids=ids,
        time_column=time_column,
        censor_column=censor_column)
    return {'kaplanMeier': km.to_json(), 'local_event_tables': [t.to_json() for t in local_event_tables]}


def calculate_km(client, ids, time_column, censor_column):
    """Calculate Kaplan-Meier curve and local event tables.

    Parameters:
    - client: Vantage6 client object
    - ids: List of organization IDs
    - time_column: Name of the column representing time
    - censor_column: Name of the column representing censoring

    Returns:
    - Tuple containing Kaplan-Meier curve (DataFrame) and local event tables (list of DataFrames)
    """
    info('Collecting unique event times')
    kwargs_dict = {'time_column': time_column}  
    method = 'get_unique_event_times'
    local_unique_event_times = launch_subtask(client, [method, kwargs_dict, ids])
    unique_event_times = {0}
    for local_unique_event_times in local_unique_event_times:
        unique_event_times |= set(local_unique_event_times)
    info(f'Collected unique event times for {len(local_unique_event_times)} organization(s)')

    info('Collecting local event tables')
    kwargs_dict = {'time_column': time_column, 'unique_event_times': list(unique_event_times), "censor_column": censor_column}  
    method = 'get_km_event_table'
    local_event_tables = launch_subtask(client, [method, kwargs_dict, ids])
    local_event_tables = [pd.read_json(event_table) for event_table in local_event_tables]
    info(f'Collected local event tables for {len(local_event_tables)} organization(s)')

    info('Aggregating event tables')
    km = pd.concat(local_event_tables).groupby(time_column, as_index=False).sum()
    km['Hazard'] = km['Deaths'] / km['AtRisk']
    km['Surv'] = (1 - km['Hazard']).cumprod()
    km['cdf'] = 1 - km['Surv']
    km['pmf'] = np.diff(km['cdf'], prepend=0)
    info('Kaplan-Meier curve has been computed successfully')
    return km, local_event_tables

@data(0)
def get_unique_event_times(df: pd.DataFrame, *args, **kwargs):
    """Get unique event times from a DataFrame.

    Parameters:
    - df: Input DataFrame
    - kwargs: Additional keyword arguments, including time_column

    Returns:
    - List of unique event times
    """
    time_column = kwargs.get("time_column")
    return df[time_column].unique().tolist()

@data(1)
def get_km_event_table(df: pd.DataFrame, *args, **kwargs):
    """Calculate death counts, total counts, and at-risk counts at each unique event time.

    Parameters:
    - df: Input DataFrame
    - kwargs: Additional keyword arguments, including time_column, unique_event_times, and censor_column

    Returns:
    - JSON-formatted string representing the calculated event table
    """
    info(f"Sample size {str(len(df))}")
    
    # parse kwargs
    time_column = kwargs.get("time_column", "T")  
    unique_event_times = kwargs.get("unique_event_times")
    censor_column = kwargs.get("censor_column", "C") 
    
    # Calculate death counts at each unique event time
    death = df.groupby(time_column, as_index=False).sum().rename(columns={censor_column: 'Deaths'})[[time_column, 'Deaths']]
    death = pd.DataFrame(unique_event_times, columns=[time_column]).merge(death, on=time_column, how='left').fillna(0)
    
    # Calculate total counts at each unique event time
    total = df.groupby(time_column, as_index=False).count().rename(columns={censor_column: 'Total'})[[time_column, 'Total']]
    total = pd.DataFrame(unique_event_times, columns=[time_column]).merge(total, on=time_column, how='left').fillna(0)
    
    # Merge death and total DataFrames on the time column
    km = death.merge(total, on=time_column)
    
    # Calculate "at-risk" counts at each unique event time and merge with km DataFrame
    return km.merge(
        pd.DataFrame.from_dict({
            unique_event_times[i]: len(df[df[time_column] >= unique_event_times[i]]) for i in range(len(unique_event_times))
        }, orient='index').rename(columns={0: 'AtRisk'}).sort_index(),
        left_on=time_column,
        right_index=True
    ).to_json()


def launch_subtask(client, task_info):
    """Launch a subtask to organizations and wait for results.

    Parameters:
    - client: Vantage6 client object
    - task_info: List containing method, kwargs_dict, and organization IDs

    Returns:
    - Results obtained from organizations
    """
    method, kwargs_dict, ids = task_info
    info(f'Sending task to organizations {ids}')
    task = client.task.create(
        input_={
            'method': method,
            'kwargs': kwargs_dict
        },
        organizations=ids
    )
    info("Waiting for results")
    results = client.wait_for_results(task_id=task.get("id"), interval=1)
    info(f"Results obtained for {method}!")
    return results
