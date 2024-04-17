from typing import Dict, List, Union
from vantage6.algorithm.client import AlgorithmClient
from vantage6.algorithm.tools.util import info
from vantage6.algorithm.tools.decorators import algorithm_client

from .v6_km_utils import calculate_km, get_km_event_table, get_unique_event_times

MINIMUM_ORGANIZATIONS = 3


@algorithm_client
def master(
    client: AlgorithmClient,
    time_column_name: str,
    censor_column_name: str,
    bin_size: int = None,
    filter_value: str = None,
    organization_ids: List[int] = None
) -> Dict[str, Union[str, List[str]]]:
    """Compute Kaplan-Meier curve in a federated environment.

    Parameters:
    - client: Vantage6 client object
    - time_column_name: Name of the column representing time
    - censor_column_name: Name of the column representing censoring
    - binning: Simple KM or use binning to obfuscate events
    - filter_value: Value to be filtered in specified column, both from node configuration
    - organization_ids: List of organization IDs to include (default: None, includes all)

    Returns:
    - Dictionary containing Kaplan-Meier curve and local event tables
    """
    info('Collecting information on participating organizations')
    if not isinstance(organization_ids, list):
        organizations = client.organization.list()
        ids = [organization.get("id") for organization in organizations]
    else:
        ids = organization_ids

    # if len(ids) < MINIMUM_ORGANIZATIONS:
    #     error(f"To further ensure privacy, a minimum of {MINIMUM_ORGANIZATIONS} participating organizations is required")
    #     sys.exit(1)

    info(f'Sending task to organizations {ids}')
    km = calculate_km(
        client=client,
        ids=ids,
        time_column_name=time_column_name,
        censor_column_name=censor_column_name,
        bin_size=bin_size,
        filter_value=filter_value
    )
    return km.to_json()
