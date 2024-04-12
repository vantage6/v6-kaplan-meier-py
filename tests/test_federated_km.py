# -*- coding: utf-8 -*-
import numpy as np
from config_unit_tests import *


class TestFederatedKaplanMeier:
    """ Unit tests for federated Kaplan-Meier algorithm
    """
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
