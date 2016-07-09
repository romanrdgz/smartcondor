import numpy as np
from datetime import datetime
# from bokeh.plotting import Figure
# from bokeh.models import ColumnDataSource, HBox, VBoxForm
from bokeh.models.widgets import Button, Slider, RadioButtonGroup
# from bokeh.io import curdoc


class RiskGraph(object):
    '''
    Creates a risk graph for the combination of options provided
    in the input list of options for the different times to
    expiration provided

    inputs:
    options_list -> list of options composing the strategy. It is important
        to provide this list ordered by near-term expiries first
        TODO change for Strategy object
    t_list -> dates to be plotted (in datetime)
    risk_free_rate -> interest rate on a 3-month U.S. Treasury bill or similar
    iv -> current underlying IV (as sigma)
    '''

    def __init__(self, options_list, risk_free_rate, iv):
        self.options = options_list
        self.r = risk_free_rate
        self.iv = iv
        self.curr_iv = iv
        self.t = datetime.today()
        self.expiry_t = self.options[0].expiration

        self.x_vector = None
        self.min_strike = None
        self.max_strike = None

        # Widgets
        self.right_radio = RadioButtonGroup(labels=["Calls", "Puts"], active=0)
        self.expiry_slider = Slider(
            title="Days to exp.", value=0.0, start=-5.0, end=5.0, step=1)
        self.iv_slider = Slider(
            title="IV", value=self.curr_iv, start=0.0, end=1.0, step=0.01)
        self.restore_iv_button = Button(label="Restore IV")

    def _define_graph_bounds(self):
        '''
        Get the graph bounds, 10% apart from the min and max strikes
        '''
        for opt in self.options:
            if(self.min_strike is None) or (opt.strike < self.min_strike):
                self.min_strike = opt.strike
            if(self.max_strike is None) or (opt.strike > self.max_strike):
                self.max_strike = opt.strike

        # Prices vector
        self.x_vector = np.linspace(
            self.min_strike * 0.7, self.max_strike * 1.3, 500)


if __name__ == "__main__":
    pass
