import numpy as np
import pandas as pd

from typing import Any, Callable, Dict, List, Tuple, Union
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.util import get_env_var, info, warn, error
from vantage6.algorithm.tools.decorators import data


def aggregate_unique_event_times(
        client: AlgorithmClient,
        ids: List[int],
        time_column_name: str,
        bin_size: int = None,
        filter_value: str = None
) -> List[int]:
    """Calculate Kaplan-Meier curve and local event tables.

    Parameters:
    - client: Vantage6 client object
    - ids: List of organization IDs
    - time_column_name: Name of the column representing time
    - bin_size: Simple KM or use binning to obfuscate events
    - filter_value: Value to be filtered in specified column, both from node configuration

    Returns:
    - List containing unique event times
    """
    method_kwargs = dict(
        time_column_name=time_column_name,
        filter_value=filter_value
    )
    method = 'get_unique_event_times'
    local_unique_event_times_aggregated = launch_subtask(client, method, ids, **method_kwargs)
    unique_event_times = {0}
    for local_unique_event_times in local_unique_event_times_aggregated:
        unique_event_times |= set(local_unique_event_times)
    info(f'Collected unique event times for {len(local_unique_event_times_aggregated)} organization(s)')

    # Apply binning to obfuscate event times
    if bin_size:
        info('Binning unique times')
        unique_event_times = list(range(
            0, int(max(unique_event_times)) + bin_size, bin_size
        ))
    return unique_event_times


def calculate_km(
    client: AlgorithmClient,
    ids: List[int],
    time_column_name: str,
    censor_column_name: str,
    bin_size: int = None,
    filter_value: str = None
) -> Tuple[pd.DataFrame, List[pd.DataFrame]]:
    """Calculate Kaplan-Meier curve and local event tables.

    Parameters:
    - client: Vantage6 client object
    - ids: List of organization IDs
    - time_column_name: Name of the column representing time
    - censor_column_name: Name of the column representing censoring
    - binning: Simple KM or use binning to obfuscate events

    Returns:
    - Tuple containing Kaplan-Meier curve (DataFrame) and local event tables (list of DataFrames)
    """
    info('Collecting unique event times')
    unique_event_times = aggregate_unique_event_times(
        client, ids, time_column_name, bin_size, filter_value
    )

    info('Collecting local event tables')
    method_kwargs = dict(
        time_column_name=time_column_name,
        unique_event_times=list(unique_event_times),
        censor_column_name=censor_column_name,
        bin_size=bin_size,
        filter_value=filter_value)
    method = 'get_km_event_table'
    local_event_tables = launch_subtask(client, method, ids, **method_kwargs)
    local_event_tables = [pd.read_json(event_table) for event_table in local_event_tables]
    info(f'Collected local event tables for {len(local_event_tables)} organization(s)')

    info('Aggregating event tables')
    km = pd.concat(local_event_tables).groupby(time_column_name, as_index=False).sum()
    km['hazard'] = km['observed'] / km['at_risk']
    km['survival_cdf'] = (1 - km['hazard']).cumprod()
    info('Kaplan-Meier curve has been computed successfully')
    return km


def filter_df(df: pd.DataFrame, filter_value: str) -> pd.DataFrame:
    """
    Filter a DataFrame based on a specified value for a column specified via
    node configuration.

    Parameters:
    - df: Input DataFrame
    - filter_value: Value to filter on the DataFrame using the specified column
    - [Env var] V6_FILTER_COLUMN: Name of the column to filter on
    - [Env var] V6_FILTER_VALUES_ALLOWED: Allowed values for the filter column

    Returns:
    - Filtered DataFrame
    """

    filter_column = get_env_var("V6_FILTER_COLUMN", default=False)
    if filter_column is False:
        error("Filtering requested, but no filter column is set in the node configuration."
              " Please set the V6_FILTER_COLUMN environment variable at the node.")
        raise ValueError("No filter column set")
    else:
        if filter_column not in df.columns:
            error(f"Filter column '{filter_column}' not found in dataset. "
                  f"Please check the column name and the dataset.")
            raise ValueError("Filter column not found in dataset")

    filters_allowed = get_env_var("V6_FILTER_VALUES_ALLOWED", default=False)
    if filters_allowed is False:
        warn("No limitations on filter values are set. All values are allowed.")
    else:
        # parse env var V6_FILTER_VALUES_ALLOWED
        filters_allowed = filters_allowed.split(',')

        if filter_value not in filters_allowed:
            error(f"Filter value '{filter_value}' is not allowed. "
                  f"Allowed values are: {', '.join(filters_allowed)}")
            raise ValueError("Filter value not allowed")

    # if type of filter_column is not string, convert it to string
    # TODO: this is a temporary solution, we need to handle other types
    if not pd.api.types.is_string_dtype(df[filter_column]):
        df[filter_column] = df[filter_column].astype(str)

    return df[df[filter_column] == str(filter_value)]


