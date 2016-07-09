from argparse import ArgumentParser
from option import Option
from calendar_spread import CalendarSpread
from make_selection import SelectionList
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
import sys
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)


class RiskGraph(object):
    '''
    Creates a risk graph for the combination of options provided
    in the input list of options for the different times to
    expiration provided

    inputs:
    strategy -> Option strategy to be analyzed
    t_list -> dates to be plotted (in datetime)
    risk_free_rate -> interest rate on a 3-month U.S. Treasury bill or similar
    iv -> current underlying IV (as sigma)
    '''

    def __init__(self, strategy, risk_free_rate, iv):
        self.r = risk_free_rate
        self.strategy = strategy
        self.ticker = self.strategy.get_ticker()

        min_strike, max_strike = self.strategy.get_strike_bounds()
        self.x_vector = np.linspace(min_strike * 0.7, max_strike * 1.3, 500)
        self.t = datetime.today()
        self.expiry_t = self.strategy.get_nearest_expiration()
        self.iv = iv
        self.current_iv = iv
        self.s = min_strike  # TODO s must be current underlying value

        # Figure
        self.fig, self.ax = plt.subplots()
        self.fig.canvas.set_window_title('Calendar Spread Analyzer')
        plt.subplots_adjust(bottom=0.2)

        # First column: Connect button and list of options
        ax1 = plt.subplot2grid((12, 8), (0, 0), colspan=2)
        conn_button = Button(ax1, 'Connect')
        # TODO add connection callback
        ax2 = plt.subplot2grid((12, 8), (1, 0), colspan=2, rowspan=11)
        # TODO add list and its callback

        # Second column: skip the plot area to be the last one and set the
        # parameters widgets
        ax3 = plt.subplot2grid((12, 8), (9, 3), colspan=4)
        days_to_expiration = (self.expiry_t - self.t).days
        self.date_slider = Slider(ax3, 'Days to expire', 0, days_to_expiration,
                                  valinit=days_to_expiration, valfmt='%0.0f')
        self.date_slider.on_changed(self._update_time)
        ax4 = plt.subplot2grid((12, 8), (10, 3), colspan=4)
        self.iv_slider = Slider(ax4, 'IV', 0.01, 1.0, valinit=self.iv)
        self.iv_slider.on_changed(self._update_iv)
        ax5a = plt.subplot2grid((12, 8), (11, 3), colspan=2)
        self.max_gain_label = Button(ax5a, 'Max gain: ')
        ax5b = plt.subplot2grid((12, 8), (11, 3), colspan=2)
        self.profit_prob_label = Button(ax5b, 'Profit %: ')
        # TODO labels with prob of profit, max gain...

        # And finally, the plot
        plt.subplot2grid((12, 8), (0, 2), colspan=6, rowspan=9)

        self.expiry_y = self._update_plot(self.expiry_t)
        self.variable_y = self._update_plot(self.t)
        self.var_line, = plt.plot(
            self.x_vector, self.variable_y, '-b', label='t')
        self.exp_line, = plt.plot(
            self.x_vector, self.expiry_y, '-r', label='On expiry')
        self._update_results()

        plt.legend()
        plt.xlabel('Price')
        plt.ylabel('P/L')

        # Show the plot dialog
        plt.tight_layout()
        plt.show()

    def _update_plot(self, plot_date):
        '''
        Updates the plot with current scenario parameters
        '''
        y = self.strategy.plot(self.x_vector, plot_date, self.r, self.iv)
        return y

    def _update_time(self, val):
        '''
        TODO
        '''
        self.t = self.expiry_t - timedelta(days=self.date_slider.val)
        self.variable_y = self._update_plot(self.t)
        self.var_line.set_ydata(self.variable_y)
        self._update_results()
        plt.draw()

    def _update_iv(self, val):
        '''
        TODO
        '''
        self.iv = self.iv_slider.val
        self.expiry_y = self._update_plot(self.expiry_t)
        self.variable_y = self._update_plot(self.t)
        self.exp_line.set_ydata(self.expiry_y)
        self.var_line.set_ydata(self.variable_y)
        self._update_results()
        plt.draw()

    def _update_results(self):
        '''
        TODO
        '''
        # Update results
        self.max_gain_label.label.set_text(
            'Max gain: ' + str(max(self.expiry_y)))
        profit_prob = self.strategy.get_profit_probability(
            self.x_vector, self.expiry_y, self.iv, self.s)
        self.profit_prob_label.label.set_text(
            'Prob. of profit: ' + '{0:.2f}'.format(100 * profit_prob) + '%')


if __name__ == "__main__":
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True,
                        help='Uses an excel file as input')
    args = parser.parse_args()

    # Load option chains from excel input file
    excel_file = pd.ExcelFile(args.input)
    # Get sheets names (tickers)
    tickers = excel_file.sheet_names
    # Let the user decide which ticker to analyze
    selectionList = SelectionList(tickers)
    selectionList.mainloop()
    selected_ticker = None
    if selectionList.selection:
        selected_ticker = selectionList.selection
    else:
        sys.exit()
    df = excel_file.parse(selected_ticker)

    # Keep only calls or puts depending on the selection made
    df = df[df.m_right == 'C']  # TODO make this selectable
    # Remove NaN values
    df = df.dropna()
    # Keep only options where ask/bid > 0
    df = df[((df['bid'] > 0) & (df['ask'] > 0))]

    # Get a list of expiries
    expiries = df['m_expiry'].unique()
    selectionList = SelectionList(expiries)
    selectionList.mainloop()
    near_term = None
    if selectionList.selection:
        near_term = int(selectionList.selection)
    else:
        sys.exit()

    selectionList = SelectionList(
        df[df['m_expiry'] > near_term]['m_expiry'].unique())
    selectionList.mainloop()
    next_term = None
    if selectionList.selection:
        next_term = int(selectionList.selection)
    else:
        sys.exit()

    # Get a list with strikes available in both selected expirations
    near_term_k = df[df['m_expiry'] == near_term]['m_strike'].unique()
    next_term_k = df[df['m_expiry'] == next_term]['m_strike'].unique()
    strikes = list(set(near_term_k).intersection(next_term_k))
    strikes = [int(k) for k in strikes]
    strikes.sort()
    selectionList = SelectionList(strikes)
    selectionList.mainloop()
    if selectionList.selection:
        strike = int(selectionList.selection)
    else:
        sys.exit()

    # Create options from selected data
    near_term_opt = Option.from_pandas(
        df[(df['m_expiry'] == near_term) &
           (df['m_strike'] == strike)], amount=-1)
    next_term_opt = Option.from_pandas(
        df[(df['m_expiry'] == next_term) &
           (df['m_strike'] == strike)], amount=1)

    calendar = CalendarSpread(near_term_opt, next_term_opt)
    risk_graph = RiskGraph(calendar, 0.01, 0.149)
