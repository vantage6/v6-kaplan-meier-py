# -*- coding: utf-8 -*-

""" Centralised solution for Kaplan-Meier to be used for unit testing
"""
import pandas as pd
from lifelines import KaplanMeierFitter


def get_centralised_solution(
        data_paths: list, query_string: str, time_column_name: str,
        censor_column_name: str
) -> pd.DataFrame:

    # Reading and combining data
    df = pd.DataFrame()
    for data_path in data_paths:
        df_tmp = pd.read_csv(data_path)
        df = df._append(df_tmp, ignore_index=True)

    # Query data
    df = df.query(query_string)

    # Centralised solution
    kmf = KaplanMeierFitter()
    kmf.fit(
        list(df[time_column_name].values),
        event_observed=list(df[censor_column_name].values)
    )

    return kmf.event_table
