How to use
==========

Input arguments
---------------

``kaplan_meier_central``
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :widths: 25 10 65
    :header-rows: 1

    * - Argument
      - Type
      - Description
    * - ``time_column_name``
      - ``String``
      - The name of the column that contains the event times. This column should contain
        numerical data.
    * - ``censor_column_name``
      - ``String``
      - The name of the column that contains the censoring information. This column
        should contain binary data, where 1 indicates an event and 0 indicates
        censoring.
    * - ``organizations_to_include``
      - ``List`` of ``Int``
      - The IDs of the organizations that should be included in the computation


Python client example
---------------------

To understand the information below, you should be familiar with the vantage6
framework. If you are not, please read the `documentation <https://docs.vantage6.ai>`_
first, especially the part about the
`Python client <https://docs.vantage6.ai/en/main/user/pyclient.html>`_.

.. code-block:: python

  from vantage6.client import Client

  # fill in your own values
  server = 'http://localhost'
  port = 5000
  api_path = '/api'
  private_key = None
  username = 'root'
  password = 'password'

  # Create connection with the vantage6 server
  client = Client(server, port, api_path)
  client.setup_encryption(private_key)
  client.authenticate(username, password)

  collaboration_id = 1  # or check your collaborations with client.collaboration.list()
  org_ids = [org['id'] for org in client.organization.list(collaboration=collaboration_id)]

  input_ = {
    'method': 'kaplan_meier_central',
    'args': [],
    'kwargs': {
        "time_column_name": "TIME_AT_RISK",
        "censor_column_name": "MORTALITY_FLAG",
        "organizations_to_include": org_ids
    }
  }

  my_task = client.task.create(
      collaboration=1,
      organizations=org_ids[0],
      name='v6-kaplan-meier-py',
      description='Federated Kaplan Meier from Python Client',
      image='harbor2.vantage6.ai/algorithms/kaplan-meier',
      input=input_,
  )

  task_id = my_task.get('id')
  results = client.wait_for_results(task_id)