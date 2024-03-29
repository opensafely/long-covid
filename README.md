# Clinical coding of long COVID in English primary care: a federated analysis of 58 million patient records in situ using OpenSAFELY

This is the code and configuration for our paper.

* The published peer-reviewed paper is available in the [British Journal of General Practice](https://doi.org/10.3399/BJGP.2021.0301)
* Raw model outputs, including charts, crosstabs, etc, are in `released_outputs/`
* If you are interested in how we defined our variables, take a look at the [study definition](analysis/study_definition_cohort.py); this is written in `python`, but non-programmers should be able to understand what is going on there
* If you are interested in how we defined our code lists, look in the [codelists folder](./codelists/)
* Developers and epidemiologists interested in the framework should review [the OpenSAFELY documentation](https://docs.opensafely.org)
* The preprint version of the paper is [here](https://doi.org/10.1101/2021.05.06.21256755)

# About the OpenSAFELY framework

The OpenSAFELY framework is a secure analytics platform for
electronic health records research in the NHS.

Instead of requesting access for slices of patient data and
transporting them elsewhere for analysis, the framework supports
developing analytics against dummy data, and then running against the
real data *within the same infrastructure that the data is stored*.
Read more at [OpenSAFELY.org](https://opensafely.org).
