'''
Created on Apr 20, 2013

@author: dimitris
'''
################################################################################

import numpy         as np
import numpy.random  as rn
import scipy.stats   as st
import scipy.special as sp

################################################################################

## random number distributions

def uniform(low = 0., high = 1., N = None):
    return st.uniform.rvs(low, high - low, N)
    
################################################################################

def normal(mean = 0., var = 1., N = None):
    return st.norm.rvs(mean, np.sqrt(var), N)
    
################################################################################

def beta(a = 1., b = 1., N = None):
    return st.beta.rvs(a, b, 0., 1., N)

################################################################################

def exponential(rate = 1., N = None):
    return st.expon.rvs(0., 1. / rate, N)

################################################################################

def gamma(shape = 2., scale = 1., N = None):
    return st.gamma.rvs(shape, 0., scale, N)

################################################################################

def invgamma(shape = 2., scale = 1., N = None):
    return st.invgamma.rvs(shape, 0., scale, N)

################################################################################

def categorical(w, N = 1):
    ws     = w.cumsum(0)
    ws[-1] = 1. 

    if w.ndim == 1:        
        idxs = ( ws < rn.uniform( size = (N,1) ) ).sum(1) 
    else:  ## assume w.ndim == 2
        idxs = ( ws < rn.uniform( size = w.shape[1] ) ).sum(0) 
        
    ## return
    return idxs
        
################################################################################
 
def stick(Ko, eta): 
    ## compute the cumulative sum of Ko
    cs = Ko.cumsum()
    
    ## generate beta variates 
    v     = rn.beta(1. + Ko, eta + cs[-1] - cs);
    v[-1] = 1.   ## this ensures that sum(w) = 1. 

    lv    = np.log(v)
    lcp   = np.log1p(-v[:-1]).cumsum()
    
    ## compute weights
    lw = np.r_[lv[0], lv[1:] + lcp]
    
    ## return        
    return lw
    
################################################################################

def rEta(eta, K, N, a = 2., b = 1.):
    ## compute x, r and p
    x  = beta(eta + 1., N)
    lx = np.log(x)
    r  = (a + K - 1.) / ( N * (b - lx) )
    p  = r / (r + 1.)
    
    ## update eta
    rnd     = uniform()
    eta_out = gamma(a + K, b - lx) if rnd < p else gamma(a + K - 1., b - lx)  
    
    ## return
    return eta_out 
    
################################################################################

## conjugate pairs

def exponential_rate(data, a0 = 2., b0 = 1.):
    ## compute shape and rate    
    a = a0 + data.size;
    b = b0 + data.sum();

    ## return
    return rn.gamma(a, 1. / b);


################################################################################

def gamma_scale(data, shape = 2., a0 = 2., b0 = 1.):
    ## compute shape and rate    
    a = a0 + data.size * shape;
    b = b0 + data.sum();

    ## return
    return 1. / gamma(a, 1. / b);


################################################################################

def gamma_shape_scale(data, shape, scale, lp0 = 0., q0 = 0., r0 = 0., s0 = 0.):
    ## compute log(p), q, r, s
    lp = lp0 + np.log(data).sum()
    q  = q0  + data.sum() 
    r  = r0  + data.size
    s  = s0  + data.size
    
    ## proposals    
    shape_ = shape * np.exp(0.01 * np.random.randn())
    scale_ = scale * np.exp(0.01 * np.random.randn())
    
    ## compute log-densities
    ll  = (shape  - 1.) * lp - q / scale  - r * sp.gammaln(shape)  - shape  * s * np.log(scale) 
    ll_ = (shape_ - 1.) * lp - q / scale_ - r * sp.gammaln(shape_) - shape_ * s * np.log(scale_)

    ## make Metropolis step     
    if ( ll_ > ll ) or ( np.random.rand() < np.exp(ll_ - ll) ):
        shape = shape_
        scale = scale_
    
    ## return
    return shape, scale


################################################################################


#def invgamma_rate(data, shape = 2., a0 = 2., b0 = 1.):
#    ## compute shape and rate    
#    a = a0 + data.size * shape;
#    b = b0 + (1. / data).sum();
#
#    ## return
#    return 1. / gamma(a, 1. / b);


################################################################################

def normal_mean_var(data, mu0 = -10., n0 = 1., a0 = 2., s0 = 1.):
    N      = data.size
    avg    = data.sum() / N
    dot    = ( (data - avg) ** 2 ).sum()
    resid0 = avg - mu0;
    
    ## compute mu, n, a, s
    mu = (n0 * mu0 + N * avg) / (n0 + N);
    n  = n0 + N;
    a  = a0 + N;
    s  = s0 + dot + N * n0 / (N + n0) * resid0 * resid0;    
    
    ## compute var and mean
    var  = invgamma(a * 0.5, s * 0.5);
    mean = normal(mu, var / n);

    ## return
    return mean, var

 
################################################################################

## density functions

def dLogNegBinomial(x, alpha, p):
    return sp.gammaln(x + alpha) - sp.gammaln(alpha) - sp.gammaln(x + 1.) + alpha * np.log(p) + x * np.log1p(-p)

################################################################################

def dLogPoisson(x, mu):
    return x * np.log(mu) - mu - sp.gammaln(x + 1.)
    
################################################################################

def dLogNormal(x, mean = 0., var = 1.):
    return st.norm.logpdf(x, mean, np.sqrt(var))
    
################################################################################
    
def dLogExponential(x, rate = 1.):
    return st.expon.logpdf(x, 0., 1. / rate)
    
################################################################################

def dLogGamma(x, shape = 2., scale = 1.):
    return st.gamma.logpdf(x, shape, 0., scale)

################################################################################

def dLogInvGamma(x, shape = 2., scale = 1.):
    return st.invgamma.logpdf(x, shape, 0., scale)

################################################################################

## other functions

################################################################################

def adjustPValues(p, method = 'Bonferonni'):
    padj = p * p.size
    padj[padj > 1.] = 1.
    
    return padj

################################################################################
    
def computePValues(x, y):
    ## lambda function for computing p(y|x)
    computeP = lambda x, y, r: np.exp( y * np.log(r) + sp.gammaln(x + y + 1.) - sp.gammaln(x + 1.) - sp.gammaln(y + 1.) - (x + y + 1.) * np.log(1. + r) )

    ## compute q values
    r  = y.sum() / x.sum()    
    yy = [ np.arange(int(yi) + 1)     for yi      in y          ]
    q  = [ computeP(xi, yyi, r).sum() for xi, yyi in zip(x, yy) ]
    q  = np.asarray(q)
    
    
    ## compute p values
    i    = q <= 0.5
    pval = np.zeros(q.size)
    
    pval[i]  = 2. * q[i]
    pval[~i] = 2. * ( 1. - q[~i] )    
    
    ## return
    return pval

################################################################################

def removeLowCounts(counts, prob = 0.1):
    rs = counts.sum(1)
    ii = rs > np.percentile(rs, prob * 100.)
    
    return counts[ii]
    

