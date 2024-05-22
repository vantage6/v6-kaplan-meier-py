"""
This file contains all central algorithm functions. It is important to note
that the central method is executed on a node, just like any other method.

The results in a return statement are sent to the vantage6 server (after
encryption if that is enabled).
"""

import sys

from typing import Dict, List, Union
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.util import info, error
from vantage6.algorithm.tools.decorators import algorithm_client
from vantage6.algorithm.tools.exceptions import PrivacyThresholdViolation

from .v6_km_utils import calculate_km, get_km_event_table, get_unique_event_times

from .globals import MINIMUM_ORGANIZATIONS


@algorithm_client
def central(
    client: AlgorithmClient,
    time_column_name: str,
    censor_column_name: str,
    organizations_to_include: List[int] | None = None,
) -> Dict[str, Union[str, List[str]]]:
    """
    Central part of the Federated Kaplan-Meier curve computation.

    This part is responsible for the orchestration and aggregation of the federated
    computation.

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

    if len(organizations_to_include) < MINIMUM_ORGANIZATIONS:
        raise PrivacyThresholdViolation(
            "Minimum number of organizations not met, should be at least "
            f"{MINIMUM_ORGANIZATIONS}."
        )

    info(f"Sending task to {len(organizations_to_include)} organizations")
    km = calculate_km(
        client=client,
        ids=organizations_to_include,
        time_column_name=time_column_name,
        censor_column_name=censor_column_name,
        # bin_size=bin_size,
        # filter_value=filter_value,
    )
    return km.to_json()
