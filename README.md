<h1 align="center">
  <br>
  <a href="https://vantage6.ai"><img src="https://github.com/IKNL/guidelines/blob/master/resources/logos/vantage6.png?raw=true" alt="vantage6" width="400"></a>
</h1>

<h3 align=center>
    A Privacy Enhancing Technologies Operations (PETOps) platform
</h3>

![Discord](https://img.shields.io/discord/:643526403207331841)

--------------------
# Kaplan-Meier on OHDSI

This repository contains an implementation of the Kaplan-Meier curve calculation designed for federated learning environments via the vantage6 framework. It allows for the estimation of survival probabilities across distributed datasets without sharing the patient-specific information. This method supports privacy-enhancing data analysis in medical research and other fields where event-time analysis is critical.

The algorithm operates within the vantage6 infrastructure, a platform supporting federated learning, to enable institutions to perform survival analysis while maintaining data privacy.

This initial version has been updated and adapted for the [BlueBerry](https://euracan.eu/registries/blueberry/) project.

Follow the instructions in subsequent sections to set up and execute the federated Kaplan-Meier analysis.

*TODO: Add a link to the documentation.*

## Acknowledgements
The initial idea was based on contributions from Benedetta Gottardelli [benedetta.gottardelli@unicatt.it](mailto:benedetta.gottardelli@unicatt.it). It was further developed by [Medical Data Works](https://github.com/mdw-nl/v6-km-studyathon) and finally adapated by the members of the [BlueBerry](https://euracan.eu/registries/blueberry/) project.


## Privacy Gaurds

### Minimum number of organizations
In order to minimize the risk of reconstruction the number of organizations should be at least 3. The value of this threshold can be changed by setting `KAPLAN_MEIER_MINIMUM_ORGANIZATIONS`. Note that this threshold can be set by the aggregator party only!

> [!Important]
> In case the aggregator node does not supply this environment variable, the default value of 3 will be used.


### Minimum number of records
The algorithm will only share information if there are at least n records present in the local dataset. This can be set using the variable `KAPLAN_MEIER_MINIMUM_NUMBER_OF_RECORDS`.

> [!Important]
> In case the node does not supply this environment variable, the default value of 3 will be used.

### Fix event time column
In order to limit the options the user has for selecting the event time column the `KAPLAN_MEIER_ALLOWED_EVENT_TIME_COLUMNS_REGEX` can be set to a comma separated list. Each element in the list can be a regex pattern.

> [!Important]
> In case the node does not supply this environment variable, the default value of `.*` will be used. Which means that any column can be used. In order to limit the options the user has to select the event time column, the regex can be set to a more specific value. E.g. `^event_time$` will only allow the column named `event_time` to be used.

### Noise to event times
In order to protect the individual event times noise can be added to this column. The column is user defined, see “Fixed event time column” section.

The type of noise can be set through `KAPLAN_MEIER_TYPE_NOISE`. This can be one of the following:

* `NONE` – no noise will be added to the time event columns
* `GAUSSIAN` – Gaussian noise will be added, the amount of noise can be controlled to a signal to noise ratio: `KAPLAN_MEIER_PRIVACY_SNR_EVENT_TIME`. The SNR is defined as the amount of noise compared to the standard deviation of the original signal.
* `POISSON` – Poisson noise will be applied.

> [!Important]
> In case the node does not supply this environment variable, the default value of `POISSON` will be used.

## Build
In order to build its best to use the makefile.

```bash
make image VANTAGE6_VERSION=4.5.5
```