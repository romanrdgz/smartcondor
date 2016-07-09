# from itertools import combinations
from argparse import ArgumentParser
import logging
import pandas as pd
import numpy as np
from scipy import interpolate
from scipy.stats import lognorm
import sys
from option import Option
from make_selection import SelectionList
from calendar_spread import CalendarSpread
import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style='darkgrid')
sns.set(color_codes=True)


# Create logger
logging.basicConfig(
    level=logging.INFO, filename='calendar_analyzer.log',
    format='%(asctime)s - %(levelname)s - %(message)s')


def plot_calendars(df, near_term_exp, next_term_exp, current_price):
    ticker = str(df['m_symbol'].head(1)).split()[0]
    # Filter to keep only the expirations under analysis
    df = df[(df['m_expiry'] == near_term_exp) |
            (df['m_expiry'] == next_term_exp)]
    # Replace -1.0 values in bid/ask for 0
    df.loc[df.bid < 0, 'bid'] = 0
    df.loc[df.ask < 0, 'ask'] = 0
    # Replace NaN values by 0
    df = df.fillna(0)
    # Calculate midprice and remove rows whose midprice is zero
    df['midprice'] = (df['bid'] + df['ask']) / 2
    df = df[df.midprice != 0]
    # Group by expiry & strike: each group will have 2 entries: diff their
    # midprice
    groups = df.groupby('m_expiry')
    near_term_group = groups.get_group(near_term_exp)
    next_term_group = groups.get_group(next_term_exp)
    # Drop strikes which are not available in both expiries
    strikes = pd.merge(near_term_group[['m_strike']],
                       next_term_group[['m_strike']],
                       how='inner', on=['m_strike'])
    # print len(near_term_group), len(next_term_group)
    prices = []
    for strike in strikes['m_strike']:
        a = near_term_group.loc[near_term_group['m_strike'] == strike,
                                'midprice'].values[0]
        b = next_term_group.loc[next_term_group['m_strike'] == strike,
                                'midprice'].values[0]
        price = b - a
        prices.append(price)

    # Create plot
    fig, ax1 = plt.subplots()
    ax1.set_title(ticker + ' analysis')
    ax1.plot(strikes['m_strike'], prices, 'bo')
    # Also plot an interpolation TODO cubic does not fit well...
    more_strikes = np.linspace(strikes['m_strike'].min(),
                               strikes['m_strike'].max(), 200)
    f = interpolate.interp1d(strikes['m_strike'], prices, kind='cubic')
    interpolation = f(more_strikes)
    ax1.plot(more_strikes, interpolation, 'b-')
    ax1.set_xlabel('Strike prices')
    # Make the y-axis label and tick labels match the line color.
    ax1.set_ylabel('Debit', color='b')
    ax2 = ax1.twinx()
    # Lognormal distribution
    stddev = 0.859455801705594  # volatility (of ATM?)
    mean = 8.4  # current_price
    dist = lognorm([stddev], loc=mean, scale=stddev)
    ax2.plot(more_strikes, dist.pdf(more_strikes), 'r-')
    ax2.set_ylabel('Profit probability', color='r')
    ax2.set_ylim([0, 1])
    plt.show()


