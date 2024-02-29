# Federated Kaplan-Meier Curve Calculation with vantage6

This repository contains an implementation of the Kaplan-Meier curve calculation designed for federated learning environments via the vantage6 framework. It allows for the estimation of survival probabilities across distributed datasets without sharing the patient-specific information. This method supports privacy-preserving data analysis in medical research and other fields where event-time analysis is critical.

The algorithm operates within the vantage6 infrastructure, a platform supporting federated learning, to enable institutions to perform survival analysis while maintaining data privacy. The initial idea was based on contributions from Benedetta Gottardelli (benedetta.gottardelli@unicatt.it).

Follow the instructions in subsequent sections to set up and execute the federated Kaplan-Meier analysis.

## Usage

This section provides a comprehensive guide on how to use the repository to perform federated Kaplan-Meier analysis, from initializing the client to executing the task and retrieving the results.

To perform Kaplan-Meier curve calculation in a federated learning context using vantage6, follow these instructions:

1. **Install vantage6 Client** (if not already installed):
```bash
pip install vantage6-client
```

2. **Initialize vantage6 Client**

```python
from vantage6.client import Client

# Load your configuration settings from a file or environment
config = {
    'server_url': '<API_ENDPOINT>',
    'server_port': <API_PORT>,
    'server_api': '<API_VERSION>',
    'username': '<USERNAME>',
    'password': '<PASSWORD>',
    'organization_key': '<ORGANIZATION_PRIVATE_KEY>'
}

client = Client(config['server_url'], config['server_port'], config['server_api'])
client.authenticate(username=config['username'], password=config['password'])
client.setup_encryption(config['organization_key'])
```

Replace the placeholders in `config` with your actual configuration details.

3. **Define Algorithm Input**
```python
input_ = {
    'method': 'master',
    'kwargs': {
        'time_column_name': 'time_to_event',
        'censor_column_name': 'event_occurred',
        'organization_ids': [1, 2, 3], # Example organization IDs
        'bin_size': None  # Or a specific bin size
    }
}
```

Set your specific time and censor column names, organization IDs, and bin size if needed.

4. **Create and Run the Task**
```python
task = client.task.create(
    collaboration=3,  # Use your specific collaboration ID
    organizations=[1, 2, 3],  # List your organization IDs
    name='Kaplan-Meier Task',  # Give your task a specific name
    image='ghcr.io/mdw-nl/v6-km-studyathon:v1',  # Specify the desired algorithm Docker image version
    description='Survival analysis using Kaplan-Meier',  # Describe the task
    databases=[{'label': 'my_database_label'}],  # Use your database label
    input_=input_
)
```

Provide actual values for the `collaboration`, `organizations`, `name`, `image`, `description`, and `databases` fields.

5. **Monitor and Retrieve Results**: Utilize the vantage6 client methods to check the status of the task and retrieve the results when the task is complete.

Ensure all prerequisites are met and configurations are set by referring to the 'Installation and Setup' section before proceeding with the above steps.
