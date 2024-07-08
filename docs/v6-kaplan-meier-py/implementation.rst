Implementation
==============

Overview
--------
The algorithm is executed in two steps at the nodes. First the unique event times are
collected from the nodes. Then the Kaplan-Meier curve is calculated based on the event
times and the number of events at each time point.

In this process four parties are involved; the aggregator, the data stations, the client,
and the vantage6 server. In the diagram below the central part of the algorithm is
the aggregator, the partial parts are the data stations, the client is the party that
requests the analysis. Note that the vantage6 server is not shown in the diagram, as it
merely acts as a communication hub between data station, aggregator and researcher.

.. uml::

    !theme superhero-outline

    caption The central part of the algorithm is responsible for the \
          orchestration and aggregation\n of the algorithm. The partial \
          parts are executed on each node.


    |client|
    :request analysis;

    |central|
    :Collect organizations
    in collaboration;
    :Create partial tasks;

    |partial|
    :Get unique event times;

    |central|
    :Combine unique event times;
    :Create partial tasks;

    |partial|
    :Get KM event table;

    |central|
    :Combine KM event tables;

    |client|
    :Receive results;


Partials
--------
Partials are the computations that are executed on each node. The partials have access
to the data that is stored on the node. The partials are executed in parallel on each
node.

``get_unique_event_times``
^^^^^^^^^^^^^^^^^^^^^^^^^^
Get the local unique event times. Depending on the privacy gaurds set in the node, noise
might be added to the unique event times. The exact same noise applied in this step will
also be applied in the ``get_km_event_table`` step.

See the :ref:`privacy guards <privacy-guards>` section for more information.

``get_km_event_table``
^^^^^^^^^^^^^^^^^^^^^^
Calculates death counts, total counts, and at-risk counts at each unique event time.

Central
-------
The central part is responsible for the orchestration and aggregation of the algorithm.

``kaplan_meier_central``
^^^^^^^^^^^^^^^^^^^^^^^^
The central part is responsible for:

- Creating the partial tasks for the ``get_unique_event_times`` and ``get_km_event_table``
  partials.
- Combining the local unique event times to a global list of unique event times.
- Combining the local number of events per unique event time to a global list of number
  of events.



.. Describe the central function here.

