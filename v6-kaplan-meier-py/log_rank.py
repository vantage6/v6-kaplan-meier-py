import pandas as pd

from scipy.stats import chi2


def compute_log_rank_from_km_multiple(
    *dfs: pd.DataFrame,
    time_column_name: str,
) -> tuple[float, float, pd.DataFrame]:
    """
    Compute log rank test from N Kaplan-Meier tables

    Parameters
    ----------
    *dfs : list of pandas.DataFrame
        Variable number of DataFrames, each containing columns:
        - time_column_name
            The event time column name. Note that `time_column_name` is not the
            column name but the actual column in the DataFrame containing event times
        - 'observed '
            Number of events at each time point
        - 'at_risk'
            Number at risk at each time point
        - 'censored'
            Number of censored events at each time point
    time_column_name : str
        Name of the column containing event times in each DataFrame

    Returns
    -------
    chi_square : float
        The chi-square statistic
    p_value : float
        The p-value for the test
    stats : pd.DataFrame
        DataFrame containing the test statistics

    Example
    -------
    >>> chi_square_stat, p_value, stats = compute_log_rank_from_km_multiple(
    >>>     df1, df2, df3, time_column_name="TIME_AT_RISK"
    >>> )
    """
    # Number of groups
    n_groups = len(dfs)

    if n_groups < 2:
        raise ValueError("At least two groups are required for the log-rank test")

    # Combine time points and sort
    all_times = pd.concat(
        [
            df[[time_column_name, "observed", "at_risk"]].assign(group=i)
            for i, df in enumerate(dfs, 1)
        ]
    ).sort_values(time_column_name)

    # Create stats dataframe
    stats = pd.DataFrame()
    stats["time"] = all_times[time_column_name].unique()

    # Get observed and at_risk for each group at each time point
    for group in range(1, n_groups + 1):
        group_data = all_times[all_times["group"] == group]
        stats[f"observed_{group}"] = [
            group_data[group_data[time_column_name] == t]["observed"].sum()
            for t in stats["time"]
        ]
        stats[f"at_risk_{group}"] = [
            (
                group_data[group_data[time_column_name] == t]["at_risk"].iloc[0]
                if len(group_data[group_data[time_column_name] == t]) > 0
                else 0
            )
            for t in stats["time"]
        ]

    # Calculate totals
    stats["total_events"] = sum(stats[f"observed_{i}"] for i in range(1, n_groups + 1))
    stats["total_at_risk"] = sum(stats[f"at_risk_{i}"] for i in range(1, n_groups + 1))

    # Calculate expected events for each group
    for group in range(1, n_groups + 1):
        stats[f"expected_{group}"] = stats[f"at_risk_{group}"] * (
            stats["total_events"] / stats["total_at_risk"]
        )

    # Calculate chi-square statistic
    chi_square = 0
    for group in range(1, n_groups + 1):
        O = stats[f"observed_{group}"].sum()
        E = stats[f"expected_{group}"].sum()
        if E > 0:  # Avoid division by zero
            chi_square += ((O - E) ** 2) / E

    # Degrees of freedom is (number of groups - 1)
    df = n_groups - 1
    p_value = 1 - chi2.cdf(chi_square, df=df)

    return chi_square, p_value, stats


def print_interpretation(chi_square_stat: float, p_value: float, n_groups: int) -> None:
    """
    Interpret and print the results of the multiple group log-rank test.

    Parameters
    ----------
    chi_square_stat : float
        The chi-square test statistic from the log-rank test
    p_value : float
        The p-value from the log-rank test
    n_groups : int
        Number of groups being compared
    """
    print(f"Log-rank test results for {n_groups} groups:")
    print(f"Chi-square statistic: {chi_square_stat:.4f}")
    print(f"Degrees of freedom: {n_groups - 1}")
    print(f"p-value: {p_value:.4f}\n")

    print("Conclusion:")
    if p_value < 0.05:
        print(
            "The log-rank test shows a statistically significant difference between "
            f"the survival curves (p = {p_value:.4f}). This suggests that there are "
            "significant differences in survival experiences among the {n_groups} "
            "groups."
        )
    else:
        print(
            "The log-rank test does not show a statistically significant difference "
            f"between the survival curves (p = {p_value:.4f}). This suggests that "
            f"there is not enough evidence to conclude that the survival experiences "
            f"differ among the {n_groups} groups."
        )
