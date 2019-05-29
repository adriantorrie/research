"""
Logic regarding sequential bootstrapping from chapter 4.
"""

import pandas as pd
import numpy as np


def get_ind_matrix(triple_barrier_events):
    """
    Snippet 4.3, page 64, Build an Indicator Matrix
    Get indicator matrix
    :param triple_barrier_events: (pd.DataFrame): triple barrier events from labeling.get_events
    :return: (pd.DataFrame) indicator binary matrix indicating what (price) bars influence the label for each observation
    """
    if bool(triple_barrier_events.isnull().values.any()) is True or bool(
            triple_barrier_events.index.isnull().any()) is True:
        raise ValueError('NaN values in triple_barrier_events, delete nans')

    label_endtime = triple_barrier_events.t1
    bar_index = list(triple_barrier_events.index)  # generate index for indicator matrix from t1 and index
    bar_index.extend(triple_barrier_events.t1)
    bar_index = sorted(list(set(bar_index)))  # drop duplicates and sort

    ind_mat = pd.DataFrame(0, index=bar_index, columns=range(label_endtime.shape[0]))  # zero indicator matrix
    for i, (t_0, t_1) in enumerate(
            label_endtime.iteritems()):  # TODO: make for loop faster (move away from pd.DataFrame and loc)
        ind_mat.loc[t_0:t_1, i] = 1
    return ind_mat


def get_ind_mat_average_uniqueness(ind_mat):
    """
    Snippet 4.4. page 65, Compute Average Uniqueness
    Average uniqueness from indicator matrix

    :param ind_mat: (np.matrix) indicator binary matrix
    :return: (np.matrix) matrix with label uniqueness
    """
    conc = ind_mat.sum(axis=1)  # concurrency
    average = ind_mat / conc[:, None]
    return average.T


def seq_bootstrap(ind_mat, sample_length=None, compare=False):
    """
    Snippet 4.5, Snippet 4.6, page 65, Return Sample from Sequential Bootstrap
    Generate a sample via sequential bootstrap.
    Note: Moved from pd.DataFrame to np.matrix for performance increase

    :param ind_mat: (data frame) indicator matrix from triple barrier events
    :param sample_length: (int) Length of bootstrapped sample
    :param compare: (boolean) flag to print standard bootstrap uniqueness vs sequential bootstrap uniqueness
    :return: (array) of bootstrapped samples indexes
    """

    random_state = np.random.mtrand.RandomState()

    if sample_length is None:
        sample_length = ind_mat.shape[1]

    phi = []
    while len(phi) < sample_length:
        avg_unique = np.array([])
        for i in ind_mat:  # TODO: for performance increase, this can be parallelized
            ind_mat_reduced = ind_mat[phi + [i]]  # reduce ind_mat (append i label as last column)
            # get i label uniqueness vector (which corresponds to the last column of get_ind_mat_average_uniqueness)
            label_uniqueness = get_ind_mat_average_uniqueness(ind_mat_reduced.values)[-1]
            label_av_uniqueness = label_uniqueness[label_uniqueness > 0].mean()  # get average label uniqueness
            avg_unique = np.append(avg_unique, label_av_uniqueness)
        prob = avg_unique / avg_unique.sum()  # draw prob
        phi += [random_state.choice(ind_mat.columns, p=prob)]

    if compare is True:
        standard_indx = np.random.choice(ind_mat.columns, size=sample_length)
        standart_unq = get_ind_mat_average_uniqueness(ind_mat[standard_indx].values)
        standard_unq_mean = standart_unq[standart_unq > 0].mean()

        sequential_unq = get_ind_mat_average_uniqueness(ind_mat[phi].values)
        sequential_unq_mean = sequential_unq[sequential_unq > 0].mean()
        print('Standard uniqueness: {}\nSequential uniqueness: {}'.format(standard_unq_mean, sequential_unq_mean))

    return phi
