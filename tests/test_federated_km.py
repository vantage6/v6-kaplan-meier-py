# -*- coding: utf-8 -*-

""" Unit tests for federated Kaplan-Meier algorithm
"""
import os

import numpy as np
import pandas as pd

from io import StringIO
from vantage6.algorithm.tools.mock_client import MockAlgorithmClient
from tests.centralised_solution import get_centralised_solution
from vtg_km.v6_km_utils import aggregate_unique_event_times
from vtg_km.v6_km_utils import launch_subtask


# TODO: is it possible to check each function directly? Not sure what to do
#  about the decorators on top of the functions... Current implementation of
#  the unit tests are very ugly!
# Setting up mock client for testing purposes
data_path = os.path.join(os.getcwd(), 'vtg_km', 'local')
data_paths = []
for i in range(1, 4):
    data_paths.append(os.path.join(data_path, f'data{i}.csv'))
data_path1 = os.path.join(data_path, 'data1.csv')
data_path2 = os.path.join(data_path, 'data2.csv')
data_path3 = os.path.join(data_path, 'data3.csv')
data1 = {'database': data_path1, 'db_type': 'csv'}
data2 = {'database': data_path2, 'db_type': 'csv'}
data3 = {'database': data_path3, 'db_type': 'csv'}
org_ids = [0, 1, 2]
client = MockAlgorithmClient(
    datasets=[[data1], [data2], [data3]],
    organization_ids=org_ids,
    module='vtg_km'
)

# Computing unique global times
time_column_name = 'TIME_AT_RISK'
bin_size = None
query_string = 'COHORT_DEFINITION_ID == 1029'
unique_event_times = aggregate_unique_event_times(
    client, org_ids, time_column_name, bin_size, query_string
)

# Computing local tables
censor_column_name = 'MORTALITY_FLAG'
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
    pd.read_json(StringIO(event_table)) for event_table in local_events_tables
]
km = (pd.concat(local_events_tables)
        .groupby(time_column_name,as_index=False)
        .sum()
     )

kmc = get_centralised_solution(
    data_paths, query_string, time_column_name, censor_column_name
)


class TestFederatedKaplanMeier:
    def test_global_unique_times_are_unique(self):
        assert len(unique_event_times) == len(set(unique_event_times))

    def test_local_unique_times_ordered(self):
        local_times = [
            local_table[time_column_name].values.tolist()
            for local_table in local_events_tables
        ]
        assert np.all([times == sorted(times) for times in local_times])

    def test_global_unique_times_ordered(self):
        times = km[time_column_name].values.tolist()
        assert times == sorted(times)

    def test_size_local_event_tables(self):
        assert np.all(
            [len(local_table) == len(km) for local_table in local_events_tables]
        )

    def test_compare_at_risk_with_centralised(self):
        assert km['at_risk'].values.tolist() == kmc['at_risk'].values.tolist()

    def test_compare_observed_events_with_centralised(self):
        assert km['observed'].values.tolist() == kmc['observed'].values.tolist()

    def test_compare_censored_events_with_centralised(self):
        assert km['censored'].values.tolist() == kmc['censored'].values.tolist()

    # TODO: no overlap in the times
    # TODO: negative times
    # TODO: wrong format for censor column
    # TODO: node with empty data
    # TODO: node with wrong format for data
    # def test_binning_unique_times(self):
    #     assert sum(rows) == 3
    #
    # def test_size_local_event_tables_with_binning(self):
    #     assert sum(cols) == 3
