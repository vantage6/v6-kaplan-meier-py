import time
from vantage6.tools.util import info
from itertools import product
import pandas as pd
import numpy as np


def master(client, data, expl_vars, censor_col, data_set='train', organization_ids=None):
    """This package does the following:
            2. Correlation-based feature selection
            3. Data normalization (both training and test)
            4. Saves results in each node
    """
    fold = '/mnt/data/'
    # Info messages can help you when an algorithm crashes. These info
    # messages are stored in a log file which is send to the server when
    # either a task finished or crashes.
    info('Collecting participating organizations')

    # Collect all organization that participate in this collaboration.
    # These organizations will receive the task to compute the partial.
    # organizations = client.get_organizations_in_my_collaboration()
    # ids = [organization.get("id") for organization in organizations]

    if isinstance(organization_ids, list) is False:
        organizations = client.get_organizations_in_my_collaboration()
        ids = [organization.get("id") for organization in organizations]
    else:
        ids = organization_ids

    info(f'sending task to organizations {ids}')

    ##### 2) Correlation-based feature selection #####

    kwargs_dict = {'expl_vars': expl_vars + [censor_col], 'data_set': data_set}
    method = 'average_partial'
    # results = subtaskLauncher(client, [method, kwargs_dict, ids])

    task = client.create_new_task(
        input_={
            'method': method,
            'kwargs': kwargs_dict
        },
        organization_ids=ids
    )

    info("Waiting for results")
    task_id = task.get("id")
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)

    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))

    # Now we can combine the partials to a global average.
    global_sum = 0
    global_count = 0

    for output in results:
        global_sum += output["sum"]
        global_count += output["count"]

    average = global_sum / global_count
    #average.to_csv(fold + "train_means.csv")
    #pd.DataFrame(np.array([global_count]), columns=['tot']).to_csv(fold + "train_total_patients.csv")

    info('Requesting second partial computation')

    kwargs_dict = {'expl_vars': expl_vars + [censor_col], 'average': average, 'data_set': data_set}
    method = 'corr_partial'
    # results = subtaskLauncher(client, [method, kwargs_dict, ids])

    task = client.create_new_task(
        input_={
            'method': method,
            'kwargs': kwargs_dict
        },
        organization_ids=ids
    )

    info("Waiting for results")
    task_id = task.get("id")
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)

    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))

    # Now we can combine the partials to a global average.

    sum_prod = 0
    for output in results:
        sum_prod += output["codeviances"]

    sum_prod = sum_prod.reset_index()
    sum_prod.columns = ["Var1", "Var2", "SumProd"]

    var = sum_prod[sum_prod["Var1"] == sum_prod["Var2"]].drop_duplicates()
    std_cols = var[['Var1', 'SumProd']].set_index("Var1")['SumProd']
    #std_cols.to_csv(fold + "train_std.csv")

    sum_prod = sum_prod.merge(var, on="Var1", suffixes=("", "_v1"))
    sum_prod = sum_prod.merge(var, on="Var2", suffixes=("", "_v2"))

    ## Pearson's coefficient computation
    sum_prod["rho"] = sum_prod["SumProd"] / (sum_prod["SumProd_v1"] * sum_prod["SumProd_v2"]) ** 0.5
    correlationMatrix = pd.pivot_table(sum_prod, values="rho", index="Var1", columns="Var2", aggfunc='mean')

    #correlationMatrix.to_csv(fold + "train_correlationMatrix.csv")

    corr_ff = correlationMatrix[expl_vars]
    corr_fc = correlationMatrix[censor_col]
    best_subset, best_value = CFS(corr_fc, corr_ff)

    #pd.DataFrame(best_subset, columns=["sel_expl_vars"]).to_csv(fold + "sel_expl_vars.csv")

    ##### 3) Data normalization (both training and test)  #####

    info('Normalize data!')

    # results = subtaskLauncher(client,
    #                           ['normalize',
    #                            {'expl_vars': expl_vars, 'mean_cols': average, 'std_cols': std_cols},
    #                            ids])

    task = client.create_new_task(
        input_={
            'method': 'normalize',
            'kwargs': {'expl_vars': expl_vars, 'mean_cols': average, 'std_cols': std_cols}
        },
        organization_ids=ids
    )

    info("Waiting for results")
    task_id = task.get("id")
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)

    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))

    info('save results')
    # results = subtaskLauncher(client, ['save_results', {'correlationMatrix': correlationMatrix, 'best_subset':
    # best_subset, 'average': average, 'std_cols': std_cols, 'global_count': global_count}, ids])
    print(correlationMatrix)
    task = client.create_new_task(
        input_={
            'method': 'save_results',
            'kwargs': {'correlationMatrix': correlationMatrix
                , 'best_subset': best_subset, 'average': average,'std_cols': std_cols, 'global_count': global_count}
        },
        organization_ids=ids
    )

    info("Waiting for results")
    task_id = task.get("id")
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)

    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))

    return {"correlationMatrix": correlationMatrix, 'best_subset': best_subset}


def RPC_save_results(data, correlationMatrix, best_subset, average, std_cols, global_count):
    fold = '/mnt/data/'
    average.to_csv(fold + "train_means.csv")
    pd.DataFrame(np.array([global_count]), columns=['tot']).to_csv(fold + "train_total_patients.csv")
    correlationMatrix.to_csv(fold + "train_correlationMatrix.csv")
    pd.DataFrame(best_subset, columns=["sel_expl_vars"]).to_csv(fold + "sel_expl_vars.csv")
    std_cols.to_csv(fold + "train_std.csv")
    return 'ok'


