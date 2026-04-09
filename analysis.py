"""This module provides the analysis function for muon decay data.
"""
import numpy as np
import scipy.stats as stats
from lmfit.models import ExponentialModel, ConstantModel
from typing import NamedTuple

class FitResults(NamedTuple):
    a: float
    delta_a: float
    t_a: float
    p_a: float
    n0: float
    delta_n0: float
    t_n0: float
    p_n0: float
    tau: float
    delta_tau: float
    t_tau: float
    p_tau: float
    t_dof: int
    chisq: float
    p_chisq: float
    chisq_dof: int

def decayfit(bins, bincounts, n00=100, tau0=1.67):
    """Fit the decays in data to an exponential decay with constant
    noise and return the fit parameters.
    """
    muondecay = ExponentialModel()
    bg = ConstantModel()
    model = muondecay + bg
    init = bg.make_params(c=self.bincounts[-1])
    init += muondecay.make_params(amplitude=100, decay=1.67)
    nlm = model.fit(self.bincounts, init, x=self.tt)
    fit = nlm.eval(x=self.tt)
    dcount = nlm.eval_uncertainty(sigma=0.95)
    a = nlm.params['c'].value
    n0 = nlm.params['amplitude'].value
    tau = nlm.params['decay'].value
    delta_a = nlm.params['c'].stderr
    delta_n0 = nlm.params['amplitude'].stderr
    delta_tau = nlm.params['decay'].stderr
    t_a = a / delta_a
    t_n0 = n0 / delta_n0
    t_tau = tau / delta_tau
    t_dof = self.bincounts.size - 3
    p_a = 2 * (1 - stats.t.cdf(t_a, tdof))
    p_n0 = 2 * (1 - stats.t.cdf(t_n0, tdof))
    p_tau = 2 * (1 - stats.t.cdf(t_tau, tdof))
    fit_table = np.array([
        [a, delta_a, t_a, p_a],
        [n0, delta_n0, t_n0, p_n0],
        [tau, delta_tau, t_tau, p_tau],
    )
    return(fit_table, t_dof)

def fit_chisq(bins, bincounts, a, n0, tau):
    """Do a chi-square analysis on the muon fir results.
    """
    norm = n0 * tau * (1 - np.exp(-20/tau)) + 20 * a
    ek = np.zeros(bins.size - 1)
    nn = np.sum(bincounts)
    for n in range(bins.size - 1):
        t0 = bins[n]
        t1 = bins[n+1]
        ek[n] = ((n0 * tau * (np.exp(-t0/tau) - np.exp(-t1/tau))
            + a*(t1 - t0)) / norm * nn)
    # The number of degrees of freedom for the chi square calculation is
    # the number of bins minus the number of parameters (3) minus one.
    dof = bincounts.size - 4
    # The ddof parameter is the number of parameters (3).
    chisq = stats.chisquare(bincounts, ek, ddof=3)
    return chisq, dof

def data_analysis(data, bins=None, n00=100, tau0=1.67):
    """Fit muon decay data and do a chi-square analysis of the result.
    The fit parameters and chi-square results are returned in a
    FitResults class named tuple with the following fields: a, delta_a,
    t_a, p_a, n0, delta_n0, t_n0, p_n0, tau, delta_tau, t_tau, p_tau,
    t_dof, chisq, p_chisq, and chisq_dof.
    """
    if bins == None:
        bins = np.arange(0, 21, 1)
    bincounts, _ = np.hist(data, bins=bins)
    fit_table, t_dof = decayfit(bins, bincounts, n00, tau0)
    a, delta_a, t_a, p_a = fit_table[0]
    n0, delta_n0, t_n0, p_n0 = fit_table[1]
    tau, delta_tau, t_tau, p_tau = fit_table[2]
    chisq, chi_dof = fit_chisq(bins, bincounts, a, n0, tau)
    result = FitResults(a, delta_a, t_a, p_a, n0, delta_n0, t_n0,
        p_n0, tau, delta_tau, t_tau, p_tau, t_dof, chisq, p_chisq,
        chisq_dof)
    return result
    
