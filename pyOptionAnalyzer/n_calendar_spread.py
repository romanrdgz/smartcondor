from strategy import Strategy


class NCalendarSpread(Strategy):
    '''
    This class groups N calendars to allow double, triple, ... calendar spreads
    '''

    def __init__(self, calendar_list):
        Strategy.__init__(self, calendar_list, name='N Calendar Spread')

        # Check that calendar list is not empty
        if not calendar_list:
            raise ValueError(
                'No calendars given to NCalendarSpread constructor')
        else:
            self.calendar_list = calendar_list
        # Check all given calendars have the same underlying
        fist_ticker = calendar_list[0].get_ticker()
        if not all(cal.get_ticker() == fist_ticker for cal in calendar_list):
            raise ValueError(
                'All given calendars must refer to the same underlying')
        else:
            self.ticker = fist_ticker
        # Check all calendars have the same near-term and next-term expiries
        if not all(c.near_term_opt.expiration == self.get_nearest_expiration()
                   for c in calendar_list):
            raise ValueError('All given calendars must refer to the same '
                             'near-term expiration date')
        else:
            self.near_term_exp = self.get_nearest_expiration()
        self.next_term_exp = calendar_list[0].next_term_opt.expiration
        if not all(c.next_term_opt.expiration == self.next_term_exp
                   for c in calendar_list):
            raise ValueError('All given calendars must refer to the same '
                             'next-term expiration date')

    def __len__(self):
        return len(self.calendar_list)

    def plot(self):
        pass

    def get_profit_probability(self):
        pass
