import numpy as np
from sklearn.utils import check_X_y
from sklearn.model_selection import cross_val_predict
from sklearn.linear_model import LinearRegression

from scipy.stats import norm

from .double_ml_im import DoubleMLIM

class DoubleMLPIRM(DoubleMLIM):
    """
    Double Machine Learning for Partially Linear Regression
    """
    
    def _ml_nuisance(self, X, y, d):
        ml_m = self.ml_learners['ml_m']
        ml_g = self.ml_learners['ml_g']
        
        X, y = check_X_y(X, y)
        X, d = check_X_y(X, d)
        
        smpls = self._smpls
        smpls_d0 = self._smpls_d0
        smpls_d1 = self._smpls_d1
        
        # nuisance g
        self.g_hat0 = cross_val_predict(ml_g, X, y, cv = smpls_d0)
        self.g_hat1 = cross_val_predict(ml_g, X, y, cv = smpls_d1)
        
        # nuisance m
        self.m_hat = cross_val_predict(ml_m, X, d, cv = smpls, method='predict_proba')
        
        # compute residuals
        self._u_hat0 = y - self.g_hat0
        self._u_hat1 = y - self.g_hat1
        self._v_hat = d - self.m_hat
    
    def _compute_score_elements(self, d):
        inf_model = self.inf_model
        
        u_hat = self._u_hat
        v_hat = self._v_hat
        v_hatd = self._v_hatd
        
        if inf_model == 'ATE':
            self._score_b = self.g_hat1 - self.g_hat0 \
                            + np.divide(np.multiply(d, self._u_hat1), self.m_hat) \
                            + np.divide(np.multiply(1.0-d, self._u_hat0), 1.0 - self.m_hat)
            self._score_a = -1.0
        elif inf_model == 'ATTE':
            self._score_b = np.multiply(d, self._u_hat0) / p \
                            + np.divide(np.multiply(self.m_hat, np.multiply(1.0-d, self._u_hat0)),
                                        p*(1.0 - self.m_hat))
            p = np.mean(d)
            self._score_a = - d / p
        else:
            raise ValueError('invalid inf_model')
    
    
    def fit(self, X, y, d):
        """
        Fit doubleML model for PLR
        Parameters
        ----------
        X : 
        y : 
        d : 
        Returns
        -------
        self: resturns an instance of DoubleMLPLR
        """
        self._fit(X, y, d)
        
        return
    