# -*- coding: utf-8 -*-
import pandas as pd
from io import StringIO
from typing import List, Tuple
from vantage6.algorithm.tools.mock_client import MockAlgorithmClient
from vtg_km.v6_km_utils import aggregate_unique_event_times
from vtg_km.v6_km_utils import launch_subtask


def get_federated_solution(
        data_paths: list, query_string: str, time_column_name: str,
        censor_column_name: str, bin_size: int = None
) -> Tuple[List[int], List[pd.DataFrame], pd.DataFrame]:
    """ Federated solution for Kaplan-Meier to be used for unit testing

    Parameters:

    - data_paths: List with data paths for testing data
    - query_string: Data query
    - time_column_name: Name for event time column
    - censor_column_name: Name for censor column
    - bin_size: Size of the bin, when None binning method is not used

    Returns:

    - Unique event times, local events tables, and global events table
    """

    # Datasets to be used for federated Kaplan-Meier
    datasets = []
    for data_path in data_paths:
        data = {'database': data_path, 'db_type': 'csv'}
        datasets.append([data])

    # Setting up mock client for testing purposes
    org_ids = [i for i in range(len(datasets))]
    client = MockAlgorithmClient(
        datasets=datasets,
        organization_ids=org_ids,
        module='vtg_km'
    )

    # Computing unique global times
    unique_event_times = aggregate_unique_event_times(
        client, org_ids, time_column_name, bin_size, query_string
    )

    # Computing local tables
    method_kwargs = dict(
        time_column_name=time_column_name,
        unique_event_times=list(unique_event_times),
        censor_column_name=censor_column_name,
        bin_size=bin_size,
        query_string=query_string
    )
    method = 'get_km_event_table'
    local_events_tables = launch_subtask(
        client, method, org_ids, **method_kwargs
    )

    # Computing global table
    local_events_tables = [
        pd.read_json(StringIO(event_table)) for event_table in
        local_events_tables
    ]
    km = (pd.concat(local_events_tables)
          .groupby(time_column_name, as_index=False)
          .sum()
          )

    return unique_event_times, local_events_tables, km
