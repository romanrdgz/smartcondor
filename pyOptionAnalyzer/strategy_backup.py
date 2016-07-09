    def _identify_strategy(self):
        self.strategy_name = 'Unknown strategy'

        # Identify the strategy implemented
        if len(self) is 4:
            if(self.long_calls and self.long_puts and self.short_calls and self.short_puts):
                # Same expiration
                if(self.long_calls[0][1].expiration == self.long_puts[0][1].expiration ==
                    self.short_calls[0][1].expiration == self.short_puts[0][1].expiration):
                    # Look for iron condor/butterfly
                    if((self.long_puts[0][1].strike < self.short_puts[0][1].strike) and
                       (self.short_calls[0][1].strike < self.long_calls[0][1].strike)):
                        if(self.short_puts[0][1].strike == self.short_calls[0][1].strike):
                            # It's an iron butterfly
                            self.strategy_name = 'Iron Butterfly'
                        elif(self.short_puts[0][1].strike < self.short_calls[0][1].strike):
                            # It's an iron condor
                            self.strategy_name = 'Iron Condor'

        elif len(self) is 2:
            # Look for calendar spreads and diagonal spreads
            if(self.long_calls and self.short_calls):
                if(self.long_calls[0][1].expiration == self.short_calls[0][1].expiration):
                    # Same expiration -> check for vertical spreads if strikes are different
                    if(self.long_calls[0][1].strike < self.short_calls[0][1].strike):
                        self.strategy_name = 'Bull Call Spread ' + str(self.long_calls[0][1].strike) + '-' + str(self.short_calls[0][1].strike)
                    elif(self.long_calls[0][1].strike < self.short_calls[0][1].strike):
                        self.strategy_name = 'Bear Call Spread ' + str(self.short_calls[0][1].strike) + '-' + str(self.long_calls[0][1].strike)
                else:
                    # Different expiration. Check strikes: equal or different?
                    if(self.long_calls[0][1].strike == self.short_calls[0][1].strike):
                        # Equal strikes -> it's a calendar spread
                        self.strategy_name = ('Long Call Calendar Spread ' + self.short_calls[0][1].expiration.strftime('%b-')
                            + self.long_calls[0][1].expiration.strftime('%b ') + str(self.long_calls[0][1].strike))
                    else:
                        # Different strikes -> it's a diagonal spread
                        self.strategy_name = ('Long Call Diagonal Spread ' + self.short_calls[0][1].expiration.strftime('%b-')
                            + self.long_calls[0][1].expiration.strftime('%b ') + str(self.short_calls[0][1].strike) + '-' + str(self.long_calls[0][1].strike))

            elif(self.long_puts and self.short_puts):
                if(self.long_puts[0][1].expiration == self.short_puts[0][1].expiration):
                    # Same expiration -> check for vertical spreads if strikes are different
                    if(self.long_puts[0][1].strike < self.short_puts[0][1].strike):
                        self.strategy_name = 'Bull Put Spread ' + str(self.long_puts[0][1].strike) + '-' + str(self.short_puts[0][1].strike)
                    elif(self.long_puts[0][1].strike < self.short_puts[0][1].strike):
                        self.strategy_name = 'Bear put Spread ' + str(self.short_puts[0][1].strike) + '-' + str(self.long_puts[0][1].strike)
                else:
                    # Different expiration. Check strikes: equal or different?
                    if(self.long_puts[0][1].strike == self.short_puts[0][1].strike): #TODO check front month!
                        # Equal strikes -> it's a calendar spread
                        self.strategy_name = ('Long Put Calendar Spread ' + self.short_puts[0][1].expiration.strftime('%b-')
                            + self.long_puts[0][1].expiration.strftime('%b ') + str(self.long_puts[0][1].strike))
                    else:
                        # Different strikes -> it's a diagonal spread #TODO The order of the strikes determines if short or long
                        self.strategy_name = ('Long Put Diagonal Spread ' + self.short_puts[0][1].expiration.strftime('%b-')
                            + self.long_puts[0][1].expiration.strftime('%b ') + str(self.short_puts[0][1].strike) + '-' + str(self.long_puts[0][1].strike))

            elif(self.long_calls and self.long_puts):
                # Same expiration
                if(self.long_calls[0][1].expiration == self.long_puts[0][1].expiration):
                    # Look for straddles/strangles:
                    if(self.long_calls[0][1].strike == self.long_puts[0][1].strike):
                        self.strategy_name = 'Long Straddle ' + str(self.long_calls[0][1].strike)
                    elif(long_calls[0][1].strike > long_puts[0][1].strike):
                        self.strategy_name = 'Long Strangle ' + str(self.long_puts[0][1].strike) + '/' + str(self.long_calls[0][1].strike)

            elif(self.short_calls and self.short_puts):
                # Same expiration
                if(self.short_calls[0][1].expiration == self.short_puts[0][1].expiration):
                    # Look for straddles/strangles:
                    if(self.short_calls[0][1].strike == self.short_puts[0][1].strike):
                        self.strategy_name = 'Short Straddle ' + str(self.short_calls[0][1].strike)
                    elif(short_calls[0][1].strike > short_puts[0][1].strike):
                        self.strategy_name = 'Short Strangle ' + str(self.short_puts[0][1].strike) + '/' + str(self.short_calls[0][1].strike)

        elif len(self) is 1:
            if self.short_calls:
                if self.short_calls[0][0] * 100 <= self.underlying_amount:
                    self.strategy_name = 'Covered call'
                elif self.underlying_amount == 0:
                    self.strategy_name = 'Naked call'
                else:
                    self.strategy_name = 'Partially covered call'
            elif self.short_puts:
                if self.short_puts[0][0] * 100 * (-1) <= self.underlying_amount:
                    self.strategy_name = 'Covered put'
                elif self.underlying_amount == 0:
                    self.strategy_name = 'Naked put'
                else:
                    self.strategy_name = 'Partially covered put'
            elif self.long_calls:
                self.strategy_name = 'Long call'
            else:
                if self.long_puts[0][0] * 100 >= self.underlying_amount:
                    self.strategy_name = 'Married put'
                elif self.underlying_amount == 0:
                    self.strategy_name = 'Long put'
                else:
                    self.strategy_name = 'Partially married put'
