import pandas as pd
import numpy as np
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.mlab as mlab
from matplotlib import cm
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)


def plot_iv_surface(dataframe):
    '''
    This function plots the implied volatility surface and returns it as PNG
    '''
    dataframe = dataframe[dataframe['m_expiry'] < 20170000]
    dataframe['iv'] = dataframe['bid_impliedVolatility'] + dataframe['ask_impliedVolatility']
    dataframe = dataframe.dropna()
    dataframe = dataframe[dataframe['iv'] < 1]

    t = dataframe['m_expiry']
    #t = pd.to_datetime(dataframe['m_expiry'], format='%Y%m%d')
    strike = dataframe['m_strike']
    iv = dataframe['iv']

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    triang = mtri.Triangulation(t, strike)
    ax.plot_trisurf(triang, iv, linewidth=0, cmap=cm.winter, shade=True)

    ax.set_zlim([0,1])
    ax.set_xlabel('Expiration date')
    ax.set_ylabel('Strike price')
    ax.set_zlabel('IV')

    # Get ticker
    ticker = dataframe['m_symbol'].head(1)
    plt.title(ticker + ' IV surface')
    # Also save the plot as a PNG
    png_file = ticker + '_ivsurf.png'
    #plt.savefig(png_file, dpi=1200)
    plt.show()
    return png_file
    
    
def plot_iv_surface2(dataframe):
    '''
    This function plots the implied volatility surface and returns it as PNG. 
    Least squares fit of Chebyshev will be applied.
    '''
    dataframe = dataframe[dataframe['m_expiry'] < 20170000]
    dataframe['iv'] = dataframe['bid_impliedVolatility'] + dataframe['ask_impliedVolatility']
    dataframe = dataframe.dropna()
    dataframe = dataframe[dataframe['iv'] < 1]
    #TODO Filter by open interest. How to get that data?

    t = dataframe['m_expiry']
    #t = pd.to_datetime(dataframe['m_expiry'], format='%Y%m%d')
    strike = dataframe['m_strike']
    iv = dataframe['iv']
    
    X,Y = np.meshgrid(t, strike)
    XX = X.flatten()
    YY = Y.flatten()
    
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    
    
def iv_contour(dataframe):
    # Filtering
    dataframe = dataframe.dropna()
    dataframe = dataframe[dataframe['m_expiry'] < 20170000]
    dataframe['iv'] = dataframe['bid_impliedVolatility'] + dataframe['ask_impliedVolatility']
    dataframe = dataframe[dataframe['iv'] < 200]
    #TODO Need to filter out those with no open interest
    
    # Getting data
    dataframe['days_to_exp'] = dataframe.apply(lambda row: (datetime.strptime(str(row['m_expiry']), '%Y%m%d') -
        datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        ).days, axis=1)
    x = dataframe['days_to_exp']
    y = dataframe['m_strike']
    z = dataframe['iv']
    
    plt.tricontourf(x, y, z, 50, cmap=plt.get_cmap('OrRd'))
    plt.colorbar()
    #plt.plot(x,y, 'bo')
    plt.xlim(min(x), max(x))
    plt.ylim(min(y), max(y))
    plt.xlabel('Days to expiration')
    plt.ylabel('Strike price')
    ticker = str(dataframe['m_symbol'].head(1)).split()[0]
    plt.title(ticker + ' IV surface')
    #plt.show()
    png_file = ticker + '_ivsurf.png'
    plt.savefig(png_file, dpi=1200)
    

def plot_iv_vs_strikes(t, dataframe):
    plt.plot(dataframe['m_strike'], dataframe['iv'])
    plt.xlabel('Strike prices')
    plt.ylabel('IV')

    # Show the plot
    plt.show()


def plot_iv_vs_time(strike, dataframe):
    plt.plot(dataframe['days_to_expiration'], dataframe['iv'])
    plt.xlabel('Days to expiration')
    plt.ylabel('IV')

    # Show the plot
    plt.show()
