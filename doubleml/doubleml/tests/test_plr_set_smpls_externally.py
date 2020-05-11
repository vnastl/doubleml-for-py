import numpy as np
import pytest
import math

from sklearn.base import clone
from sklearn.linear_model import LinearRegression, Lasso

import doubleml as dml

from doubleml.tests.helper_general import get_n_datasets


# number of datasets per dgp
n_datasets = get_n_datasets()

@pytest.fixture(scope='module',
                params = range(n_datasets))
def idx(request):
    return request.param


@pytest.fixture(scope='module',
                params = [LinearRegression()])
def learner(request):
    return request.param


@pytest.fixture(scope='module',
                params = ['IV-type', 'DML2018'])
def inf_model(request):
    return request.param


@pytest.fixture(scope='module',
                params = ['dml1', 'dml2'])
def dml_procedure(request):
    return request.param

@pytest.fixture(scope='module',
                params = [1, 3])
def n_rep_cross_fit(request):
    return request.param


@pytest.fixture(scope="module")
def dml_plr_smpls_fixture(generate_data1, idx, learner, inf_model, dml_procedure, n_rep_cross_fit):
    n_folds = 3

    # collect data
    data = generate_data1[idx]
    X_cols = data.columns[data.columns.str.startswith('X')].tolist()

    # Set machine learning methods for m & g
    ml_learners = {'ml_m': clone(learner),
                   'ml_g': clone(learner)}

    np.random.seed(3141)
    dml_plr_obj = dml.DoubleMLPLR(data, X_cols, 'y', ['d'],
                              ml_learners,
                              n_folds,
                              n_rep_cross_fit,
                              inf_model,
                              dml_procedure)

    dml_plr_obj.fit()

    smpls = dml_plr_obj.smpls

    dml_plr_obj2 = dml.DoubleMLPLR(data, X_cols, 'y', ['d'],
                               ml_learners,
                               inf_model=inf_model,
                               dml_procedure=dml_procedure,
                               draw_sample_splitting=False)
    dml_plr_obj2.set_sample_splitting(smpls)
    dml_plr_obj2.fit()
    
    res_dict = {'coef': dml_plr_obj.coef,
                'coef2': dml_plr_obj2.coef,
                'se': dml_plr_obj.se,
                'se2': dml_plr_obj2.se}

    return res_dict


def test_dml_plr_coef(dml_plr_smpls_fixture):
    assert math.isclose(dml_plr_smpls_fixture['coef'],
                        dml_plr_smpls_fixture['coef2'],
                        rel_tol=1e-9, abs_tol=1e-4)


def test_dml_plr_se(dml_plr_smpls_fixture):
    assert math.isclose(dml_plr_smpls_fixture['se'],
                        dml_plr_smpls_fixture['se2'],
                        rel_tol=1e-9, abs_tol=1e-4)

