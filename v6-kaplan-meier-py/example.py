import warnings
import os
import pandas as pd
from vantage6.algorithm.tools.mock_client import MockAlgorithmClient
import base64

warnings.filterwarnings("ignore")

STRING_ENCODING = "utf-8"
ENV_VAR_EQUALS_REPLACEMENT = "="


def _encode(string: str):
    return (
        base64.b32encode(string.encode(STRING_ENCODING))
        .decode(STRING_ENCODING)
        .replace("=", ENV_VAR_EQUALS_REPLACEMENT)
    )


# Initialize the mock server. The datasets simulate the local datasets from
# the node. In this case we have two parties having two different datasets:
# a.csv and b.csv. The module name needs to be the name of your algorithm
# package. This is the name you specified in `setup.py`, in our case that
# would be v6-correlation-matrix-py.
dataset_1 = {"database": "./v6-kaplan-meier-py/local/data1.csv", "db_type": "csv"}
dataset_2 = {"database": "./v6-kaplan-meier-py/local/data2.csv", "db_type": "csv"}
dataset_3 = {"database": "./v6-kaplan-meier-py/local/data3.csv", "db_type": "csv"}
org_ids = ids = [0, 1, 2]

client = MockAlgorithmClient(
    datasets=[[dataset_1], [dataset_2], [dataset_3]],
    organization_ids=org_ids,
    module="v6-kaplan-meier-py",
)

organizations = client.organization.list()
org_ids = ids = [organization["id"] for organization in organizations]

os.environ["KAPLAN_MEIER_TYPE_NOISE"] = _encode("NONE")
# os.environ["KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME"] = _encode("-1")

# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.task.create(
    input_={
        "method": "kaplan_meier_central",
        "kwargs": {
            "time_column_name": "TIME_AT_RISK",
            "censor_column_name": "MORTALITY_FLAG",
        },
    },
    organizations=[org_ids[0]],
)

results = client.result.get(average_task.get("id"))
df_events_clean = pd.read_json(results)

os.environ["KAPLAN_MEIER_TYPE_NOISE"] = _encode("GAUSSIAN")
os.environ["KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME"] = _encode("5")

# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.task.create(
    input_={
        "method": "kaplan_meier_central",
        "kwargs": {
            "time_column_name": "TIME_AT_RISK",
            "censor_column_name": "MORTALITY_FLAG",
        },
    },
    organizations=[org_ids[0]],
)

results = client.result.get(average_task.get("id"))
df_events_noise = pd.read_json(results)

os.environ["KAPLAN_MEIER_RANDOM_SEED"] = _encode("1010")
os.environ["KAPLAN_MEIER_TYPE_NOISE"] = _encode("GAUSSIAN")
os.environ["KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME"] = _encode("50")

# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.task.create(
    input_={
        "method": "kaplan_meier_central",
        "kwargs": {
            "time_column_name": "TIME_AT_RISK",
            "censor_column_name": "MORTALITY_FLAG",
        },
    },
    organizations=[org_ids[0]],
)

results = client.result.get(average_task.get("id"))
df_events_small_noise = pd.read_json(results)

os.environ["KAPLAN_MEIER_TYPE_NOISE"] = _encode("POISSON")

# To trigger the master method you also need to supply the `master`-flag
# to the input. Also note that we only supply the task to a single organization
# as we only want to execute the central part of the algorithm once. The master
# task takes care of the distribution to the other parties.
average_task = client.task.create(
    input_={
        "method": "kaplan_meier_central",
        "kwargs": {
            "time_column_name": "TIME_AT_RISK",
            "censor_column_name": "MORTALITY_FLAG",
        },
    },
    organizations=[org_ids[0]],
)

results = client.result.get(average_task.get("id"))
df_events_poisson = pd.read_json(results)

import matplotlib.pyplot as plt


# # Plot the Kaplan-Meier curve for clean data
# plt.plot(
#     df_events_clean["TIME_AT_RISK"], df_events_clean["survival_cdf"], label="Clean Data"
# )

# # Plot the Kaplan-Meier curve for noisy data
# plt.plot(
#     df_events_noise["TIME_AT_RISK"], df_events_noise["survival_cdf"], label="Noisy Data"
# )

# # Plot the Kaplan-Meier curve for noisy data
# plt.plot(
#     df_events_small_noise["TIME_AT_RISK"],
#     df_events_small_noise["survival_cdf"],
#     label="Small Noisy Data",
# )

fig, ax1 = plt.subplots()

# Combine the datasets
combined_dataset = pd.concat(
    [
        pd.read_csv(dataset_1["database"]),
        pd.read_csv(dataset_2["database"]),
        pd.read_csv(dataset_3["database"]),
    ]
)

# Plot the histogram
ax1.hist(combined_dataset["TIME_AT_RISK"], bins=100, color="lightblue")
# ax1.hist(pd.read_csv(dataset_3["database"])["TIME_AT_RISK"], bins=10)

# Set the y-axis label for the histogram
ax1.set_ylabel("Frequency")
ax1.set_xlabel("Time")

# Create a second y-axis on the right side
ax2 = ax1.twinx()

# Plot the Kaplan-Meier curve for clean data
ax2.plot(df_events_clean["TIME_AT_RISK"], df_events_clean["survival_cdf"], label="None")
ax2.plot(
    df_events_noise["TIME_AT_RISK"],
    df_events_noise["survival_cdf"],
    label="Gaussian SNR=50",
)

# Plot the Kaplan-Meier curve for noisy data
ax2.plot(
    df_events_small_noise["TIME_AT_RISK"],
    df_events_small_noise["survival_cdf"],
    label="Gaussian SNR=5",
)

# Plot the Kaplan-Meier curve for noisy data
ax2.plot(
    df_events_poisson["TIME_AT_RISK"],
    df_events_poisson["survival_cdf"],
    label="Poisson",
)

# Set the y-axis label for the Kaplan-Meier curve
ax2.set_ylabel("Survival Probability")

# Set the title and legend
plt.title("Kaplan-Meier Curve with Histogram")
plt.legend(title="Noise Type")


# plt.xlabel("Time")
# plt.ylabel("Survival Probability")
# plt.title("Kaplan-Meier Curve")
# plt.legend()

plt.show()
