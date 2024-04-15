import pytest
import lifelines
import pandas as pd

from unittest.mock import patch
from vtg_km.v6_km_utils import filter_df

class TestFiltering:
    @pytest.fixture(scope="class")
    def lifeline_waltons(self):
        waltons = lifelines.datasets.load_waltons()
        # Cheaply and badly check if the dataset has changed, as we want to
        # further make sure differences in test results are due to potential
        # errors in our code, not unexpected upstream changes to datasets from
        # lifeines.
        if pd.util.hash_pandas_object(waltons).sum() != 11603055737657237860:
            pytest.exit("Waltons dataset from lifelines _seems_ to have changed. Aborting tests with it.")

        kmf = lifelines.KaplanMeierFitter()
        kmf.fit(waltons['T'], waltons['E'])

        return waltons, kmf

    def test_filtering_unset_filter_column(self, lifeline_waltons):
        waltons_df, kmf = lifeline_waltons
        # Due to encoding of vars in vantage6 early 4 versions, we resort to mocking
        def get_env_var_mock(env_var, default=None):
            return {
                "V6_FILTER_VALUES_ALLOWED": None,
            }.get(env_var, default)

        with patch("vtg_km.v6_km_utils.get_env_var", side_effect=get_env_var_mock):
            with pytest.raises(ValueError) as excinfo:
                filter_df(waltons_df, "control")
            assert "No filter column set" in str(excinfo.value)

    def test_filter_df_not_allowed(self, lifeline_waltons):
        waltons_df, kmf = lifeline_waltons
        # Due to encoding of vars in vantage6 early 4 versions, we resort to mocking
        def get_env_var_mock(env_var, default=None):
            return {
                "V6_FILTER_COLUMN": "group",
                "V6_FILTER_VALUES_ALLOWED": "control,miR-137",
            }.get(env_var, default)

        with patch("vtg_km.v6_km_utils.get_env_var", side_effect=get_env_var_mock):
            with pytest.raises(ValueError) as excinfo:
                filter_df(waltons_df, "age")
            assert "Filter value not allowed" in str(excinfo.value)

    def test_filter_df_allowed(self, lifeline_waltons):
        waltons_df, kmf = lifeline_waltons
        # Due to encoding of vars in vantage6 early 4 versions, we resort to mocking
        def get_env_var_mock(env_var, default=None):
            return {
                "V6_FILTER_COLUMN": "group",
                "V6_FILTER_VALUES_ALLOWED": "control,miR-137",
            }.get(env_var, default)

        with patch("vtg_km.v6_km_utils.get_env_var", side_effect=get_env_var_mock):
            filtered = filter_df(waltons_df, "control")
            assert filtered.shape[0] == 129

    def test_filter_nonexisting_column(self, lifeline_waltons):
        waltons_df, kmf = lifeline_waltons
        # Due to encoding of vars in vantage6 early 4 versions, we resort to mocking
        def get_env_var_mock(env_var, default=None):
            return {
                "V6_FILTER_COLUMN": "nonexisting"
            }.get(env_var, default)

        with patch("vtg_km.v6_km_utils.get_env_var", side_effect=get_env_var_mock):
            with pytest.raises(ValueError) as excinfo:
                filter_df(waltons_df, "control")
            assert "Filter column not found" in str(excinfo.value)

    def test_filter_no_restrictions(self, lifeline_waltons):
        waltons_df, kmf = lifeline_waltons
        # Due to encoding of vars in vantage6 early 4 versions, we resort to mocking
        def get_env_var_mock(env_var, default=None):
            return {
                "V6_FILTER_COLUMN": "group"
            }.get(env_var, default)

        with patch("vtg_km.v6_km_utils.get_env_var", side_effect=get_env_var_mock):
            filtered = filter_df(waltons_df, "control")
            assert filtered.shape[0] == 129
