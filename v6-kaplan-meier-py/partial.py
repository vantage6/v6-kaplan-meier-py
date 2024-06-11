import re
import traceback
import pkg_resources
import pandas as pd
import numpy as np

from typing import List

from rpy2.robjects import RS4
from rpy2.rinterface_lib.sexp import NACharacterType

from vantage6.algorithm.tools.util import get_env_var, info, warn, error
from vantage6.algorithm.tools.decorators import (
    database_connection,
    metadata,
    OHDSIMetaData,
    RunMetaData,
)
from vantage6.algorithm.tools.exceptions import InputError, EnvironmentVariableError

from .utils import get_env_var_as_int, get_env_var_as_list, get_env_var_as_float
from .globals import (
    KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS,
    KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX,
    KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME,
    KAPLAN_MEIER_TYPE_NOISE,
)
from .enums import NoiseType

from ohdsi.sqlrender import read_sql, render, translate
from ohdsi.database_connector import query_sql
from ohdsi.common import convert_from_r


@metadata
@database_connection(types=["OMOP"], include_metadata=True)
def get_unique_event_times(
    connection: RS4,
    meta_omop: OHDSIMetaData,
    meta_run: RunMetaData,
    cohort_task_id: int,
    shared_cohort_id: float,
    time_column_name: str,
) -> List[str]:
    """
    Get unique event times from a DataFrame.

    Parameters
    ----------
    connection : RS4
        Connection to the database.
    meta_omop : OHDSIMetaData
        Metadata of the OMOP database.
    meta_run : RunMetaData
        Metadata of the run.
    cohort_task_id : int
        Task ID of the task where the cohort is created in the database.
    shared_cohort_id : float
        Shared cohort ID, this id is the same over all nodes and is returned by the
        task that created the cohort.
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
    info("Getting unique event times per cohort")
    info(f"Time column name: {time_column_name}")

    info("Creating cohort DataFrame from OMOP CDM")
    df = __create_cohort_dataframe(
        connection, meta_run, meta_omop, cohort_task_id, shared_cohort_id
    )

    info("Checking privacy guards")
    _privacy_gaurds(df, time_column_name)

    info("Adding noise to event times")
    df = _add_noise_to_event_times(df, time_column_name)

    return df[time_column_name].unique().tolist()


@metadata
@database_connection(types=["OMOP"], include_metadata=True)
def get_km_event_table(
    connection: RS4,
    meta_omop: OHDSIMetaData,
    meta_run: RunMetaData,
    cohort_task_id: int,
    shared_cohort_id: float,
    time_column_name: str,
    censor_column_name: str,
    unique_event_times: List[int | float],
) -> str:
    """
    Calculate death counts, total counts, and at-risk counts at each unique event time.

    Parameters
    ----------
    connection : RS4
        Connection to the database.
    meta_omop : OHDSIMetaData
        Metadata of the OMOP database.
    meta_run : RunMetaData
        Metadata of the run.
    cohort_task_id : int
        Task ID of the task where the cohort is created in the database.
    shared_cohort_id : float
        Shared cohort ID, this id is the same over all nodes and is returned by the
        task that created the cohort.
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
    info("Creating cohort DataFrame from OMOP CDM")
    df = __create_cohort_dataframe(
        connection, meta_run, meta_omop, cohort_task_id, shared_cohort_id
    )

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


def __create_cohort_dataframe(
    connection: RS4,
    meta_run: RunMetaData,
    meta_omop: OHDSIMetaData,
    cohort_task_id: int,
    shared_cohort_id: str,
) -> list[pd.DataFrame]:
    """
    Query the database for the data of the cohort.

    Parameters
    ----------
    connection : RS4
        Connection to the database.

    Returns
    -------
    pd.DataFrame
        The data of the cohort.
    """
    # Get the task id of the task that created the cohort at this node
    cohort_table = f"cohort_{cohort_task_id}_{meta_run.node_id}"

    # Obtain the cohort IDs by combining the shared ids (equal over all nodes) with the
    # local node id
    cohort_id = float(f"{meta_run.node_id}{shared_cohort_id}")

    # Obtain SQL file for standard features
    sql_path = pkg_resources.resource_filename(
        "v6-kaplan-meier-py", "sql/standard_features.sql"
    )

    # SQL READ
    try:
        raw_sql = read_sql(sql_path)
    except Exception as e:
        error(f"Failed to read SQL file: {e}")
        traceback.print_exc()
        raise e

    df = _query_database(connection, raw_sql, cohort_table, cohort_id, meta_omop)

    # NACHARS
    df["OBSERVATION_VAS"] = df["OBSERVATION_VAS"].apply(
        lambda val: np.nan if isinstance(val, NACharacterType) else val
    )

    # DROP DUPLICATES
    sub_df = df.drop_duplicates("SUBJECT_ID", keep="first")
    info(f"Dropped {len(df) - len(sub_df)} rows")

    return sub_df


def _query_database(
    connection: RS4,
    sql: str,
    cohort_table: str,
    cohort_id: float,
    meta_omop: OHDSIMetaData,
) -> pd.DataFrame:

    # RENDER
    sql = render(
        sql,
        cohort_table=f"{meta_omop.results_schema}.{cohort_table}",
        cohort_id=cohort_id,
        cdm_database_schema=meta_omop.cdm_schema,
        incl_condition_concept_id=["NULL"],
        incl_procedure_concept_id=["NULL"],  # 4066543
        incl_measurement_concept_id=["NULL"],
        incl_drug_concept_id=["NULL"],  #'ALL' ? @TODO in algo
    )

    # TRANSLATE
    sql = translate(sql, target_dialect="postgresql")

    # QUERY
    try:
        data_r = query_sql(connection, sql)
    except Exception as e:
        error(f"Failed to query the database: {e}")
        traceback.print_exc()
        with open("errorReportSql.txt", "r") as f:
            error(f.read())

    # CONVERT
    return convert_from_r(data_r)


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
    df[time_column_name] = np.random.poisson(df[time_column_name].astype(np.float64))
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
