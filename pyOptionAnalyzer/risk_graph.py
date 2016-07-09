import vollib.black_scholes as bs
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)


def plot_risk_graph(options_list, t_list, risk_free_rate, iv, show_plot=False,
                    save_png=False):
    '''
    Creates a risk graph for the combination of options provided
    in the input list of options for the different times to
    expiration provided

    inputs:
    options_list -> list of options composing the strategy. It is important
        to provide this list ordered by near-term expiries first
    t_list -> dates to be plotted (in datetime)
    risk_free_rate -> interest rate on a 3-month U.S. Treasury bill or similar
    iv -> implied volatility of underlying
    show_plot -> determines if the plot is shown in a window (default False)
    save_png -> determines if the plot is saved as a PNG file (default False)
    returns:
        list of tuples (x, (datetime, y))
    '''
    # First get the graph bounds, 10% apart from the min and max
    # strikes
    min_strike = None
    max_strike = None
    for opt in options_list:
        if (min_strike is None) or (opt.strike < min_strike):
            min_strike = opt.strike
        if (max_strike is None) or (opt.strike > max_strike):
            max_strike = opt.strike

    # Prices
    x_vector = np.linspace(min_strike * 0.7, max_strike * 1.3, 500)

    # Now plot the risk graph for the different time values provided
    return_values = []
    y = []
    for t in t_list:
        y.append(np.zeros(len(x_vector)))
        # Create the discrete values of P/L to plot against xrange
        for opt in options_list:
            t_exp = (opt.expiration - t).days / 365.
            y[-1] += np.array([opt.multiplier * opt.amount * (
                bs.black_scholes(opt.right, x, opt.strike, t_exp,
                                 risk_free_rate, iv / 100.) -
                opt.get_debit()) for x in x_vector])

        # Get the number of days to expiration from today for plot's legend
        days_to_expire = (options_list[0].expiration - t).days
        plt.plot(x_vector, y[-1], label='t: ' + str(days_to_expire))
        return_values.append((t, y[-1]))

    plt.legend()
    plt.xlabel('Price')
    plt.ylabel('P/L')
    # Save the plot as a PNG if required, or show plot in a window
    if save_png:
        plt.savefig(datetime.today().strftime('%d%b%y ') + '.png')
    else:
        # Show the plot
        plt.show()

    # Return the values calculated TODO for what? to calculate breakevens?
    return (x_vector, return_values)
