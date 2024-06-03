import re
import pandas as pd
import numpy as np

from typing import List
from vantage6.algorithm.tools.util import get_env_var, info, warn, error
from vantage6.algorithm.tools.decorators import data
from vantage6.algorithm.tools.exceptions import InputError, EnvironmentVariableError

from .utils import get_env_var_as_int, get_env_var_as_list, get_env_var_as_float
from .globals import (
    KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS,
    KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX,
    KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME,
    KAPLAN_MEIER_TYPE_NOISE,
)
from .enums import NoiseType


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

    _privacy_gaurds(df, time_column_name)

    df = _add_noise_to_event_times(df, time_column_name)

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
    _privacy_gaurds(df, time_column_name)

    df = _add_noise_to_event_times(df, time_column_name)

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


def _privacy_gaurds(df: pd.DataFrame, time_column_name: str) -> pd.DataFrame:
    """
    Check if the input data is valid and apply privacy guards.
    """

    info("Checking number of records in the DataFrame.")
    MINIMUM_NUMBER_OF_RECORDS = get_env_var_as_int(
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


def _add_noise_to_event_times(df: pd.DataFrame, time_column_name: str) -> pd.DataFrame:
    """
    Add noise to the event times in a DataFrame when this is requisted by the data-
    station.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame which contains the ``time_column_name`` column.
    time_column_name : str
        Privacy sensitive column name to which noise is going to b.

    Returns
    -------
    pd.DataFrame
        The DataFrame with added noise to the ``time_column_name``.
    """
    NOISE_TYPE = get_env_var("KAPLAN_MEIER_TYPE_NOISE", KAPLAN_MEIER_TYPE_NOISE).upper()
    if NOISE_TYPE == NoiseType.NONE:
        return df
    if NOISE_TYPE == NoiseType.GAUSSIAN:
        return __apply_gaussian_noise(df, time_column_name)
    elif NOISE_TYPE == NoiseType.POISSON:
        return __apply_poisson_noise(df, time_column_name)
    else:
        raise EnvironmentVariableError(f"Invalid noise type: {NOISE_TYPE}")


def __apply_gaussian_noise(df: pd.DataFrame, time_column_name: str) -> pd.DataFrame:
    """
    Apply Gaussian noise to the event times in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        The DataFrame with Gaussian noise applied to the event times column.
    """
    # The signal-to-noise ratio (SNR) is used to determine the amount of noise to add.
    # First the variance of the time column is calculated. Then the standard deviation
    # of the noise is calculated by dividing the variance by the SNR. Finally the noise
    # is generated using a normal distribution with a mean of 0 and the calculated
    # standard deviation.
    #
    #  noise = N(0, sqrt(var_time / SNR))
    #
    SNR = get_env_var_as_float(
        "KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME", KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME
    )
    var_time = np.var(df[time_column_name])
    standard_deviation_noise = np.sqrt(var_time / SNR)
    __fix_random_seed()
    noise = np.round(np.random.normal(0, standard_deviation_noise, len(df)))

    # Add the noise to the time event column and clip the values to be non-negative as
    # negative event times do not make sense.
    df[time_column_name] += noise
    df[time_column_name] = df[time_column_name].clip(lower=0.0)
    info("Gaussion noise applied to the event times.")
    info(f"Variance of the time column: {var_time}")
    info(f"Standard deviation of the noise: {standard_deviation_noise}")
    return df


def __apply_poisson_noise(df: pd.DataFrame, time_column_name: str) -> pd.DataFrame:
    """
    Apply Poisson noise to the event times in a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    Returns
    -------
    pd.DataFrame
        The DataFrame with Poisson noise applied to the event times column.
    """
    __fix_random_seed()
    df[time_column_name] = np.random.poisson(df[time_column_name])
    info("Poisson noise applied to the event times.")
    return df


def __fix_random_seed():
    """
    Every time before (every from the same function) a random number is generated we
    need to set the random seed to ensure reproducibility and privacy.
    """

    # In order to ensure that malicious parties can not reconstruct the orginal data
    # we need to add the same noise to the event times for every run. Else the party
    # can simply run the algorithm multiple times and average the results to get the
    # original event times.
    random_seed = get_env_var_as_int("KAPLAN_MEIER_RANDOM_SEED", "0")
    if random_seed == 0:
        warn(
            "Random seed is set to 0, this is not safe and should only be done for "
            "testing."
        )
    np.random.seed(random_seed)
