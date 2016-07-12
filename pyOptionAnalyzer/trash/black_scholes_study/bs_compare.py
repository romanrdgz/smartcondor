'''
This script compares different implementations of the Black-Scholes option
pricing formula:
- MibianLib
- Vollib (based on Peter Jackel's LetsBeRational)
- DX Analytics
'''
import timeit
import mibian
import vollib.black_scholes as vol_bs
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)


def mibian_lib(x_vector, K, r, t, iv):
    return [mibian.BS([x, K, r, t], volatility=iv) for x in x_vector]


def vol_lib(x_vector, K, r, t, iv):
    return [vol_bs.black_scholes('c', x, K, t, r, iv) for x in x_vector]


if __name__ == '__main__':
    underlying_price = np.linspace(180, 205, num=200)
    strike_price = 195
    interest_rate = 0.01
    days_to_expire = 20
    t_years = days_to_expire / 365.
    iv = 20
    sigma = iv / 100.

    mibian_bs_result = mibian_lib(
        underlying_price, strike_price, interest_rate, days_to_expire, iv)
    t1 = timeit.Timer(lambda: mibian_lib(
        underlying_price, strike_price, interest_rate, days_to_expire, iv))
    print 'mibian: ' + str(t1.timeit(number=1000))
    y1 = [y.callPrice for y in mibian_bs_result]

    plt.xlabel('Underlying price')
    plt.ylabel('P/L')
    plt.plot(underlying_price, y1, 'r-', label='mibian')

    y2 = vol_lib(underlying_price, strike_price, interest_rate, t_years, sigma)
    t2 = timeit.Timer(lambda: vol_lib(
        underlying_price, strike_price, interest_rate, t_years, sigma))
    print 'vollib: ' + str(t2.timeit(number=1000))
    plt.plot(underlying_price, y2, 'b-', label='vollib')

    '''
    import dx
    #https://github.com/yhilpisch/dx/blob/master/03_dx_valuation_single_risk.ipynb
    call_eur = dx.valuation_mcs_european_single(
                    name='call_eur',
                    underlying=gbm,
                    mar_env=me,
                    payoff_func='np.maximum(maturity_value - strike, 0)')
    plt.plot(underlying_price, y3, 'b-', label='DX analytics')
    '''

    # Show the plot
    plt.legend()
    plt.show()
