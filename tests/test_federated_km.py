# -*- coding: utf-8 -*-

""" Unit tests for federated Kaplan-Meier algorithm
"""
import os
import pandas as pd
from io import StringIO
from vantage6.algorithm.tools.mock_client import MockAlgorithmClient
from vtg_km.v6_km_utils import aggregate_unique_event_times
from vtg_km.v6_km_utils import launch_subtask


# TODO: is it possible to check each function directly? Not sure what to do
#  about the decorators on top of the functions... Current implementation of
#  the unit tests are very ugly!
# Setting up mock client for testing purposes
data_path = os.path.join(os.getcwd(), 'vtg_km', 'local')
data1 = {'database': os.path.join(data_path, 'data1.csv'), 'db_type': 'csv'}
data2 = {'database': os.path.join(data_path, 'data2.csv'), 'db_type': 'csv'}
org_ids = [0, 1]
client = MockAlgorithmClient(
    datasets=[[data1], [data2]],
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


class TestFederatedKaplanMeier:
    def test_global_unique_times_are_unique(self):
        assert len(unique_event_times) == len(set(unique_event_times))

    # def test_global_unique_times_ordered(self):
    #     assert result is True
    #
    # def test_binning_unique_times(self):
    #     assert sum(rows) == 3
    #
    # def test_size_local_event_tables(self):
    #     assert sum(cols) == 3
    #
    # def test_size_local_event_tables_with_binning(self):
    #     assert sum(cols) == 3
    #
    # def test_incorrect_data_types(self):
    #     assert result is True
    #
    # def test_validity_censor_column(self):
    #     assert result is True
    #
    # def test_presence_nan_values_input_data(self):
    #     assert result is True
    #
    # def test_presence_nan_values_local_tables(self):
    #     assert result is True
    #
    # def test_total_patients_t_zero(self):
    #     assert result is True
    #
    # def test_total_patients_final_t(self):
    #     assert result is True
    #
    # def test_equivalence_with_centralised(self):
    #     assert result is True
