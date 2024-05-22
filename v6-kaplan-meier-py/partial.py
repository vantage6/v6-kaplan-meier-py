import pandas as pd

from typing import List
from vantage6.algorithm.tools.util import get_env_var, info, warn, error
from vantage6.algorithm.tools.decorators import data
from vantage6.algorithm.tools.exceptions import InputError


@data(1)
def get_unique_event_times(df: pd.DataFrame, time_column_name: str) -> List[str]:
    """
    Get unique event times from a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame supplied by the node.
    time_column_name : str
        Name of the column representing time.

    Returns
    -------
    List[str]
        List of unique event times.
    """
    if time_column_name not in df.columns:
        raise InputError(f"Column '{time_column_name}' not found in the dataframe.")

    # TODO: FM 22-05-2024
    #   * We need to apply some noise
    #   * We need to check if this column is allowed to be used

    return df[time_column_name].unique().tolist()


@data(1)
def get_km_event_table(
    df: pd.DataFrame,
    time_column_name: str,
    censor_column_name: str,
    unique_event_times: List[int | float],
) -> str:
    """
    Calculate death counts, total counts, and at-risk counts at each unique event time.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    time_column_name : str
        Name of the column representing time.
    censor_column_name : str
        Name of the column representing censoring.
    unique_event_times : List[int | float]
        List of unique event times.

    Returns
    -------
    str
        The Kaplan-Meier event table as a JSON string.
    """
    # Group by the time column, aggregating both death and total counts simultaneously
    km_df = (
        df.groupby(time_column_name)
        .agg(
            removed=(censor_column_name, "count"), observed=(censor_column_name, "sum")
        )
        .reset_index()
    )
    km_df["censored"] = km_df["removed"] - km_df["observed"]

    # Make sure all global times are available and sort it by time
    km_df = pd.merge(
        pd.DataFrame({time_column_name: unique_event_times}),
        km_df,
        on=time_column_name,
        how="left",
    ).fillna(0)
    km_df.sort_values(by=time_column_name, inplace=True)

    # Calculate "at-risk" counts at each unique event time
    km_df["at_risk"] = km_df["removed"].iloc[::-1].cumsum().iloc[::-1]

    # Convert DataFrame to JSON
    return km_df.to_json()