@data(1)
def get_unique_event_times(df: pd.DataFrame, time_column_name: str, filter_value: str = None) -> List[str]:
    """Get unique event times from a DataFrame.

    Parameters:
    - df: Input DataFrame
    - time_column_name: Name of the column representing time
    - filter_value: Value to filter on the DataFrame using node-configured column

    Returns:
    - List of unique event times
    """
    if filter_value:
        df = filter_df(df, filter_value)

    return df[time_column_name].unique().tolist()


@data(1)
def get_km_event_table(
    df: pd.DataFrame,
    time_column_name: str,
    censor_column_name: str,
    unique_event_times: List,
    bin_size: int,
    filter_value: str = None) -> str:
    """Calculate death counts, total counts, and at-risk counts at each unique event time.

    Parameters:
    - df: Input DataFrame
    - time_column_name: Name of the column representing time
    - censor_column_name: Name of the column representing censoring
    - unique_event_times: List of unique event times
    - bin_size: Size of the bin, when None binning method is not used

    Returns:
    - JSON-formatted string representing the calculated event table
    """
    # Filter the local dataframe with the query
    info(f"Overall number of patients: {df.shape[0]}")
    if filter_value:
        df = filter_df(df, filter_value)
        info(f"Number of patients in the cohort: {df.shape[0]}")

    # Apply binning to obfuscate event times
    if bin_size:
        # Convert time_column to appropriate data type for binning if needed
        if not pd.api.types.is_numeric_dtype(df[time_column_name]):
            df[time_column_name] = pd.to_numeric(df[time_column_name], errors='coerce')

        # Bin event time data
        info('Binning event times to compute tables')
        df[time_column_name] = np.float64(pd.cut(
            df[time_column_name], bins=unique_event_times,
            labels=unique_event_times[1:]
        ))
        df[time_column_name].fillna(0, inplace=True)

    # Group by the time column, aggregating both death and total counts simultaneously
    km_df = (
        df
        .groupby(time_column_name)
        .agg(
            removed=(censor_column_name, 'count'),
            observed=(censor_column_name, 'sum')
        )
        .reset_index()
    )
    km_df['censored'] = km_df['removed'] - km_df['observed']

    # Make sure all global times are available and sort it by time
    km_df = pd.merge(
        pd.DataFrame({time_column_name: unique_event_times}), km_df,
        on=time_column_name, how='left'
    ).fillna(0)
    km_df.sort_values(by=time_column_name, inplace=True)

    # Calculate "at-risk" counts at each unique event time
    km_df['at_risk'] = km_df['removed'].iloc[::-1].cumsum().iloc[::-1]

    # Convert DataFrame to JSON
    return km_df.to_json()


def launch_subtask(
    client: AlgorithmClient,
    method: Callable[[Any], Any],
    ids: List[int],
    **kwargs
) -> List[Dict[str, Union[str, List[str]]]]:
    """Launches a subtask to multiple organizations and waits for results.

    Parameters:
    - client: The Vantage6 client object used for communication with the server.
    - method: The callable method/function to be executed as a subtask by the organizations.
    - ids: A list of organization IDs to which the subtask will be distributed.
    - **kwargs: Additional keyword arguments to be passed to the method/function.

    Returns:
    - A list of dictionaries containing results obtained from the organizations.
    """
    info(f'Sending task to organizations {ids}')
    task = client.task.create(
        input_={
            'method': method,
            'kwargs': kwargs
        },
        organizations=ids
    )

    info("Waiting for results")
    results = client.wait_for_results(task_id=task.get("id"), interval=1)
    info(f"Results obtained for {method}!")
    return results
