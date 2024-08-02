Kaplan Meier
============

Description
-----------

This `vantage6 <https://vantage6.ai>`_ algorithm computes the Kaplan-Meier curve
in a federated manner. Hence, it allows for the estimation of survival probabilities across
distributed datasets without sharing patient-specific information.

The Kaplan-Meier algorithm is a non-parametric statistic used to estimate the survival
function from lifetime data. In medical research, it is often used to measure the
fraction of patients that are alive for a certain amount of time after treatment.

Authors
-------

* B. Gottardelli [#unicatt]_ `benedetta.gottardelli@gmail.com <benedetta.gottardelli@gmail.com>`_
* A. Lobo Gomes [#maastro]_ `aiara.lobogomes@maastro.nl <aiara.lobogomes@maastro.nl>`_
* I\. Zhovannik [#MDW]_ `ivan.zhovannik@medicaldataworks.nl <ivan.zhovannik@medicaldataworks.nl>`_
* L. Sanchez [#MDW]_ `luis.sanchezgomez@medicaldataworks.nl <luis.sanchezgomez@medicaldataworks.nl>`_
* F.C. Martin [#IKNL]_ `f.martin@iknl.nl <mailto:f.martin@iknl.nl>`_
* A.J. van Gestel [#IKNL]_ `a.vangestel@iknl.nl <mailto:a.vangestel@iknl.nl>`_

Thanks to M.J. Bijlsma [#IKNL]_ for the suggestion of applying Poisson noise to the event times.

.. [#unicatt] Università Cattolica del Sacro Cuore, Italy
.. [#maastro] MAASTRO Clinic, The Netherlands
.. [#MDW] Medical Data Works (MDW), The Netherlands
.. [#IKNL] Netherlands Comprehensive Cancer Organisation (IKNL), The Netherlands

Source code
-----------

Source code is available on `GitHub <https://github.com/vantage6/v6-kaplan-meier-py>`_.


Contents
--------

.. toctree::
   :maxdepth: 2
   :hidden:

   self

.. toctree::
    :maxdepth: 2

    v6-kaplan-meier-py/implementation
    v6-kaplan-meier-py/usage
    v6-kaplan-meier-py/privacy
    v6-kaplan-meier-py/validation
    v6-kaplan-meier-py/references