def RPC_normalize(data, expl_vars, mean_cols, std_cols):
    fold = '/mnt/data/'
    # nomalize the training set
    file = fold + 'data_train.csv'
    df = pd.read_csv(file)
    df[expl_vars] = (df[expl_vars] - mean_cols[expl_vars]) / std_cols[expl_vars]
    df.to_csv(fold + 'norm_data_train.csv', index=False)

    # normalize the test set
    file = fold + 'data_test.csv'
    df = pd.read_csv(file)
    df[expl_vars] = (df[expl_vars] - mean_cols[expl_vars]) / std_cols[expl_vars]
    df.to_csv(fold + 'norm_data_test.csv', index=False)


def CFS(corr_fc, corr_ff):
    bestMerit = -1
    best_value = -1
    subset = []
    queue = []
    nFails = 0

    # list for visited nodes
    visited = []

    # counter for backtracks
    n_backtrack = 0

    # limit of backtracks
    max_backtrack = 5

    queue = PriorityQueue()
    queue.push(subset, bestMerit)

    # repeat until queue is empty
    # or the maximum number of backtracks is reached
    while not queue.isEmpty():
        # get element of queue with highest merit
        subset, priority = queue.pop()
        # print(subset, priority)

        # check whether the priority of this subset
        # is higher than the current best subset
        if (priority < best_value):
            n_backtrack += 1
        else:
            best_value = priority
            best_subset = subset
            # print(best_value, best_subset)

        # goal condition
        if n_backtrack == max_backtrack:
            break

        # iterate through all features and look of one can
        # increase the merit
        for feature in list(corr_ff):
            temp_subset = subset + [feature]

            # check if this subset has already been evaluated
            for node in visited:
                if set(node) == set(temp_subset):
                    break
            # if not, ...
            else:
                # ... mark it as visited
                visited.append(temp_subset)
                # ... compute merit
                merit = getMerit(temp_subset, corr_fc, corr_ff)  # (temp_subset, label)
                # and push it to the queue
                queue.push(temp_subset, merit)
    return best_subset, best_value


def getMerit(subset, corr_fc, corr_ff):
    k = len(subset)
    rcf = abs(corr_fc[subset]).mean()
    if k > 1:
        sub_corr_ff = corr_ff[subset].loc[subset]
        sub_corr_ff.values[np.tril_indices_from(sub_corr_ff.values)] = np.nan

        sub_corr_ff = abs(sub_corr_ff)
        rff = sub_corr_ff.unstack().mean()
    else:
        rff = 0

    return (k * rcf) / np.sqrt(k + k * (k - 1) * rff)


class PriorityQueue:
    def __init__(self):
        self.queue = []

    def isEmpty(self):
        return len(self.queue) == 0

    def push(self, item, priority):
        """
        item already in priority queue with smaller priority:
        -> update its priority
        item already in priority queue with higher priority:
        -> do nothing
        if item not in priority queue:
        -> push it
        """
        for index, (i, p) in enumerate(self.queue):
            if (set(i) == set(item)):
                if (p >= priority):
                    break
                del self.queue[index]
                self.queue.append((item, priority))
                break
        else:
            self.queue.append((item, priority))

    def pop(self):
        # return item with highest priority and remove it from queue
        max_idx = 0
        for index, (i, p) in enumerate(self.queue):
            if (self.queue[max_idx][1] < p):
                max_idx = index
        (item, priority) = self.queue[max_idx]
        del self.queue[max_idx]
        return (item, priority)


def data_selector(data, data_set):
    fold = '/mnt/data/'
    if data_set == 'train':
        return pd.read_csv(fold + 'data_train.csv')
    elif data_set == 'test':
        return pd.read_csv(fold + 'data_test.csv')
    else:
        return data


def RPC_average_partial(data, expl_vars, data_set):
    """Compute the average partial

    The data argument contains a pandas-dataframe containing the local
    data from the node.
    """
    df = data_selector(data, data_set)
    # compute sum and N.
    # info(f'Extracting  {column_name}')

    local_sum = df[expl_vars].sum()
    local_count = len(df)
    print(local_sum, local_count)
    # return the values as a dict
    return {
        "sum": local_sum,
        "count": local_count
    }


def RPC_corr_partial(data, expl_vars, average, data_set):
    """Compute the average partial

    The data argument contains a pandas-dataframe containing the local
    data from the node.
    """
    # compute differences from mean 
    df = data_selector(data, data_set)

    cc = list(product(expl_vars, repeat=2))
    diff = df[expl_vars] - average

    # calculate all sum of products (codeviances)

    df_prod = pd.concat([diff[c[1]] * diff[c[0]] for c in cc], axis=1, keys=cc)
    diff_sum = df_prod.sum()

    print(diff_sum)
    # return the values as a dict
    return {
        "codeviances": diff_sum
    }


def subtaskLauncher(client, taskInfo):
    method, kwargs_dict, ids = taskInfo

    info(f'sending task to organizations {ids}')

    task = client.create_new_task(
        input_={
            'method': method,
            'kwargs': kwargs_dict
        },
        organization_ids=ids
    )

    info("Waiting for results")
    task_id = task.get("id")
    task = client.get_task(task_id)
    while not task.get("complete"):
        task = client.get_task(task_id)
        info("Waiting for results")
        time.sleep(1)
    # Once we know the partials are complete, we can collect them.
    info("Obtaining results")
    results = client.get_results(task_id=task.get("id"))
    return results
