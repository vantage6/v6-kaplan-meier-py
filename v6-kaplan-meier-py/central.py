"""
This file contains all central algorithm functions. It is important to note
that the central method is executed on a node, just like any other method.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled).
"""

import pandas as pd

from typing import Dict, List, Union
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.util import info, error
from vantage6.algorithm.tools.decorators import algorithm_client
from vantage6.algorithm.tools.exceptions import PrivacyThresholdViolation

from .globals import KAPLAN_MEIER_MINIMUM_ORGANIZATIONS
from .utils import get_env_var_as_int


@algorithm_client
def kaplan_meier_central(
    client: AlgorithmClient,
    time_column_name: str,
    censor_column_name: str,
    organizations_to_include: List[int] | None = None,
) -> Dict[str, Union[str, List[str]]]:
    """
    Central part of the Federated Kaplan-Meier curve computation.

    This part is responsible for the orchestration and aggregation of the federated
    computation. The algorithm is executed in two steps on the nodes. The first step
    collects all unique event times from the nodes. The second step calculates the
    Kaplan-Meier curve and local event tables.

    Parameters
    ----------
    client : Vantage6 client object
        The client object used for communication with the server.
    time_column_name : str
        Name of the column containing the survival times.
    censor_column_name : str
        Name of the column containing the censoring.
    organizations_to_include : list of int, optional
        List of organization IDs to include (default: None, includes all).

    Returns
    -------
    dict
        Dictionary containing Kaplan-Meier curve and local event tables.
    """
    if not organizations_to_include:
        info("Collecting participating organizations")
        organizations_to_include = [
            organization.get("id") for organization in client.organization.list()
        ]

    MINIMUM_ORGANIZATIONS = get_env_var_as_int(
        "KAPLAN_MEIER_MINIMUM_ORGANIZATIONS", KAPLAN_MEIER_MINIMUM_ORGANIZATIONS
    )
    if len(organizations_to_include) < MINIMUM_ORGANIZATIONS:
        raise PrivacyThresholdViolation(
            "Minimum number of organizations not met, should be at least "
            f"{MINIMUM_ORGANIZATIONS}."
        )

    info("Collecting unique event times")
    local_unique_event_times_per_node = _start_partial_and_collect_results(
        client=client,
        method="get_unique_event_times",
        organizations_to_include=organizations_to_include,
        time_column_name=time_column_name,
    )

    info("Aggregating unique event times")
    unique_event_times = set()
    for local_unique_event_times in local_unique_event_times_per_node:
        unique_event_times |= set(local_unique_event_times)

    info("Collecting Kaplan-Meier curve and local event tables")
    local_km_per_node = _start_partial_and_collect_results(
        client=client,
        method="get_km_event_table",
        organizations_to_include=organizations_to_include,
        unique_event_times=list(unique_event_times),
        time_column_name=time_column_name,
        censor_column_name=censor_column_name,
    )
    local_event_tables = [
        pd.read_json(event_table) for event_table in local_km_per_node
    ]

    info("Aggregating event tables")
    km = pd.concat(local_event_tables).groupby(time_column_name, as_index=False).sum()
    km["hazard"] = km["observed"] / km["at_risk"]
    km["survival_cdf"] = (1 - km["hazard"]).cumprod()

    info("Kaplan-Meier curve computed")
    return km.to_json()


def _start_partial_and_collect_results(
    client: AlgorithmClient, method: str, organizations_to_include: List[int], **kwargs
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Launches a partial task to multiple organizations and collects their results when
    ready.

    Parameters
    ----------
    client : AlgorithmClient
        The vantage6 client used for communication with the server.
    method : str
        The method/function to be executed as a subtask by the organizations.
    organization_ids : List[int]
        A list of organization IDs to which the subtask will be distributed.
    **kwargs : dict
        Additional keyword arguments to be passed to the method/function.

    Returns
    -------
    List[Dict[str, Union[str, List[str]]]]
        A list of dictionaries containing results obtained from the organizations.
    """
    info(f"Including {len(organizations_to_include)} organizations in the analysis")
    task = client.task.create(
        input_={"method": method, "kwargs": kwargs},
        organizations=organizations_to_include,
    )

    info("Waiting for results")
    results = client.wait_for_results(task_id=task["id"])
    info(f"Results obtained for {method}!")
    return results
