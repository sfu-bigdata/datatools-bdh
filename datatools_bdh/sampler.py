"""Construct random and deterministic sets of numbers that follow
   some given distribution and obey constraints.

   For instance, to draw 100 samples from a Normal distribution that fall
   within the bounds [-.5, .5] call:
   ```
    lub = .5
    nsamples = 100
    s = make_normal_bounded(-lub, +lub, nsamples=nsamples,
                            oversample=10,
                            sigma=lub*.3
                           )
    import matplotlib.pyplot as plt
    print(f"Generated {len(s)} samples from a constrained Gaussian distribution.")
    plt.hist(s, bins=min(int(nsamples/2), 100));
    plt.xlim([-lub, +lub])
   ```
"""

import scipy.stats as sps
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Inverse transform sampling

class ITFSampler:
    """Instantiate this class via make sampler"""
    def __init__(self,
                distribution=sps.exponpow,
                cdf_miniv=0.01,
                cdf_nsteps=100,
                **kwargs
            ):
        self.cdf_miniv = cdf_miniv
        self.distribution = distribution
        self.cdf_nsteps = cdf_nsteps
        self.cdf_lb = self.cdf_miniv
        self.cdf_ub = 1 - self.cdf_miniv
        self.x = np.linspace(self.distribution.ppf(self.cdf_lb, **kwargs),
                             self.distribution.ppf(self.cdf_ub, **kwargs), self.cdf_nsteps)
        self.x0 = np.linspace(self.cdf_lb, self.cdf_ub, self.cdf_nsteps)
        self.xs = pd.DataFrame(self.distribution.cdf(self.x, **kwargs))
        self.xsi = self.xs.reset_index().set_index(0)['index']

    def __call__(self, y):
        return (self.xsi.reindex(np.atleast_1d(y), method='ffill', fill_value=0)
                / self.cdf_nsteps * (self.cdf_ub - self.cdf_lb) + self.cdf_lb)
        # TODO check if this should be divided by (cdf_nsteps-1) instead of cdf_nsteps
        # to enable reaching the upper bound


# ---------------------------------------------------------------------------
# sampling with constraints

# If less than this number of points pass the sample constraint test,
# raise an error.
SAMPLE_CONSTRAINT_RATE = 1e-4

def make_sample_constrained(in_sample,
                            draw_sample, nsamples, oversample=1,
                            sample_constraint_rate=SAMPLE_CONSTRAINT_RATE,
                            unsorted=False):
    """Draw a number samples from a distribution with constraints.

    Args:
        in_sample   - function that determines whether the value in its argument
                      satisfies the constraint
        draw_sample - function to generate random sample of size given as argument
        nsamples    - total number of sample values to generate
        oversample  - internally create `oversample` multiple of nsamples, then sort 
                      and return every n-th sample such that only nsamples are retained.
        sample_constraint_rate - if the ratio of samples that pass the in_sample test
                                 is below this rate, raise an error
        unsorted    - if True, return the sample values unsorted. If `oversample` is more than 
                      1, then requesting an unsorted sample requires O(nsamples) more work
                      than the sorted output, produced by default. If `oversample` is 1, i.e.
                      no oversampling is done, then unsorted output is more efficient.

    Returns:
        numpy array of sample values

    See also:
        make_sample_bounded
    """
    samples = []
    nsamples *= oversample
    nsampled = 0
    while len(samples) < nsamples:
        n_add = max(nsamples - len(samples), 0)
        s = draw_sample(nsamples)
        s = list(filter(in_sample, s))
        samples.extend(s[:n_add])
        nsampled += nsamples
        if sample_constraint_rate:
            min_samples = nsampled * sample_constraint_rate
            if min_samples > 1 and len(samples) < min_samples:
                raise f"Failed to obtain at least one sample per {int(1/sample_constraint_rate)} trials"
    if not unsorted:
        return sorted(samples)[::oversample]
    else:
        if oversample == 1:
            return samples
        sel_mask = np.zeros(len(samples), np.bool)
        sorted_idx = np.argsort(samples)
        sel_mask[sorted_idx[::oversample]] = True
        return samples[sel_mask]

def make_sample_bounded(lb, ub, draw_sample, nsamples, oversample=1, **kwargs):
    """Draw a number of samples from a distribution with enforced lower and upper bound.
    Args:
        lb, ub - lower and upper bound of range
        all other arguments - see make_sample_constrained
    Returns:
        numpy array of sample values
    """
    def in_range(x):
        return x >= lb and x <= ub
    return make_sample_constrained(in_range, draw_sample,
                                   nsamples, oversample, **kwargs)

def make_normal_bounded(lb, ub, nsamples, oversample=1, mu=None, sigma=None, **kwargs):
    """Draw a number of samples from a normal distribution with enforced lower and upper bound."""
    if mu is None:
        mu = lb + 0.5 * (ub - lb)
    if sigma is None:
        sigma = lu_range * .5
    draw_sample = lambda nsamples: np.random.normal(mu, sigma, nsamples)
    return make_sample_bounded(lb, ub, draw_sample, nsamples, oversample, **kwargs)

def make_exponential_bounded(lb, ub, nsamples, oversample=1, scale=1.0, **kwargs):
    """Draw a number of samples from an exponential distribution with enforced lower and upper bound."""
    draw_sample = lambda nsamples: np.random.exponential(scale=scale, size=nsamples)
    return make_sample_bounded(lb, ub, draw_sample, nsamples, oversample, **kwargs)

def make_power_bounded(lb, ub, nsamples, oversample=1, a=1.0, **kwargs):
    """Draw a number of samples from a power distribution with enforced lower and upper bound."""
    draw_sample = lambda nsamples: np.random.power(a=a, size=nsamples)
    return make_sample_bounded(lb, ub, draw_sample, nsamples, oversample, **kwargs)
