# For early versions of vantage6 version 4, environment variables are encoded
# by the node in a non-standard way. This function is taken directly from
# vantage6-node, to avoid pulling yet another dependency.  In later versions,
# get_env_var won't attempt decoding if the environment variable is not
# encoded.
# See: https://github.com/vantage6/vantage6/blob/version/4.3.4/vantage6-node/vantage6/node/docker/task_manager.py#L628-L654
# TODO: @lsago document this better..

import base64

STRING_ENCODING = "utf-8"
ENV_VAR_EQUALS_REPLACEMENT = "!"

def _encode_env_var(string: str) -> str:
    """Encode env var value

    We first encode to bytes, then to b32 and then decode to a string.
    Finally, '=' is replaced by less sensitve characters to prevent
    issues with interpreting the encoded string in the env var value.

    Parameters
    ----------
    string: str
        String to be encoded

    Returns
    -------
    str:
        Encoded string

    Examples
    --------
    >>> _encode("abc")
    'MFRGG!!!'
    """
    return (
        base64.b32encode(string.encode(STRING_ENCODING))
        .decode(STRING_ENCODING)
        .replace("=", ENV_VAR_EQUALS_REPLACEMENT)
    )
