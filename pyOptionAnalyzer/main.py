import pandas as pd
import pymongo
from datetime import datetime
from argparse import ArgumentParser
import smtplib
import threading
import traceback


def load_from_excel(input_file, tickers):
    '''
    This function reads option chain from given input excel file
    input_file -> input file where the data will be imported from
    tickers -> list of tickers to be loaded from the excel file
    '''
    opt_chains = {}
    for tick in tickers:
        opt_chains[tick] = pd.ExcelFile(input_file).parse(tick)
    return opt_chains


def save_to_excel(opt_chains, output_file):
    '''
    This function stores an option chain in given output excel file
    opt_chains -> dictionary of {ticker: dataframe}
    output_file -> output file where the data will be exported
    '''
    writer = pd.ExcelWriter(output_file)
    for ticker in opt_chains.keys():
        opt_chains[ticker].to_excel(writer, sheet_name=ticker)
    writer.save()


def check_mongo_server_is_on():
    mongo_server_status = True
    try:
        con = pymongo.MongoClient('localhost:27017',
                                  serverSelectionTimeoutMS=2000)
        con.server_info()
    except pymongo.errors.ServerSelectionTimeoutError as err:
        print('ERROR: No MongoDB server was found: ' + str(err))
        mongo_server_status = False

    return mongo_server_status


def send_email_alert(from_addr, to_addr, email_pass, msg):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_addr, email_pass)
    server.sendmail(from_addr, to_addr, msg)
    server.quit()


if __name__ == "__main__":
    # Configure the command line options
    parser = ArgumentParser()
    parser.add_argument('-t', '--tickers', nargs='+', required=True,
                        help='[Required] Determines a list of option tickers')
    parser.add_argument('-x', '--expiry', type=str, help=('Determines option '
                        'expiry date. Use format YYYYMM'))
    parser.add_argument('-s', '--strike', help='Determines option strike')
    parser.add_argument('-i', '--input', type=str,
                        help='Uses an excel file as input')
    parser.add_argument('-o', '--output', type=str,
                        help='Uses an excel file as output')
    parser.add_argument('-m', '--mongo', type=str,
                        help='Stores output data in given MongoDB database')
    parser.add_argument('-e', '--toaddr', type=str,
                        help='E-mail where error alarms are sent to')
    parser.add_argument('-p', '--emailpass', type=str,
                        help='E-mail account password for error alarms')

    args = parser.parse_args()
    df_option_chains = None

    # If input excel file was given, load data
    if args.input:
        df_option_chains = load_from_excel(args.input, args.tickers)
    else:
        # Check if MongoDB server is accessible if mongo flag is on before
        # asking the IB server for any data
        if args.mongo and not check_mongo_server_is_on():
            # Send e-mail alert
            if args.toaddr and args.emailpass:
                from_addr = 'smartcondor@gmail.com'
                msg = 'MongoDB server offline'
                send_email_alert(from_addr, args.toaddr, args.emailpass, msg)
                quit()

        # Data will be loaded from Interactive Brokers server
        from ib_api import IB_API
        from time import sleep

        # Connection thread
        try:
            client_id = 0
            ib = None
            event = threading.Event()
            # Try connecting with secuential client_id values until using
            # one free id
            while True:
                try:
                    ib = IB_API(client_id=client_id, event=event)
                    ib.start()
                    sleep(1)
                    if ib.thread_exception_msg:
                        client_id += 1
                        continue
                    break
                except Exception, e:
                    print e
                    break

            ib.get_option_contracts(args.tickers)
            event.wait()  # Wait for the IB thread to finish
            event.clear()
            for ticker in args.tickers:
                ib.get_stock_implied_volatility(ticker, True)
                event.wait()
                event.clear()

            if(len(ib.opt_chain) == 0):
                print('Error, zero contracts retrieved')
            else:
                # Store option chain in excel file
                if args.output:
                    # Get option chains from the IB connection class
                    df_option_chains = {t: pd.DataFrame(ib.opt_chain[t]).T
                                        for t in args.tickers}

                    # Get columns to be exported to excel file
                    for key in ib.opt_chain[args.tickers[0]]:
                        cols = ib.opt_chain[args.tickers[0]][key].keys()
                        break
                    for t in args.tickers:
                        # Set column names
                        df_option_chains[t] = df_option_chains[t][cols]
                        # Remove those option contracts without price
                        df_option_chains[t].dropna(subset=['close'])

                    # Save dataframe to Excel file
                    save_to_excel(df_option_chains, args.output)
                    print 'Successfully exported to ' + str(args.output)
                elif args.mongo:
                    # Store option chains in MongoDB database
                    con = pymongo.MongoClient('localhost:27017')
                    db = args.mongo
                    today = datetime.now().replace(
                        hour=0, minute=0, second=0, microsecond=0)

                    for t in args.tickers:
                        # Store underlyings close price and IV
                        con[db]['underlyings'].insert(
                            {'ticker': t,
                             'last': ib.stk_data[t]['close'],
                             'iv': ib.stk_data[t]['iv'],
                             'timestamp': today})

                        # Store option contracts
                        print(str(t) + ' optchain size: ' +
                              str(len(ib.opt_chain[t].keys())))
                        if(len(ib.opt_chain[t].keys()) > 0):
                            con[db]['options'].insert([
                                {'ticker': t,
                                 'contract_id': c['m_conId'],
                                 'right': c['m_right'],
                                 'strike': c['m_strike'],
                                 'close': c['close'],
                                 'expiry':
                                 datetime.strptime(c['m_expiry'], '%Y%m%d'),
                                 'multiplier': c['m_multiplier'],
                                 'timestamp': today}
                                for c in ib.opt_chain[t].values() if c['close']
                            ])

                    print 'Successfully exported to Mongo database'

        except Exception, e:
            traceback.print_exc()
            print 'ERROR in IB_API: ' + str(e)
            if args.emailpass and args.toaddr:
                # Send e-mail report
                from_addr = 'smartcondor@gmail.com'
                msg = 'Smartcondor auto data downloader error'
                send_email_alert(from_addr, args.toaddr, args.emailpass, msg)
        finally:
            ib.stop()
            quit()
