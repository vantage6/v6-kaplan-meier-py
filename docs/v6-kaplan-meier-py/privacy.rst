Privacy
=======

.. _privacy-guards:

Guards
------

There are several guards in place to protect sharing too much information on individual
records:

- **Minumum number of data rows to participate**: The minimum number of data rows that a
  node must have to participate in the computation. This is to prevent nodes with very
  few data rows from being able to infer too much information about the data. By default
  this is set to 10. Node administrators can change this threshold by adding the
  following to their node configuration file:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS: 5

- **Set allowed event time columns**: The user is able to define the column that is used
  as the event time. To limit the columns that can be used by the user, the node
  administrator can set the allowed columns by defining regex expressions. By default
  all columns are allowed (regex expression: ``.*``). For example you want to allow all
  columns that start with `event_time` you can set the following in the node:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX: "^event_time.*"

  It is possible to define multiple regex expressions by separating them with a comma:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX: "^event_time.*,^event_date.*"

  If you want to define a specific column name you can set the following in the node:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS: "^event_time$,^event_time_2$"

- **Add noise to the unique event times**: In order to protect the individual event
  times noise can be added to the values in this column. It is possible to add Gaussian
  or Poission noise. Adding to much noise can make the results of the Kaplan-Meier
  analysis less accurate. The most convenient way to add noise is by applying Poission
  noise as the amount of noise is proportional to the value. By default, Poission noise
  is applied.

  Below, we detail how to use the different types of noise. But first, in case you do
  not want to add any noise you can set the following in the node:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_TYPE_NOISE: "NONE"

  .. important::

    Not adding any noise is not recommended. Your data would be at risk of being
    reconstructed.

  The methods that add noise rely on the `numpy.random` package. The random seed is set
  to a fixed value, so that the results are reproduced between successive calls. The
  node administrator can set the random seed to a fixed value  by adding the following
  to their node configuration:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_RANDOM_SEED: 1011

  This can be any positive integer.

  .. important::

      Do **not** share the random seed with anyone. This can be used to reproduce the
      data and might lead to privacy issues.

  .. warning::

      - If the user requests the unique event times multiple times, potentially the user
        can reconstruct the original data.
      - When this value has not been set the node will use 0 as the random seed. This
        should only be the case when testing.

  If you want to add Gaussian noise you can set the following in the node:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_TYPE_NOISE: "GAUSSIAN"
      KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME: 5

  The ``KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME`` parameter is the signal-to-noise ratio
  [#snr]_. Use this with caution as adding too much noise makes the results of the
  Kaplan-Meier analysis less accurate.

  .. figure:: ../_static/privacy_snr_event_time.png

    The effect of the signal-to-noise ratio on the Kaplan-Meier curve. The histogram
    shows the distribution of the event times.

  .. [#snr] K Mivule, Utilizing Noise Addition for Data Privacy, an Overview, 2013.

- **Minimum number of organizations**: The minimum number of organizations that must
  participate in the computation. This is to prevent the aggregation of too few
  organizations. By default this is set to 3. Node administrators can change this
  threshold by adding the following to their node configuration file:

  .. code-block:: yaml

    algorithm_env:
      KAPLAN_MEIER_MINIMUM_ORGANIZATIONS: 3

  .. hint::

    Note that this parameter can only be set by the aggregator node.

Data sharing
------------

.. list-table::
    :widths: 25 10 40 25
    :header-rows: 1

    * - Description
      - Source
      - Destination
      - Risk

    * - (Noised) Unique event times
      - Data station
      - Aggregator, Client
      - 🟠

    * - Kaplan-Meier event table
      - Data station
      - Aggregator, Client
      - 🟢



Vulnerabilities to known attacks
--------------------------------

.. Table below lists some well-known attacks. You could fill in this table to show
.. which attacks would be possible in your system.

.. list-table::
    :widths: 25 10 65
    :header-rows: 1

    * - Attack
      - Risk eliminated?
      - Risk analysis
    * - Reconstruction
      - ⚠
      - Event times might be reconstructed / obtained by the client. To mitigate this,
        noise should be added to the unique event times. The user should not send
        many requests with different random seeds or they may be able to reconstruct the
        unique event times.
    * - Differencing
      - ✔
      - Not applicable
    * - Deep Leakage from Gradients (DLG)
      - ✔
      - Not applicable
    * - Generative Adversarial Networks (GAN)
      - ✔
      - Not applicable
    * - Model Inversion
      - ✔
      - Not applicable
    * - Watermark Attack
      - ✔
      - Not applicable