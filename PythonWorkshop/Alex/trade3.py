import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import sys
sys.path.insert(0,"/Users/229922I/research/python/econometrics")
import dataobj as dob

from scipy.stats import uniform
import copy 

def accumulation(x):
    """
    Give x, calcualte the accumulated sum
    """
    T = len(x)
    return [sum(x[0:i]) for i in range(1,T)]

def moving_average(m, N=20): 
	"""
	Calculate N days moving average for stock, stock. 
	Input: 
		m: a KXT numpy array containing T time series observations for K stocks. 
		N: an integer. The windows of moving average
	Output:
		mv: a KX(T-N) numpy array containing the N moving averages for stock. 
	"""
	K,T = m.shape # The method shape returns the number of rows (K) and the number of columns (T)
	mv = np.zeros((K,T-N+1)) #initiate the output variables with size K X (T-N)
	for i,s in enumerate(m): 
		temp = [sp.stats.tmean(s[t-N:t-1]) for t in range(N,T+1)]	
		mv[i] = temp
	return mv

def entry_buy(cp, mv): 
	"""
	Determine the entry for buying 
	Input:
		cp: a 2 X 1 array containing closing prices for two consecutive days 
		mv: a 2 X 1 array containing moving averages for two consecutive days
	Ouput:
		Boolean: True if entry happens otherwise False
	"""
	if cp[1] > mv[1] and cp[0] <= mv[0]: 
		return True 
	else: 
		return False

def entry_sell(cp, mv):
	"""
	Determine the entry for selling 
	Input:
		cp: a 2 X 1 array containing closing prices for two consecutive days 
		mv: a 2 X 1 array containing moving averages for two consecutive days
	Ouput:
		Boolean: True if entry happens otherwise False
	"""
	if cp[1] < mv [1] and cp[0] >= mv[0]:
		return True 
	else: 
		return False

def exit_trendreverse_buy(mv, cp):
	"""
	Determine exit status due to trend reversal. 
	Input:
		mv: a scalar denoting the moving average of the last N days
		cp: a scalar denoting the closing price of the same day. 
	Output:
		Boolean: True if exit happens and False otherwise.
	"""
	if cp < mv:
		return True
	else:
		return False

def exit_trendreverse_sell(mv, cp):
	"""
	Determine exit status due to trend reversal. 
	Input:
		mv: a scalar denoting the moving average of the last N days
		cp: a scalar denoting the closing price of the same day. 
	Output:
		Boolean: True if exit happens and False otherwise.
	"""
	if cp > mv:
		return True
	else:
		return False

def exit_varloss(entryprice, cp, varloss, status):
	"""
	Determine exit status due to accumulative returns less than worse case VaR
	Input: 
		entryprice: a scailar indicating the price at the time of entry. 
		cp: a scalar denoting the closing price of the current day. 
	Output:
		Boolean: True if exit happens and False otherwise.
	"""
	ar =np.log(cp/entryprice)
        if status is "short":
            ar = -ar
	if ar <= varloss: 
		return True
	else: 
		return False

def exit_vargain(entryprice, cp, vargain, status): 
	"""
	Determine exit status due to accumulative returns greater than best case VaR
	Input:
		entryproce: a scalar indicating the price at the time of entry
		cp: a scalar denoting the closing price of the current day
	Output:
		Boolean: True if exit happens and False otherwise.
	"""
	ar = np.log(cp/entryprice)
        if status is "short":
            ar = -ar
	if ar > vargain:
		return True
	else:
		return False
def bootstrap_extreme(rm, alpha=0.05, replication=1000):
	"""
	Bootstrap the Vargain and Varloss based on the return data. 
	Input:
		rm: a T numpy.array containing return data. 
		alpha: a scalar representing the significant level
		replication: a scailar representing the number of replicaiton in the bootstrap
	"""
	T = len(rm)
	vargain_m = np.zeros(replication)
        varloss_m = np.zeros(replication)
	for i in range(0,replication):
	    boots_index = [int(np.floor(j)) for j in uniform.rvs(size=T, loc=0, scale=T-1)]
            tempboots = rm[boots_index]
            tempboots.sort()
	    vargain_m[i] = tempboots[int(np.floor((1-alpha)*T))]
            varloss_m[i] = tempboots[int(np.floor((alpha)*T))] 
	varloss,vargain = sp.stats.tmean(varloss_m), sp.stats.tmean(vargain_m) 
	return varloss,vargain

