import warnings
import dx
import datetime as dt
import pandas as pd
import seaborn as sns
sns.set()
warnings.simplefilter('ignore')



r = dx.constant_short_rate('r', 0.01)

me_1 = dx.market_environment('me', dt.datetime(2015, 1, 1))
# starting value of simulated processes
me_1.add_constant('initial_value', 100.)
# volatiltiy factor
me_1.add_constant('volatility', 0.2)
# horizon for simulation
me_1.add_constant('final_date', dt.datetime(2016, 6, 30))
# currency of instrument
me_1.add_constant('currency', 'EUR')
# frequency for discretization
me_1.add_constant('frequency', 'W')
# number of paths
me_1.add_constant('paths', 10000)
# discount curve
me_1.add_curve('discount_curve', r)

gbm_1 = dx.geometric_brownian_motion('gbm_1', me_1)
