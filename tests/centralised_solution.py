# -*- coding: utf-8 -*-
import pandas as pd
from lifelines import KaplanMeierFitter


def get_centralised_solution(
        data_paths: list, query_string: str, time_column_name: str,
        censor_column_name: str
) -> pd.DataFrame:
    """ Centralised solution for Kaplan-Meier to be used for unit testing

    Parameters:

    - data_paths: List with data paths for testing data
    - query_string: Data query
    - time_column_name: Name for event time column
    - censor_column_name: Name for censor column

    Returns:

    - Kaplan-Meier event table obtained with lifelines
    """

    # Reading and combining data
    df = pd.concat([pd.read_csv(path) for path in data_paths], ignore_index=True)

    # Query data
    df = df.query(query_string)

    # Centralised solution
    kmf = KaplanMeierFitter()
    kmf.fit(
        list(df[time_column_name].values),
        event_observed=list(df[censor_column_name].values)
    )

    return kmf.event_table
