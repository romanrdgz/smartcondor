# SmartCondor

SmartCondor is a web application for traders with the following features:

  - Option strategies analysis
  - Implied volatility study
  - Alerts based on options value and their underlying price action

### What are option strategies?
Any option is defined by an **strike price** and its **expiration date**, and its price is derived from certain parameters (**greeks**) related to the time until expiration, implied volatility and underlying price. Moreover, there are two esential types of options an investor can buy or sell: **CALLs** and **PUTs**

  - **Buying a CALL option gives you the right of buying** the referred underlying at the strike price after expiration, no matter how much the underlying costs then. Obviously, if the underlying price is then lower than the strike, it has no sense to execute the option rights, and therefore it is said that the option expires worthless.
  - **Selling a CALL option assigns you the obligation of selling** the referred underlying to the investor who has bought the CALL option (this is a zero sum game), in case he decides to execute his rights.
  - **Buying a PUT option gives you the right of selling** the referred underlying.
  - **Selling a PUT option assigns you the obligation of buying** the referred underlying to the investor who has bought the PUT option.

Each of these four possibilities can be represented in a risk graph which determines how much the option is valued at any time, and how much will it be valued at expiration. The following figure represents a **long** (bought) **CALL**:

![Long CALL risk graph](http://www.theoptionsguide.com/images/long-call.gif)

These four possibilities can be combined (even with a long/short stock position) to generate different strategies, such as calendar spreads (e.g. see figure below), diagonal spreads, iron condors, strangles, butterfly spreads...

![Long calendar spread](http://www.theoptionsguide.com/images/neutral-calendar-spread.gif)

The risk graph of these option strategies can be obtained as the sum of each component risk graph. Altougth there are different software platforms for creating and analysing this plots, they are either too expensive for a casual trader or too poor quality. Therefore, **the scope of this project is to provide casual investors an easy and modern tool for analysing option strategies**.

### Requirements
 - Req #1: Users shall be able to create an account and identify themselves
 - Req #2: Users shall be able to select an underlying (among those available) and explore the option chain
 - Req #3: Users shall be able to select options (and their amounts) from the option chain in order to build and strategy while watching the result risk graph
 - Req #4: The strategy type shall be automatically detected (or be set as 'unknown')
 - Req #5: Users shall be able to select how many plots are to be represented in the risk graph (one per date to be shown). Initially, current date and expiration date shall be shown.
 - Req #6: Users shall be able to select a plot and modify the date baing represented
 - Req #7: Users shall be able to modify the implied volatility which affects all plots (but the one from expiration date)
 - Req #8: Users shall be able to modify the underlying value which affects all plots
 - Req #9: Users shall be able to modify the price of the options composing the strategy (in case he has already opened the operation before at different prices)
 - Req #10: The expected profit/loss of the strategy shall be shown next to the risk graph
 - Req #11: Risk/reward value shall be shown next to the risk graph
 - Req #12: Advice shall be shown in order to improve the strategy
 - Req #13: Users shall be able to save the strategy
 - Req #14: Users shall view a dashboard where they can choose between creating a new strategy, exploring saved strategies, or other posible services to be determined (alerts, implied volatility studies, algorithmic trading...)
 - Req #15: Users shall be able to share any strategy risk graph in social networks
- Req #16: Risk graph shall be calculated using Black-Scholes method
- Req #17: Heavy calculations shall be performed at client's browser
- Req #18: Users shall be able to publish their strategies at SmartCondor public strategies, or to keep them private
- Req #19: Registered users shall be able to comment on public strategies
- Req #20: Users shall get a notification when somebody comments on their own strategies or answers to their own comments
- Req #21: Users shall be able to explore the evolution of implied volatility for any available underlying
- Req #22: Users shall be able to explore 3D volatility surfaces for any available underlying
- Req #23: Users shall be able to create alarms for option strategies and receive a notification when the alarm is triggered
- Req #24: Market data shall be automatically updated from a data source to be determined

### Interfaces and tech

SmartCondor is composed by different modules:
 - Webapp server [Meteor - Angular/Blaze?]
 - Market data connector [Python - Interactive Brokers (temporary solution)]
 - Database [MongoDB]

Both the webapp and the market data connector share the database. Currently, new market data is downloaded only at the end of the trading day.

### Installation

Section to be edited once the code is reorganized in the Github repository.

### Development

Want to contribute? Great! We are looking for programmers and designers willing to contribute to this project. Please let us know.

### License
MIT