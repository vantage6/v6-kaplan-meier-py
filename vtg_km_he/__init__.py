import numpy as np
import pandas as pd
from typing import Any, List, Dict, Tuple, Union
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client, data


@algorithm_client
def master(
    client: AlgorithmClient,
    time_column: str,
    censor_column: str,
    binning: bool = False,
    bins: dict = None,
    cohort_id: Union[int, str],
    query_string: str = None,
    organization_ids: List[int] = None
) -> Dict[str, Union[str, List[str]]]:
    """Compute Kaplan-Meier curve in a federated environment.

    Parameters:
    - client: Vantage6 client object
    - time_column: Name of the column representing time
    - censor_column: Name of the column representing censoring
    - binning: Simple KM or use binning to obfuscate events
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
        censor_column=censor_column,
        binning=binning,
        bins=bins
        cohort_id=cohort_id
    )
    return {'kaplanMeier': km.to_json(), 'local_event_tables': [t.to_json() for t in local_event_tables]}


def calculate_km(
    client: AlgorithmClient,
    ids: List[int],
    time_column: str,
    censor_column: str,
    binning: bool = False,
    bins: dict = None
    cohort_id: Union[int, str],
    query_string: str = None
) -> Tuple[pd.DataFrame, List[pd.DataFrame]]:
    """Calculate Kaplan-Meier curve and local event tables.

    Parameters:
    - client: Vantage6 client object
    - ids: List of organization IDs
    - time_column: Name of the column representing time
    - censor_column: Name of the column representing censoring
    - binning: Simple KM or use binning to obfuscate events

    Returns:
    - Tuple containing Kaplan-Meier curve (DataFrame) and local event tables (list of DataFrames)
    """
    info('Collecting unique event times')
    kwargs_dict = dict(time_column=time_column, cohort_id=cohort_id)
    method = 'get_unique_event_times'
    local_unique_event_times_aggregated = launch_subtask(client, [method, kwargs_dict, ids])
    unique_event_times = {0}
    for local_unique_event_times in local_unique_event_times_aggregated:
        unique_event_times |= set(local_unique_event_times)
    info(f'Collected unique event times for {len(local_unique_event_times_aggregated)} organization(s)')

    # Apply binning to obfuscate event times
    if binning:
        try:
            # Define bins for time events
            info('Binning unique times')
            unique_event_times = list(
                range(
                    0,
                    int(np.max(list(unique_event_times))+bins['size']),
                    bins['size']
                )
            )
            info(f'Unique times: {unique_event_times}')
        except Exception as e:
            info(f'Exception occurred with input \'bins\': {e}')

    info('Collecting local event tables')
    kwargs_dict = dict(
        time_column=time_column,
        unique_event_times=list(unique_event_times),
        censor_column=censor_column,
        binning=binning,
        cohort_id=cohort_id)
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
def get_unique_event_times(df: pd.DataFrame, *args, **kwargs) -> List[str]:
    """Get unique event times from a DataFrame.

    Parameters:
    - df: Input DataFrame
    - kwargs: Additional keyword arguments, including time_column

    Returns:
    - List of unique event times
    """
    time_column = kwargs.get("time_column")
    cohort_id = kwargs.get("cohort_id")
    return (
        df
        .query(f"COHORT_DEFINITION_ID == {cohort_id}")[time_column]
        .unique()
        .tolist())


@data(1)
def get_km_event_table(df: pd.DataFrame, *args, **kwargs) -> str:
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
    binning = kwargs.get("binning")
    cohort_id = kwargs.get("cohort_id")

    # Apply binning to obfuscate event times
    if binning:
        # Bin event time data
        info('Binning event times to compute tables')
        df[time_column] = np.float64(pd.cut(
            df[time_column], bins=unique_event_times,
            labels=unique_event_times[1:]
        ))
    

    # Filter the local dataframe with the query
    info(f"Overall number of patients: {df.shape[0]}")
    df = df.query(f"COHORT_DEFINITION_ID == {cohort_id}")
    info(f"Number of patients in the cohort #{cohort_id}: {df.shape[0]}")

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

def launch_subtask(
    client: AlgorithmClient,
    task_info: List[Any]
) -> List[Dict[str, Union[str, List[str]]]]:
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
