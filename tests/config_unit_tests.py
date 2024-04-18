# -*- coding: utf-8 -*-

""" Input for testing federated Kaplan-Meier algorithm
"""
import os
from tests.centralised_solution import get_centralised_solution
from tests.federated_solution import get_federated_solution


# Datasets to be used for testing
data_path = os.path.join(os.getcwd(), 'vtg_km', 'local')
data_paths = []
for i in range(1, 4):
    data_paths.append(os.path.join(data_path, f'data{i}.csv'))

# Parameters for testing
time_column_name = 'TIME_AT_RISK'
censor_column_name = 'MORTALITY_FLAG'
filter_value = '1029'
# for centralised solution using lifelines
query_string = 'COHORT_DEFINITION_ID == 1029'

# Federated solution
unique_event_times, local_events_tables, km = get_federated_solution(
    data_paths, filter_value, time_column_name, censor_column_name
)

# Centralised solution
kmc = get_centralised_solution(
    data_paths, query_string, time_column_name, censor_column_name
)