def bootstrap(rm, alpha=0.05, replication=1000):
	"""
	Bootstrap the Vargain and Varloss based on the return data. 
	Input:
		rm: a T numpy.array containing return data. 
		alpha: a scalar representing the significant level
		replication: a scailar representing the number of replicaiton in the bootstrap
	"""
	T = len(rm)
	ThreeMmeans = np.zeros(replication)
	for i in range(0,replication):
	    boots_index = [int(np.floor(j)) for j in uniform.rvs(size=T, loc=0, scale=T-1)]
	    ThreeMmeans[i] = sp.stats.tmean(rm[boots_index])
	sThreeMeans = copy.copy(ThreeMmeans)
	sThreeMeans.sort()
	varloss,vargain = sThreeMeans[int(np.floor(len(sThreeMeans)*alpha))], sThreeMeans[int(len(sThreeMeans)-np.floor(len(sThreeMeans)*alpha))]
	return varloss,vargain 

def trade_stock(mv, op, cp, varloss, vargain, N=20, alpha=0.05, replication=1000):
	"""
	Trade stock based on opening, closing and moving average price by executing various entry and exit rules. 
	Input:
		mv: a T-N numpy array of moving average. 
		op: a T numpy array of openning prices. 
		cp: a T numpy array of closing prices. 
		N: a scalar representing the windows of moving averages. 
		alpha: a scalar denoting the significant level for the calculation of VaR. 
		replication: a scalar indicating the number of replication in bootstrapping. 
		varloss: var for worse case
		vargain: var for best case
	Output:
		profit: total gain/loss of trade. 
		no_entry_sell: total number of sell entries. 
		no_entry_buy: total number of buy entries. 
		no_profit_entry: total number of profit entry.
		ptofit_pertrade = profit/(no_entry_sell+no_entry_buy) 
	"""
	T = len(op)
	no_entry_buy = 0
	no_entry_sell = 0
        status = "none"
	no_profit_entry = 0
	profit_list = []
        profit = 0
        loss_list = []
	for t in range(N+1,T):
            temp_mv = np.array([mv[t-N-1], mv[t-N]])
            temp_cp = np.array([cp[t-2], cp[t-1]])
            if (status is "none"): 
                if entry_buy(temp_cp, temp_mv) and op[t] >= temp_mv[1]: 
                    status = "long"
                    entryprice = op[t]
                    entrytime = t
                elif entry_sell(temp_cp, temp_mv) and op[t] <= temp_mv[1]: 
                    status = "short"
                    entryprice = op[t]
                    entrytime = t
            else:
                if status is "long" and (exit_trendreverse_buy(mv[t-N+1],cp[t]) or exit_varloss(op[entrytime],cp[t],varloss, status) or exit_vargain(op[entrytime], cp[t], vargain, status)):  
                    profit_list.append(np.log(cp[t]/op[entrytime]))
                    status = "none"
                elif status is "short" and (exit_trendreverse_sell(mv[t-N+1],cp[t]) or exit_varloss(op[entrytime],cp[t],varloss, status) or exit_vargain(op[entrytime], cp[t], vargain, status)):   
                    profit_list.append(-np.log(cp[t]/op[entrytime]))
                    status = "none"
        profit = sum(profit_list)
        return profit_list,profit


######################################################################################################################
#A block time wasting code to convince Alex
choice = 0
N=20
alpha=0.05
m_cp = dob.dataobj("ClosePrice.csv")
m_op = dob.dataobj("OpenPrice.csv") 
mv_cp = moving_average(m_cp.data, N=N)
r_cp = np.log(m_cp.data.transpose()[1:m_cp.T]/m_cp.data.transpose()[0:m_cp.T-1])
r_cp = r_cp.transpose()
#varloss,vargain = bootstrap(r_cp[choice])
varloss,vargain = bootstrap_extreme(r_cp[0], alpha=alpha)
profit_list,profit= trade_stock(mv_cp[choice], m_op.data[choice], m_cp.data[choice], varloss, vargain, N=N, alpha=alpha)
"""
accum_profit = accumulation(profit_list)
print("The profit is {0}".format(profit))
print("The Number of Entry Sell is {0}".format(no_entry_sell))
print("The Number of Entry Buy is {0}".format(no_entry_buy))
print("The Number of No Profit Entry is {0}".format(no_profit_entry))
print("The Average Profit is {0}".format(aprofit))

K,T = mv.shape
T = 500
for i,s in enumerate(mv):
	plt.subplot(K,1,i+1)
	plt.plot(range(0,T+N), m.data[i][0:T+N], "r", range(N,T+N), mv[i][0:T], "b")
plt.show()

######################################################################################################################
	
m = dob.dataobj("ClosePrice.csv")
N=20
testmv = moving_average(m.data[0:4], N=N)

"""