if __name__ == "__main__":
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=str,
                        help='Uses an excel file as input')
    parser.add_argument('-x', '--expiry', type=str, help=('Determines option '
                        'expiry date. Use format YYYYMM'))
    parser.add_argument('-s', '--strike', type=float,
                        help='Determines option strike')
    parser.add_argument('-c', '--current_price', type=float,
                        help='Current underlying price')
    parser.add_argument('-v', '--iv', type=float, help='Current underlying IV')
    parser.add_argument('-r', '--right', type=str, required=True,
                        help='[Required] \'C\' for calls, \'P\' for puts')

    args = parser.parse_args()
    df_option_chain = None
    if not args.input:
        print('ERROR: requires an excel input')
    if not args.right:
        print('ERROR: must select call or put calendar spreads with -r')
    if args.right.upper() not in ['C', 'P']:
        print('ERROR: -r argument must be either \'C\' or \'P\'')
    else:
        # Load the option chain from excel
        logging.info('Loading option chain from Excel file ' + args.input)
        excel_file = pd.ExcelFile(args.input)
        # Get sheets names
        tickers = excel_file.sheet_names
        # Let the user decide which ticker to analyze
        selectionList = SelectionList(tickers)
        selectionList.mainloop()
        selected_ticker = None
        if selectionList.selection:
            selected_ticker = selectionList.selection
            logging.info('Selected ' + selected_ticker + ' options')
        else:
            logging.info('User quitted')
            sys.exit()
        df = excel_file.parse(selected_ticker)

        # Keep only calls or puts depending on the selection made
        df = df[df.m_right == args.right.upper()]
        # Remove NaN values
        df = df.dropna()
        # Keep only options where ask/bid > 0
        df = df[((df['bid'] > 0) & (df['ask'] > 0))]

        # Get a list of expiries
        expiries = df['m_expiry'].unique()
        logging.info('Available expiries: ' + str(expiries))

        selectionList = SelectionList(expiries)
        selectionList.mainloop()
        near_term = None
        if selectionList.selection:
            near_term = int(selectionList.selection)
            logging.info('Selected ' + str(near_term) + ' as near-term expiry')
        else:
            logging.info('User quitted')
            sys.exit()

        selectionList = SelectionList(
            df[df['m_expiry'] > near_term]['m_expiry'].unique())
        selectionList.mainloop()
        next_term = None
        if selectionList.selection:
            next_term = int(selectionList.selection)
            logging.info('Selected ' + str(next_term) + ' as next-term expiry')
        else:
            logging.info('User quitted')
            sys.exit()

        # Get a list with strikes available in both selected expirations
        near_term_k = df[df['m_expiry'] == near_term]['m_strike'].unique()
        next_term_k = df[df['m_expiry'] == next_term]['m_strike'].unique()
        strikes = list(set(near_term_k).intersection(next_term_k))
        strikes = [int(k) for k in strikes]
        strikes.sort()
        logging.info('Available strikes: ' + str(strikes))
        # TODO Show the user which is current underlying price or at least
        # where ATM is at the selection dialog
        selectionList = SelectionList(strikes)
        selectionList.mainloop()
        if selectionList.selection:
            strike = int(selectionList.selection)
            logging.info('Selected ' + str(strike) + ' as calendar strike')
        else:
            logging.info('User quitted')
            sys.exit()

        near_term_opt = Option.from_pandas(
            df[(df['m_expiry'] == near_term) &
               (df['m_strike'] == strike)], amount=-1)
        next_term_opt = Option.from_pandas(
            df[(df['m_expiry'] == next_term) &
               (df['m_strike'] == strike)], amount=1)

        calendar = CalendarSpread(near_term_opt, next_term_opt)
        logging.info('Plotting ' + str(near_term) + '/' + str(next_term) +
                     ' risk graph')
        print near_term_opt
        print next_term_opt

        r = 0.01
        t = 0  # TODO set t
        breakevens, max_profit, max_loss = calendar.plot(  # TODO Remove IV
            risk_free_rate=r, iv=args.iv, show_plot=True, iv_change=1.00)
        # TODO Printing stats from plot (debug purposes)
        print 'Near-term opt. IV: ' + str(near_term_opt.get_iv())
        print 'B/E: ' + str(breakevens)
        print 'Max profit: ' + str(max_profit)
        print 'Max loss: ' + str(max_loss)

        # Set current underlying price so we can plot the probability
        # distribution
        current_price = None
        if not args.current_price:
            # TODO Get current underlying price from Yahoo or similar
            pass
        else:
            current_price = args.current_price
            current_iv = args.iv
            if len(breakevens) > 2:
                print 'ERROR: more than 2 zeroes detected'
            else:
                # Get probability of underlying being below first zero
                # REVIEW CDF can't return zero!
                scale = current_price * np.exp(r * t)
                p_below = lognorm.cdf(breakevens[0], current_iv, scale=scale)
                # Get probability of underlying being above second zero
                p_above = lognorm.sf(breakevens[1], current_iv, scale=scale)
                # Get the probability of profit for the calendar
                p_profit = 1 - p_above - p_below
                print('Probabilities (below, above, profit): ' + str(p_below) +
                      ' - ' + str(p_above) + ' - ' + str(p_profit))

        calls = df[df['m_right'] == 'C']
        plot_calendars(calls, near_term, next_term, current_price)
        sys.exit()  # TODO remove to go on

        '''
        # Do all the possible combinations of expiries for calendar spreads
        expiry_combinations = list(combinations(expiries, r=2))

        # Iterate calls
        for (near_term, next_term) in expiry_combinations:
            if near_term > next_term:
                continue
            today = datetime.today()  # TODO Avoid past options for now
            if today > datetime.strptime(str(near_term), '%Y%m%d'):
                continue
        '''
