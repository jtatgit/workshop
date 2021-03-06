#!/usr/bin/python3
###########################################################################################################################################################################
"""
Author:                   Felix Chan
Email:                    fmfchan@gmail.com
Created:                  2016.07.14
Description:              Source code 2 on a course of bootstrapping. It demonstrates how to estimate coefficients and their standard errors in a regression by bootstrapping. 

"""
###########################################################################################################################################################################
import numpy as np
import numpy.random as npr
import scipy.stats as sps
import scipy as sp
import matplotlib.pyplot as plt
import lm as lm 
import pandas as pd

N = 1000 #sample size
B = 500 #bootstrap sample size ie number of replication
a = 1  #true interpcept
b = 0.5 #true slope
s = 0.4 #true variance
e = sps.norm.rvs(size=N,loc=0, scale=s) #simulating residual vector
x = sps.norm.rvs(size=N,loc=2,scale=1) #simulating explanatory variable
y = a+b*x+e #constructing dependent variable
m = np.c_[y,x] #constructing dataset
ols_main = lm.lm('y~c+x', data=m, header=['y','x']) #estimating linear regression based on simulated dataset
ols_main.estimate()
coef = np.zeros((B,2)) #initiate vector to store bootstrapped coefficient estiamtes. 
for j in range(0,B):
    index = npr.choice(range(0,N), size=N, replace=True) #construct index set for bootstrap sample. 
    bootsample = m[list(index)] #extract bootstrap sample. 
    ols_temp = lm.lm('y~c+x', data=bootsample, header=['y','x']) #estimate regression based on bootstrap sample
    ols_temp.estimate()
    coef[j] = ols_temp.coef.reshape((1,2)) #store bootstrap estimate
####################################Calculate the true variance-covariance matrix of the OLS estimate###########################
tempx = np.c_[np.ones(N), x]
cov = np.power(s,2)*np.linalg.inv(np.dot(tempx.transpose(), tempx))
truecov = np.diag(cov)
###############################################################################################################################
summary = np.c_[truecov.reshape((2,1)), np.diag(ols_main.cov).reshape((2,1)), np.array([sps.tvar(coef[:,i]) for i in range(0,2)]).reshape((2,1))]
summary = np.r_[np.c_[np.r_[a,b], ols_main.coef.reshape((2,1)), np.array([sps.tmean(coef[:,i]) for i in range(0,2)]).reshape((2,1))], summary]
header = ['Theoretical', 'Sample Estimate', 'Bootstrap Estiamte']
labelx = ['a','b','var a', 'var b']
result = pd.DataFrame(summary, columns=header, index = labelx)
print(result)

