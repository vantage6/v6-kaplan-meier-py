# The following global variables are algorithm settings. They can be overwritten by
# the node admin by setting the corresponding environment variables.


KAPLAN_MEIER_MINIMUM_ORGANIZATIONS = 3

KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS = 3

KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX = ".*"

# Default noise type for event counts. Can be either "POISSON" or "GAUSSIAN".
KAPLAN_MEIER_TYPE_NOISE = "POISSON"

# Default gaussian noise SNR for event times, not that by default Poisson noise is
# used for event counts.
KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME = 0.0
