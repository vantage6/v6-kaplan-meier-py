"""
Run pytest to test the Kaplan-Meier algorithm locally using MockNetwork.

    uv sync --group dev
    uv run pytest test/test.py -v
"""

import os
from io import StringIO
from pathlib import Path

import pandas as pd
import pytest
from lifelines import KaplanMeierFitter

from vantage6.algorithm.mock.network import MockNetwork

current_path = Path(__file__).parent

TIME_COLUMN = "TIME_AT_RISK"
CENSOR_COLUMN = "MORTALITY_FLAG"
DATABASE_LABEL = "Database"

df1 = pd.read_csv(current_path / "data1.csv")
df2 = pd.read_csv(current_path / "data2.csv")
df3 = pd.read_csv(current_path / "data3.csv")
combined = pd.concat([df1, df2, df3], ignore_index=True)

os.environ["KAPLAN_MEIER_TYPE_NOISE"] = "NONE"

network = MockNetwork(
    datasets=[
        {DATABASE_LABEL: {"database": df1}},
        {DATABASE_LABEL: {"database": df2}},
        {DATABASE_LABEL: {"database": df3}},
    ],
    module_name="v6-kaplan-meier-py",
)
client = network.user_client

DATABASES = [{"type": "dataframe", "dataframe_id": network.hq.dataframes[0]["id"]}]

organizations = client.organization.list()
org_ids = [organization["id"] for organization in organizations]

KM_ARGS = {
    "time_column_name": TIME_COLUMN,
    "censor_column_name": CENSOR_COLUMN,
    "organizations_to_include": org_ids,
}


def _central_result(results):
    """Parse the JSON string returned by kaplan_meier_central."""
    payload = results[0]
    if isinstance(payload, str):
        return pd.read_json(StringIO(payload))
    return pd.read_json(StringIO(payload))


def _reference_survival() -> pd.Series:
    kmf = KaplanMeierFitter()
    kmf.fit(combined[TIME_COLUMN], combined[CENSOR_COLUMN])
    return kmf.survival_function_.iloc[:, 0]


def test_central_kaplan_meier():
    """Federated KM curve should match centralized lifelines reference without noise."""
    task = client.task.create(
        method="kaplan_meier_central",
        arguments=KM_ARGS,
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    federated = _central_result(client.wait_for_results(task.get("id")))
    reference = _reference_survival()

    assert TIME_COLUMN in federated.columns
    assert "survival_cdf" in federated.columns
    assert len(federated) > 0

    federated = federated.set_index(TIME_COLUMN)["survival_cdf"]
    common_times = federated.index.intersection(reference.index)
    assert len(common_times) > 0

    for time_point in common_times:
        assert federated.loc[time_point] == pytest.approx(
            reference.loc[time_point], rel=1e-6
        )


def test_partial_unique_event_times():
    """Partial step should return unique event times from one node."""
    task = client.task.create(
        method="get_unique_event_times",
        arguments={"time_column_name": TIME_COLUMN},
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    results = client.wait_for_results(task.get("id"))

    unique_times = set(results[0])
    expected = set(df1[TIME_COLUMN].unique())
    assert unique_times == expected


def test_partial_km_event_table():
    """Partial event table should include required Kaplan-Meier columns."""
    unique_times = sorted(df1[TIME_COLUMN].unique().tolist())
    task = client.task.create(
        method="get_km_event_table",
        arguments={
            "time_column_name": TIME_COLUMN,
            "censor_column_name": CENSOR_COLUMN,
            "unique_event_times": unique_times,
        },
        organizations=[org_ids[0]],
        databases=DATABASES,
    )
    results = client.wait_for_results(task.get("id"))

    event_table = pd.read_json(StringIO(results[0]))
    for column in (TIME_COLUMN, "observed", "removed", "censored", "at_risk"):
        assert column in event_table.columns
    assert len(event_table) == len(unique_times)
