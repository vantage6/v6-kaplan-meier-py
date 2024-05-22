from vantage6.algorithm.tools.util import get_env_var


# FIXME: FM 22-05-2024 This function will be released with vantage6 4.5.0, and can be
#   removed from the algorithm code at that time.
def convert_envvar_to_int(envvar_name: str, default: str) -> int:
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
    if envvar < 0:
        raise ValueError(error_msg)
    return envvar
