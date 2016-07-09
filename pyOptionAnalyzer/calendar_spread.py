import vollib.black_scholes as bs
from strategy import Strategy
import numpy as np
from scipy.stats import lognorm


class CalendarSpread(Strategy):
    '''
    This class implements a calendar spread strategy
    '''

    def __init__(self, near_term_option, next_term_option):
        Strategy.__init__(
            self, [near_term_option, next_term_option], name='Calendar Spread')
        # Check both options have the same underlying
        if near_term_option.ticker != next_term_option.ticker:
            raise ValueError(
                'Calendar options must refer to the same underlying')
        else:
            self.ticker = near_term_option.ticker
        # Check both options have the same strike
        if near_term_option.strike != next_term_option.strike:
            raise ValueError('Calendar options must refer to the same strike. '
                             'Try a diagonal spread instead')
        else:
            self.strike = near_term_option.strike
        # Check the options have different expiry dates
        if near_term_option.expiration == next_term_option.expiration:
            raise ValueError('Calendar options must have different expiry '
                             'dates')
        else:
            # Consider to swap input options if given near_term > next_term
            if near_term_option.expiration > next_term_option.expiration:
                self.near_term_opt = next_term_option
                self.next_term_opt = near_term_option
            else:
                self.near_term_opt = near_term_option
                self.next_term_opt = next_term_option
        # Check that one option is short and the other is long
        if((abs(near_term_option.amount) != abs(next_term_option.amount)) or
           (near_term_option.amount + next_term_option.amount != 0)):
            raise ValueError('Near term and next term option number must be '
                             'the same, but with different sign')
        else:
            # Next term option gives the sign of the calendar
            self.amount = next_term_option.amount
        # Check that both options are call or put
        if near_term_option.right != next_term_option.right:
            raise ValueError('Calendar options must be of the same kind')
        else:
            self.right = near_term_option.right
        # Get calendar debit value per each (near_term, next term) pair
        self.debit = (
            near_term_option.get_price() + next_term_option.get_price())
        # Get calendar greeks
        # TODO review if they can be summed in Passarelli's book (deltas can)
        self.delta = (
            near_term_option.get_delta() + next_term_option.get_delta())
        self.gamma = (
            near_term_option.get_gamma() + next_term_option.get_gamma())
        self.theta = (
            near_term_option.get_theta() + next_term_option.get_theta())
        self.vega = near_term_option.get_vega() + next_term_option.get_vega()

    def __str__(self):
        return(self.near_term_opt.expiration.strftime('%d %b\'%y') + '-' +
               self.next_term_opt.expiration.strftime('%d %b\'%y') +
               (' call' if self.call else ' put') +
               ' calendar spread, strike ' + str(self.strike))

    def __len__(self):
        return self.amount

    def get_profit_probability(self, x_vector, y_vector, iv, s, r, t):
        '''
        Returns the probability of obtaining a profit with the strategy with
        in current scenario under study
        inputs:
            x_vector -> vector of underlying prices
            y_vector -> vector with Black-Scholes results
            iv -> underlying implied volatility
            s -> current underlying price
        '''
        p_profit = 0
        # Calculate break-even points
        zero_crossings = np.where(np.diff(np.sign(y_vector)))[0]
        breakevens = [x_vector[i] for i in zero_crossings]
        if len(breakevens) > 2:
            print 'ERROR: more than 2 zeroes detected'
        elif len(breakevens) == 0:
            p_profit = (0.9999 if y_vector[(len(y_vector)/2)] > 0 else 0.0001)
        else:
            # Get probability of being below the min breakeven at expiration
            # REVIEW CDF can't return zero!
            scale = s * np.exp(r * t)
            p_below = lognorm.cdf(breakevens[0], iv, scale=scale)
            # Get probability of being above the max breakeven at expiration
            p_above = lognorm.sf(breakevens[1], iv, scale=scale)
            # Get the probability of profit for the calendar
            p_profit = 1 - p_above - p_below
            print('Profit prob. with s=' + str(s) + ', iv=' + str(iv) +
                  ', b/e=' + str(breakevens))
            print('1 - ' + str(p_below) + ' - ' + str(p_above) + ' = ' +
                  str(p_profit))  # TODO debugging purposes

        return p_profit

    def plot(self, x_vector, date, r, iv):
        '''
        Creates a risk graph for the calendar spread
        inputs:
            x_vector -> vector of underlying prices where Black-Scholes must
                be calculated
            date -> date to be plotted
            r -> interest rate on a 3-month U.S. Treasury bill or similar
            iv -> implied volatility of the underlying
        returns:
            y -> Black-Scholes solution to given x_vector and parameters
        '''
        y = np.zeros(len(x_vector))
        # Create the discrete values of P/L to plot against xrange
        for opt in self.options_list:
            t = (opt.expiration - date).days / 365.
            y += np.array([opt.multiplier * opt.amount * (bs.black_scholes(
                opt.right, x, opt.strike, t, r, iv) -
                opt.get_debit()) for x in x_vector])
        return y
