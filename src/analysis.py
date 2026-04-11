"""This module provides the analysis functions for muon decay data.
"""
import numpy as np
import scipy.stats as stats
from lmfit.models import ExponentialModel, ConstantModel
from typing import NamedTuple

class FitResults(NamedTuple):
    """
    A NamedTupel that holds the results of the muon decay fit and
    chi-squared analysis.
    
    Attributes:
        a (float): Fit value of the constant noise rate
            (decays/microsecond)
        delta_a (float): Standard error of a
        t_a (float): T-statistic of a
        p_a (float): P-value of a (from T-test)
        n0 (float): Fit value of the number of muons in the decaying
            population
        delta_n0 (float): Standard error of n0
        t_n0 (float): T-statistic of n0
        p_n0 (float): P-value of n0 (from T-test)
        tau (float): Fit value of muon lifetime (microseconds)
        delta_tau (float): Standard error of tau
        t_tau (float): T-statistic of tau
        p_tau (float): P-value of tau (from T-test)
        t_dof (int): Number of degrees of freedom for the fit
            parameter T-tests
        rsquared (float): R-squared value for the fit
        fitcount (np.ndarray): Numpy array with the fit function
        	values for each bin
		dcount (np.ndarray): Numpy array with the fit value 95%
			confidence band width for each bin
        chisq (float): Chi-squared statistic for the fit
        p_chisq (float): P-value from chi-squared test of the fit
        chisq_dof (int): Number of degrees of freedom for chi-squared
            test of the fit
    """
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
    rsquared: float
    fitcount: np.ndarray
    dcount: np.ndarray
    chisq: float
    p_chisq: float
    chisq_dof: int

def decayfit(bins, bincounts, n00=100, tau0=1.67):
    """Fit the decays in data to an exponential decay with constant
    noise and return the fit parameters.
    
    fit_table, t_dof, rsquared = decayfit(bins, bincounts[, n00=100,
        tau0=1.67])
        
    Arguments
        bins (array of numbers): the bin boundaries for the decay histogram
            (see numpy.histogram)
        bincounts (array of int): array of counts of decays in each
            histogram bin
        n00 (int, optional): initial guess for number of decaying
            muons used in fit algorithm (default: 100)
        tau0 (float, optional): initial guess for mean muon lifetime
            value used in fit algorithm (default: 1.67)
    
    Returns
        fit_table (3 by 4 numpy.array of float): each row is the fit
            value, standard error, t-statistic, and p-value (from the
            T-test) for the parameters a (noise rate), n0 (muon
            population size), and tau (muon lifetime) with time units
            in microseconds
        t_dof (int): The number of degrees of freedom for the fit-parameter T-tests
        rsquared float: The R-squared value for the fit.
    """  
    tt = (bins[1:] + bins[0:-1]) / 2
    muondecay = ExponentialModel()
    bg = ConstantModel()
    model = muondecay + bg
    init = bg.make_params(c=bincounts[-1])
    init += muondecay.make_params(amplitude=n00, decay=tau0)
    nlm = model.fit(bincounts, init, x=tt)
    fitcount = nlm.eval(x=tt)
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
    t_dof = bincounts.size - 3
    p_a = 2 * (1 - stats.t.cdf(t_a, t_dof))
    p_n0 = 2 * (1 - stats.t.cdf(t_n0, t_dof))
    p_tau = 2 * (1 - stats.t.cdf(t_tau, t_dof))
    fit_table = np.array([
        [a, delta_a, t_a, p_a],
        [n0, delta_n0, t_n0, p_n0],
        [tau, delta_tau, t_tau, p_tau],
    ])
    return(fit_table, t_dof, nlm.rsquared, fitcount, dcount)

def fit_chisq(bins, bincounts, a, n0, tau):
    """Do a chi-square analysis on the muon fit results.
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

def data_analysis(data, bins=[], n00=100, tau0=1.67):
    """Fit muon decay data and do a chi-square analysis of the result.
    The fit parameters and chi-square results are returned in a
    FitResults class named tuple with the following fields: a, delta_a,
    t_a, p_a, n0, delta_n0, t_n0, p_n0, tau, delta_tau, t_tau, p_tau,
    t_dof, chisq, p_chisq, and chisq_dof.
    """
    if len(bins) == 0:
        bins = np.arange(0, 21, 1)
    bincounts, _ = np.histogram(data, bins=bins)
    fit_table, t_dof, rsquared, fitcount, dcount = decayfit(bins,
        bincounts, n00, tau0)
    a, delta_a, t_a, p_a = fit_table[0]
    n0, delta_n0, t_n0, p_n0 = fit_table[1]
    tau, delta_tau, t_tau, p_tau = fit_table[2]
    chisq, chisq_dof = fit_chisq(bins, bincounts, a, n0, tau)
    result = FitResults(a, delta_a, t_a, p_a, n0, delta_n0, t_n0,
        p_n0, tau, delta_tau, t_tau, p_tau, t_dof, rsquared,
        fitcount, dcount, chisq.statistic, chisq.pvalue, chisq_dof)
    return result
    
