class Strategy(object):
    '''
    Strategy super class
    '''

    def __init__(self, options_list, underlying_amount=0, name='Unknown'):
        '''
        options_list -> list of Options composing the strategy. It is important
            to provide this list ordered by near-term expiries first
        underlying_amount -> [Optional] amount of stocks of the underlying
            (long or short). Will consider zero if not provided.
        name -> [Optional] strategy name. To be filled at each particular
            strategy derivated from this Strategy class
        '''
        if not isinstance(options_list, list):
            raise Exception('options_list parameter must be a list')
        elif not options_list:
            raise Exception('Cannot create an option strategy with an empty '
                            'list of options')

        self.options_list = options_list
        self.underlying_amount = underlying_amount
        self.strategy_name = name
        # Iterate the options to classify them and determine plot bounds and
        # front expiration (bounds must be 10% apart from the min and max
        # strikes)
        self.min_strike = None
        self.max_strike = None
        self.nearest_expiration = None

        for opt in self.options_list:
            if(self.min_strike is None) or (opt.strike < self.min_strike):
                self.min_strike = opt.strike
            if(self.max_strike is None) or (opt.strike > self.max_strike):
                self.max_strike = opt.strike
            if((self.nearest_expiration is None) or
               (opt.expiration < self.nearest_expiration)):
                self.nearest_expiration = opt.expiration

    def __str__(self):
        return(self.strategy_name)

    def __repr__(self):
        return(self.strategy_name)

    def __len__(self):
        raise NotImplementedError('Method has not been implemented')

    def __iter__(self):
        return iter(self.options_list)

    def get_ticker(self):
        '''
        Returns the ticker of the options composing the strategy
        '''
        return self.options_list[0].ticker

    def get_strike_bounds(self):
        '''
        Returns a tuple (min strike, max strike)
        '''
        return (self.min_strike, self.max_strike)

    def plot(self):
        raise NotImplementedError('Method has not been implemented')

    def get_profit_probability(self):
        raise NotImplementedError('Method has not been implemented')

    def get_nearest_expiration(self):
        '''
        Returns the nearest expiration date among those options composing the
        strategy
        '''
        return self.nearest_expiration
