import pandas as pd
from datetime import datetime
from math import copysign
import copy


class Option(object):
    '''
    This class implements an option object
    '''

    def __init__(self, ticker, strike, expiration, implied_volatility, bid_ask,
                 delta, gamma, theta, vega, multiplier, right, amount=1):
        self.ticker = ticker
        self.strike = strike
        self.expiration = expiration
        self.implied_volatility = implied_volatility
        self.bid_ask = bid_ask
        self.delta = delta
        self.gamma = gamma
        self.theta = theta
        self.vega = vega
        self.multiplier = multiplier
        self.right = right.lower()  # Vollib BS implementation uses lowercase
        self.amount = amount
        self.debit = None

    @classmethod
    def from_pandas(cls, df, amount=1):
        '''
        Constructor from Pandas dataframe
        '''
        if not isinstance(df, pd.DataFrame):
            raise ValueError('Given argument is not a Pandas DataFrame')
        if len(df) != 1:
            raise ValueError('Input DataFrame must contain a single option, '
                             'given DataFrame contains ' + str(len(df)))

        bid_ask = (df.bid.iloc[0], df.ask.iloc[0])
        delta = (df.bid_delta.iloc[0], df.ask_delta.iloc[0])
        gamma = (df.bid_gamma.iloc[0], df.ask_gamma.iloc[0])
        theta = (df.bid_theta.iloc[0], df.ask_theta.iloc[0])
        vega = (df.bid_vega.iloc[0], df.ask_vega.iloc[0])
        implied_volatility = (
            df.bid_impliedVolatility.iloc[0], df.ask_impliedVolatility.iloc[0])

        return cls(df.m_symbol.iloc[0], df.m_strike.iloc[0],
                   datetime.strptime(str(df.m_expiry.iloc[0]), '%Y%m%d'),
                   implied_volatility, bid_ask, delta, gamma, theta, vega,
                   multiplier=df.m_multiplier.iloc[0],
                   right=df.m_right.iloc[0], amount=amount)

    def __str__(self):
        return(str(self.amount) + ' ' + str(self.ticker) +
               (' call ' if (self.right.upper() == 'C') else ' put ') +
               str(self.strike) + ' (' +
               self.expiration.strftime('%d %b\'%y') + ')')

    def get_price(self, midprice=False):
        '''
        Gets option price; will return ask price if going long, or bid price
        if going short. If midprice argument is True, will return the midpoint
        between bid and ask
        '''
        price = None
        if midprice:
            price = (self.bid_ask[0] + self.bid_ask[1]) / 2
        else:
            price = (self.bid_ask[1] if (copysign(1, self.amount) > 0)
                     else self.bid_ask[0])
        return price

    def get_debit(self):
        '''
        Gets the debit (if going long, if going short is credit) paid when the
        possition was established. If no real possition has been established,
        bid-ask midpoint will be returned instead.
        The value returned is always positive, even if it is a credit. Use
        the amount value to determine if it is debit or credit.
        '''
        return(self.debit if self.debit else
               ((self.bid_ask[0] + self.bid_ask[1]) / 2))

    def get_delta(self):
        '''
        Gets option delta
        '''
        return(self.delta[1] if (copysign(1, self.amount) > 0)
               else self.delta[0])

    def get_gamma(self):
        '''
        Gets option gamma
        '''
        return(self.gamma[1] if (copysign(1, self.amount) > 0)
               else self.gamma[0])

    def get_theta(self):
        '''
        Gets option theta
        '''
        return(self.theta[1] if (copysign(1, self.amount) > 0)
               else self.theta[0])

    def get_vega(self):
        '''
        Gets option vega
        '''
        return(self.vega[1] if (copysign(1, self.amount) > 0)
               else self.vega[0])

    def get_iv(self):
        '''
        Gets option implied volatility (IV)
        '''
        return(self.implied_volatility[1] if (copysign(1, self.amount) > 0)
               else self.implied_volatility[0])

    def get_copy(self, iv_change):
        '''
        Returns a copy of this option object, but with an increment/decrement
        in IV
        inputs:
            iv_change: percentaje to increment/decrement the IV of the option.
                E.g.: 1.03 for a 3% increment, 0.97 for a 3% decrement.
        '''
        option_copy = copy.deepcopy(self)
        option_copy.implied_volatility = (
            self.implied_volatility[0] * iv_change,
            self.implied_volatility[1] * iv_change)
        return option_copy
