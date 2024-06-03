from vantage6.algorithm.tools.util import get_env_var


# FIXME: FM 22-05-2024 This function will be released with vantage6 4.5.0, and can be
#   removed from the algorithm code at that time.
def get_env_var_as_int(envvar_name: str, default: str) -> int:
    """
    Convert an environment variable to an integer value.

    Parameters
    ----------
    envvar_name : str
        The environment variable name to convert.
    default : str
        The default value to use if the environment variable is not set.

    Returns
    -------
    int
        The integer value of the environment variable.
    """
    envvar = get_env_var(envvar_name, default)
    error_msg = (
        f"Environment variable '{envvar_name}' has value '{envvar}' which cannot be "
        "converted to a positive integer value."
    )
    try:
        envvar = int(envvar)
    except ValueError as exc:
        raise ValueError(error_msg) from exc
    return envvar


def get_env_var_as_float(envvar_name: str, default: str) -> float:
    """
    Convert an environment variable to a float value.

    Parameters
    ----------
    envvar_name : str
        The environment variable name to convert.
    default : str
        The default value to use if the environment variable is not set.

    Returns
    -------
    float
        The float value of the environment variable.
    """
    envvar = get_env_var(envvar_name, default)
    error_msg = (
        f"Environment variable '{envvar_name}' has value '{envvar}' which cannot be "
        "converted to a float value."
    )
    try:
        envvar = float(envvar)
    except ValueError as exc:
        raise ValueError(error_msg) from exc
    return envvar


def get_env_var_as_list(envvar_name: str, default: str, separator: str = ",") -> list:
    """
    Convert an environment variable to a list. The environment variable should be a
    string with elements separated by a separator. The default value is used if the
    environment variable is not set.

    Parameters
    ----------
    envvar_name : str
        The environment variable name to convert.
    default : str
        The default value to use if the environment variable is not set.
    separator : str, optional
        The separator to use to split the environment variable (default: ',').

    Returns
    -------
    list
        The list of the environment variable.
    """
    envvar = get_env_var(envvar_name, default)
    return envvar.split(separator)
