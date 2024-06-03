import re
import pandas as pd
import numpy as np

from typing import List
from vantage6.algorithm.tools.util import get_env_var, info, warn, error
from vantage6.algorithm.tools.decorators import data
from vantage6.algorithm.tools.exceptions import InputError

from .utils import convert_envvar_to_int, get_env_var_as_list, get_env_var_as_float
from .globals import (
    KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS,
    KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX,
    KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME,
)


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

    Raises
    ------
    InputError
        If the time column is not found in the DataFrame.
    """
    info("Getting unique event times")
    info(f"Time column name: {time_column_name}")

    info("Checking number of records in the DataFrame.")
    MINIMUM_NUMBER_OF_RECORDS = convert_envvar_to_int(
        "KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS", KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS
    )
    if len(df) <= MINIMUM_NUMBER_OF_RECORDS:
        raise InputError("Number of records in 'df' must be greater than 3.")

    info("Check that the selected time column is allowed by the node")
    ALLOWED_EVENT_TIME_COLUMNS_REGEX = get_env_var_as_list(
        "KAPLAN_MEIER_EVENT_TIME_COLUMN", KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX
    )
    for pattern in ALLOWED_EVENT_TIME_COLUMNS_REGEX:
        if re.match(pattern, time_column_name):
            break
    else:
        info(f"Allowed event time columns: {ALLOWED_EVENT_TIME_COLUMNS_REGEX}")
        raise InputError(
            f"Column '{time_column_name}' is not allowed as a time column."
        )

    if time_column_name not in df.columns:
        raise InputError(f"Column '{time_column_name}' not found in the data frame.")

    SNR = get_env_var_as_float(
        "KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME", KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME
    )
    POISSON = get_env_var_as_float("POISSON", "1")
    if SNR >= 0.0:
        # FIXME: ! t < 0.0
        np.random.seed(42)
        info("Applying Gaussian noise to the unique event times.")
        var_time = np.var(df[time_column_name])
        info(f"Variance of the time column: {var_time}")
        standard_deviation_noise = np.sqrt(var_time / SNR)
        info(f"Standard deviation of the noise: {standard_deviation_noise}")
        noise = np.random.normal(0, standard_deviation_noise, len(df))
        df[time_column_name] += np.round(noise)
        df[time_column_name] = df[time_column_name].clip(lower=0.0)
        info(f"avg delta: {sum(abs(noise)) / len(df)}")
        info(f"sum noise: {sum(noise)}")
    elif POISSON:
        df[time_column_name] = np.random.poisson(df[time_column_name])
    else:
        warn("No noise applied to the unique event times.")

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
    SNR = get_env_var_as_float(
        "KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME", KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME
    )
    POISSON = get_env_var_as_float("POISSON", "1")
    if SNR >= 0.0:
        # FIXME: ! t < 0.0
        np.random.seed(42)
        info("Applying Gaussian noise to the unique event times.")
        var_time = np.var(df[time_column_name])
        info(f"Variance of the time column: {var_time}")
        standard_deviation_noise = np.sqrt(var_time / SNR)
        info(f"Standard deviation of the noise: {standard_deviation_noise}")
        noise = np.random.normal(0, standard_deviation_noise, len(df))
        df[time_column_name] += np.round(noise)
        df[time_column_name] = df[time_column_name].clip(lower=0.0)
        info(f"avg delta: {sum(abs(noise)) / len(df)}")
        info(f"sum noise: {sum(noise)}")
    elif POISSON:
        df[time_column_name] = np.random.poisson(df[time_column_name])

    else:
        warn("No noise applied to the unique event times.")
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


def _add_noise(df: pd.DataFrame, snr: float = 5.0) -> pd.DataFrame:
    """
    Add noise to a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    epsilon : float
        The privacy budget.

    Returns
    -------
    pd.DataFrame
        The DataFrame with added noise.
    """
