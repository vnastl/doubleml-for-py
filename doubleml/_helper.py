import numpy as np

from sklearn.utils.multiclass import type_of_target
from sklearn.model_selection import cross_val_predict
from sklearn.base import clone
from sklearn.preprocessing import LabelEncoder

import warnings
from joblib import Parallel, delayed


def assure_2d_array(x):
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    elif x.ndim > 2:
        raise ValueError('Only one- or two-dimensional arrays are allowed')
    return x


def check_binary_vector(x, variable_name=''):
    # assure D binary
    assert type_of_target(x) == 'binary', 'variable ' + variable_name  + ' must be binary'
    
    if np.any(np.power(x, 2) - x != 0):
        raise ValueError('variable ' + variable_name + ' must be binary with values 0 and 1')


def _check_is_partition(smpls, n_obs):
    test_indices = np.concatenate([test_index for _, test_index in smpls])
    if len(test_indices) != n_obs:
        return False
    hit = np.zeros(n_obs, dtype=bool)
    hit[test_indices] = True
    if not np.all(hit):
        return False
    return True


def _fit(estimator, X, y, train_index, idx=None):
    estimator.fit(X[train_index, :], y[train_index])
    return estimator, idx


def _dml_cv_predict(estimator, X, y, smpls=None,
                    n_jobs=None, est_params=None, method='predict', return_train_preds=False):
    n_obs = X.shape[0]

    smpls_is_partition = _check_is_partition(smpls, n_obs)
    fold_specific_params = (est_params is not None) & (not isinstance(est_params, dict))
    fold_specific_target = isinstance(y, list)
    manual_cv_predict = (not smpls_is_partition) | return_train_preds | fold_specific_params | fold_specific_target

    if not manual_cv_predict:
        if est_params is None:
            # if there are no parameters set we redirect to the standard method
            return cross_val_predict(clone(estimator), X, y, cv=smpls, n_jobs=n_jobs, method=method)
        elif isinstance(est_params, dict):
            # if no fold-specific parameters we redirect to the standard method
            warnings.warn("Using the same (hyper-)parameters for all folds")
            return cross_val_predict(clone(estimator).set_params(**est_params), X, y, cv=smpls, n_jobs=n_jobs,
                                     method=method)
    else:
        if not smpls_is_partition:
            assert not fold_specific_target, 'combination of fold-specific y and no cross-fitting not implemented yet'
            assert len(smpls) == 1

        if method == 'predict_proba':
            assert not fold_specific_target  # fold_specific_target only needed for PLIV.partialXZ
            y = np.asarray(y)
            le = LabelEncoder()
            y = le.fit_transform(y)

        parallel = Parallel(n_jobs=n_jobs, verbose=0, pre_dispatch='2*n_jobs')

        if fold_specific_target:
            y_list = list()
            for idx, (train_index, _) in enumerate(smpls):
                xx = np.full(n_obs, np.nan)
                xx[train_index] = y[idx]
                y_list.append(xx)
        else:
            # just replicate the y in a list
            y_list = [y] * len(smpls)

        if est_params is None:
            fitted_models = parallel(delayed(_fit)(
                clone(estimator), X, y_list[idx], train_index, idx)
                                     for idx, (train_index, test_index) in enumerate(smpls))
        elif isinstance(est_params, dict):
            warnings.warn("Using the same (hyper-)parameters for all folds")
            fitted_models = parallel(delayed(_fit)(
                clone(estimator).set_params(**est_params), X, y_list[idx], train_index, idx)
                                     for idx, (train_index, test_index) in enumerate(smpls))
        else:
            assert len(est_params) == len(smpls), 'provide one parameter setting per fold'
            fitted_models = parallel(delayed(_fit)(
                clone(estimator).set_params(**est_params[idx]), X, y_list[idx], train_index, idx)
                                     for idx, (train_index, test_index) in enumerate(smpls))

        preds = np.full(n_obs, np.nan)
        if method == 'predict_proba':
            preds = np.full((n_obs, 2), np.nan)
        train_preds = list()
        for idx, (train_index, test_index) in enumerate(smpls):
            assert idx == fitted_models[idx][1]
            pred_fun = getattr(fitted_models[idx][0], method)
            if method == 'predict_proba':
                preds[test_index, :] = pred_fun(X[test_index, :])
            else:
                preds[test_index] = pred_fun(X[test_index, :])

            if return_train_preds:
                train_preds.append(pred_fun(X[train_index, :]))

        if return_train_preds:
            return preds, train_preds
        else:
            return preds
