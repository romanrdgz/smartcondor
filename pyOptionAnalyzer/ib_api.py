'''
This script will access the IB API and download the option chain for given
securities
'''
from threading import Thread
from Queue import Queue
from ib.opt import ibConnection
from ib.ext.Contract import Contract
from time import sleep
import pandas as pd
import logging
import traceback  # TODO debugging purposes only


class IB_API(Thread):
    '''
    This class will establish a connection to IB and group the different
    operations
    '''

    def __init__(self, event, port=4001, client_id=0):
        '''
        Connection to the IB API
        '''
        super(IB_API, self).__init__()
        self.event = event
        # Create logger
        logging.basicConfig(
            level=logging.INFO, filename='ib_conn.log',
            format='%(asctime)s - %(levelname)s - %(message)s')

        # Create message queues
        self.input_queue = Queue()
        self.output_queue = Queue()

        # Connection variables
        self.connection = None
        self.port = port
        self.client_id = client_id
        self.reqId = 1
        self.status = 'DISCONNECTED'
        self.keep_alive = True

        # Dict which relates contract ids with the req id used for retrieval
        self.reqId_ticker = {}
        self.opt_chain = MultiDict()
        self.stk_data = MultiDict()
        self.contracts = []
        self.portfolio_positions = MultiDict()
        self.subscriptions = []

        self.thread_exception_msg = None

    def run(self):
        '''
        Thread runnable method
        '''
        try:
            # Creation of Connection class
            logging.info('Establishing connection with client id #' +
                         str(self.client_id))
            self.connection = ibConnection(
                host='localhost', port=self.port, clientId=self.client_id)
            # Register data handlers
            self.connection.registerAll(self._receive_message)
            # Create a thread for sending messages
            self.sender_thread = Thread(target=self._send_messages)
            self.sender_thread.start()
            # Connect
            self.connection.connect()
            self.status = 'CONNECTED'
            # Check input messages
            while(self.keep_alive):
                while not self.input_queue.empty():
                    # Extract message from queue and process it
                    self._process_message(self.input_queue.get())
                if self.thread_exception_msg:
                    logging.error(self.thread_exception_msg)
                    self.close()
        except Exception, e:
            traceback.print_exc()
            logging.error(str(e))
            self.stop()

    def stop(self):
        self.keep_alive = False
        self.disconnect()
        self.sender_thread.__stop = True
        self.__stop = True

    def disconnect(self):
        '''
        Disconnect from IB API
        '''
        if self.connection:
            self.connection.disconnect()
            self.status = 'DISCONNECTED'
            logging.info('Disconnected from IB server')

    def save_to_excel(self, opt_chains, output_file):
        '''
        This function stores an option chain in given output excel file
        opt_chains -> dictionary of {ticker: dataframe}
        output_file -> output file where the data will be exported
        '''
        writer = pd.ExcelWriter(output_file)
        for ticker in opt_chains.keys():
            opt_chains[ticker].to_excel(writer, sheet_name=ticker)
        writer.save()

    def _receive_message(self, msg):
        '''
        Callback method to receive messages from IB server
        '''
        self.input_queue.put(msg)

    def _process_message(self, msg):
        '''
        Callback method to process each different message
        '''
        msg_reqId = msg.values()[0]
        logging.info('Received msg of type ' + str(msg.typeName) +
                     ' (' + str(msg_reqId) + ')')
        if msg.typeName == 'managedAccounts':
            logging.info('Established connection with IB account ' +
                         str(msg.accountsList))
            # Ask for an account summary TODO under testing
            # self._get_account_summary(msg.accountsList, True)
        elif msg.typeName == 'nextValidId':
            logging.info('Next valid order id: ' + str(msg.orderId))
            self.reqId = msg.orderId
            if msg.orderId == 1:
                # Clear contract dicts
                self.reqId_ticker = {}
                self.opt_chain = MultiDict()
                self.stk_data = MultiDict()
                self.contracts = []
        elif msg.typeName == 'updateAccountTime':
            pass  # TODO UNIMPLEMENTED
        elif msg.typeName == 'updateAccountValue':
            pass  # TODO UNIMPLEMENTED
        elif msg.typeName == 'updatePortfolio':
            self._parsePortfolioData(msg)
        elif msg.typeName == 'contractDetails':
            contract = msg.contractDetails.m_summary
            self.contracts.append(contract)
            # Check security type at received contractDetails message
            if contract.m_secType == 'OPT':
                # Store list of available options into dict
                self._save_option_contracts_to_dict(contract)
            else:
                logging.info('WARNING: Received contractDetails for security '
                             'type ' + str(contract.m_secType) +
                             ': UNIMPLEMENTED')
        elif msg.typeName == 'contractDetailsEnd':
            logging.info('Received contractDetailsEnd for reqId ' +
                         str(msg_reqId))
            # Request market data snapshots to the server
            self._get_market_data(snapshot=True)
        elif msg.typeName == 'tickPrice':
            self._parse_tickPrice(msg)
        elif msg.typeName == 'tickOptionComputation':
            self._parse_tickOptionComputation(msg)
        elif msg.typeName == 'tickGeneric':
            self._parse_tickGeneric(msg)
        elif msg.typeName == 'tickSnapshotEnd':
            # Remove the req id from the list of requested ids, to be able to
            # determine when all the data has arrived
            if msg_reqId in self.reqId_ticker.keys():
                del self.reqId_ticker[msg_reqId]
            # Print info
            logging.info('Received tickSnapshotEnd for reqId ' +
                         str(msg_reqId) + '. Still pending ' +
                         str(len(self.reqId_ticker)))
            # Check if all the expected data has arrived
            self.check_if_all_data_arrived()
        elif msg.typeName == 'currentTime':
            logging.info('Current server time: ' + str(msg.time))
        elif msg.typeName == 'execDetails':
            logging.info('Received execDetails for reqId ' + str(msg_reqId))
        elif msg.typeName == 'error':
            logging.error(str(msg.errorCode) + ' - ' + str(msg.errorMsg))
            if msg.errorCode == 200:
                # Requested contract is ambiguous, remove from req_Id List
                if msg_reqId in self.reqId_ticker.keys():
                    del self.reqId_ticker[msg_reqId]
                # Check if all the expected data has arrived
                self.check_if_all_data_arrived()
            elif msg.errorCode == 326:
                # ClientId in use, raise exception and reconnect with different
                # id
                self.thread_exception_msg = msg.errorMsg
        elif msg.typeName == 'connectionClosed':
            logging.info('Connection has been closed')

    def check_if_all_data_arrived(self):
        '''
        This method checks if all the expected data has arrived
        '''
        if not self.reqId_ticker:
            logging.info('All requested market data has arrived')
            if not self.subscriptions:
                self.status = 'IDLE'
                logging.info('IB connection status set to IDLE')
                self.event.set()

    def _parse_tickPrice(self, msg):
        '''
        This method parses received message of type tickPrice
        msg -> received message
        '''
        if msg.tickerId not in self.reqId_ticker.keys():
            return

        price = msg.price
        contract = self.reqId_ticker[msg.tickerId]
        underlying = contract.m_symbol
        contract_id = contract.m_localSymbol

        # Parse message
        if msg.field == 1:
            if contract.m_secType == 'OPT':
                self.opt_chain[underlying][contract_id]['bid'] = str(price)
            elif contract.m_secType == 'STK':
                self.stk_data[underlying]['bid'] = str(price)
        elif msg.field == 2:
            if contract.m_secType == 'OPT':
                self.opt_chain[underlying][contract_id]['ask'] = str(price)
            elif contract.m_secType == 'STK':
                self.stk_data[underlying]['ask'] = str(price)
        elif msg.field == 9:
            if contract.m_secType == 'OPT':
                self.opt_chain[underlying][contract_id]['close'] = str(price)
            elif contract.m_secType == 'STK':
                self.stk_data[underlying]['close'] = str(price)
                if self._check_underlying_data(underlying):
                    self.cancel_subscription(msg.tickerId)

    def _parse_tickOptionComputation(self, msg):
        '''
        This method parses received message of type tickOptionComputation
        msg -> received message
        '''
        if msg.tickerId not in self.reqId_ticker.keys():
            return

        underlying = self.reqId_ticker[msg.tickerId].m_symbol
        contract_id = self.reqId_ticker[msg.tickerId].m_localSymbol
        field = msg.field
        price = msg.values()[2]
        delta = msg.delta
        impliedVolatility = msg.impliedVol
        optPrice = msg.optPrice
        pvDividend = msg.pvDividend
        gamma = msg.gamma
        vega = msg.vega
        theta = msg.theta
        undPrice = msg.undPrice
        # Parse message
        if field == 10:
            self.opt_chain[underlying][contract_id]['bid_delta'] = str(delta)
            self.opt_chain[underlying][contract_id][
                'bid_impliedVolatility'] = (str(impliedVolatility))
            self.opt_chain[underlying][contract_id]['bid_optPrice'] = (
                str(optPrice))
            self.opt_chain[underlying][contract_id]['bid_pvDividend'] = (
                str(pvDividend))
            self.opt_chain[underlying][contract_id]['bid_gamma'] = str(gamma)
            self.opt_chain[underlying][contract_id]['bid_vega'] = str(vega)
            self.opt_chain[underlying][contract_id]['bid_theta'] = str(theta)
            self.opt_chain[underlying][contract_id]['bid_undPrice'] = (
                str(undPrice))
        elif field == 11:
            self.opt_chain[underlying][contract_id]['ask_delta'] = str(delta)
            self.opt_chain[underlying][contract_id][
                'ask_impliedVolatility'] = (str(impliedVolatility))
            self.opt_chain[underlying][contract_id]['ask_optPrice'] = (
                str(optPrice))
            self.opt_chain[underlying][contract_id]['ask_pvDividend'] = (
                str(pvDividend))
            self.opt_chain[underlying][contract_id]['ask_gamma'] = str(gamma)
            self.opt_chain[underlying][contract_id]['ask_vega'] = str(vega)
            self.opt_chain[underlying][contract_id]['ask_theta'] = str(theta)
            self.opt_chain[underlying][contract_id]['ask_undPrice'] = (
                str(undPrice))
        elif field == 24:
            self.opt_chain[underlying][contract_id]['iv'] = str(price)

    def _parse_tickGeneric(self, msg):
        '''
        This method parses received message of type tickGenetic, which contains
        historical volatility (tick 23) or implied volatility (tick 24), among
        others
        msg -> received message
        '''
        if msg.tickerId not in self.reqId_ticker.keys():
            return

        underlying = self.reqId_ticker[msg.tickerId].m_symbol
        if msg.tickType == 23:
            self.stk_data[underlying]['hv'] = str(msg.value)
            logging.info('[HV] ' + underlying + ': ' + str(msg.value))
        elif msg.tickType == 24:
            self.stk_data[underlying]['iv'] = str(msg.value)
            logging.info('[IV] ' + underlying + ': ' + str(msg.value))
            if self._check_underlying_data(underlying):
                self.cancel_subscription(msg.tickerId)

    def get_option_contracts(self, tickers, expiry=None, strike=None):
        '''
        Call for all the options contract for the underlying
        tickers -> List of tickers whose options will be requested to IB server
        expiry -> [Optional] Expiry date of the options to be retrieved. Can be
            used as a results filter. If expiry is not provided, it will
            download all available expiries
        strike -> [Optional] Strike of the options to be retrieved. Can be
            used as a results filter. If strike is not provided, it will
            download all available strikes
        '''
        self.status = 'WORKING'
        for ticker in tickers:
            logging.info(
                'Getting ' + str(ticker) + ' option contracts' +
                (' expiring on ' + str(expiry)) if expiry else '' +
                (' with strike ' + str(strike)) if strike else '')
            # Contract creation
            contract = Contract()
            contract.m_symbol = ticker
            contract.m_exchange = 'SMART'
            contract.m_secType = 'OPT'
            if expiry:
                contract.m_expiry = expiry
            if strike:
                contract.m_strike = strike
            self.connection.reqContractDetails(self.reqId, contract)
            logging.info('Requested contract details for ' + ticker + ' (' +
                         str(self.reqId) + ')')
            self.reqId += 1

    def _get_market_data(self, snapshot):
        '''
        Requests all the options prices and greeks
        snapshot -> True if only a snapshot of market data is desired; False if
            a subscription is desired
        '''
        self.status = 'WORKING'
        # Loop through all options contracts
        for contract in self.contracts:
            # Store the relationship between reqId and contract object
            self.reqId_ticker[self.reqId] = contract
            self.output_queue.put(
                (self.reqId, 'reqMktData', contract, snapshot))
            # If it is a subscription, add reqId to the subscription list
            if not snapshot:
                self.subscriptions.append(self.reqId)
            self.reqId += 1

    def cancel_subscription(self, req_id):
        '''
        Cancels the data subscription associated to given req_id
        '''
        if req_id in self.reqId_ticker.keys():
            contract = self.reqId_ticker[req_id]
            self.output_queue.put((req_id, 'cancelMktData', contract, False))

    def get_stock_historical_volatility(self, ticker):
        '''
        Requests stock historical volatility
        '''
        self.status = 'WORKING'
        # Create stock's contract
        stock_contract = Contract()
        stock_contract.m_symbol = ticker
        stock_contract.m_secType = 'STK'
        stock_contract.m_exchange = 'SMART'
        stock_contract.m_currency = 'USD'

        # Insert request to output queue
        self.reqId_ticker[self.reqId] = stock_contract
        self.output_queue.put(
            (self.reqId, 'reqStkHistoricalVol', stock_contract, False))
        self.reqId += 1

    def get_stock_implied_volatility(self, ticker, snapshot):
        '''
        Requests stock implied volatility
        snapshot -> True if only a snapshot of market data is desired; False if
            a subscription is desired
        '''
        self.status = 'WORKING'
        # Create stock's contract
        stock_contract = Contract()
        stock_contract.m_symbol = ticker
        stock_contract.m_secType = 'STK'
        stock_contract.m_exchange = 'SMART'
        stock_contract.m_currency = 'USD'

        # Insert request to output queue
        self.reqId_ticker[self.reqId] = stock_contract
        self.output_queue.put(
            (self.reqId, 'reqStkImpliedVol', stock_contract, snapshot))
        # If it is a subscription, add reqId to the subscription list
        if not snapshot:
            self.subscriptions.append(self.reqId)
        self.reqId += 1

    def _send_messages(self):
        '''
        Method to send pending messages at output queue to the IB server
        '''
        while True:
            while not self.output_queue.empty():
                req_id, msgType, contract, snapshot = self.output_queue.get()
                if msgType == 'reqMktData':
                    self.connection.reqMktData(
                        req_id, contract, None, snapshot=snapshot)
                    logging.info('Requested market data snapshot for ' +
                                 str(contract.m_localSymbol) + ' (' +
                                 str(req_id) + ')')
                elif msgType == 'cancelMktData':
                    self.connection.cancelMktData(req_id)
                    logging.info('Cancelled market data subscription for ' +
                                 str(contract.m_localSymbol) + ' (' +
                                 str(req_id) + ')')
                    # Remove reqId from subscription list
                    if req_id in self.subscriptions:
                        self.subscriptions.remove(req_id)
                    # If it does not belong to a subscription, remove the reqId
                    # from the list of requested ids
                    if req_id in self.reqId_ticker.keys():
                        del self.reqId_ticker[req_id]
                    # Check if there is any pending job
                    if not self.subscriptions and not self.reqId_ticker:
                        self.status = 'IDLE'
                        logging.info('IB connection status set to IDLE')
                        self.event.set()
                elif msgType == 'reqStkHistoricalVol':  # TODO Under test
                    self.connection.reqMktData(
                        req_id, contract, '104', snapshot=False)
                    logging.info('Requested historical volatility for ' +
                                 str(contract.m_symbol) + ' (' +
                                 str(req_id) + ')')
                elif msgType == 'reqStkImpliedVol':
                    self.connection.reqMktData(
                        req_id, contract, '106', snapshot=False)
                    logging.info('Requested implied volatility for ' +
                                 str(contract.m_symbol) + ' (' +
                                 str(req_id) + ')')
                elif msgType == 'reqAccountUpdates':  # TODO Under test
                    # Contract variable here refers to the account number
                    self.connection.reqAccountUpdates(True, contract)

                # Sleep between messages to avoid collapsing IB server
                sleep(0.1)

    def _save_option_contracts_to_dict(self, opt_con):
        '''
        It saves the options market data into the both the contracts dictionary
        and the option chain dictionary
            opt_con -> Contract details on an option
        '''
        underlying = opt_con.m_symbol
        c_id = opt_con.m_localSymbol  # contract id

        # Store data in the option chain dictionary
        self.opt_chain[underlying][c_id]['m_conId'] = opt_con.m_conId
        self.opt_chain[underlying][c_id]['m_expiry'] = opt_con.m_expiry
        self.opt_chain[underlying][c_id]['m_strike'] = opt_con.m_strike
        self.opt_chain[underlying][c_id]['m_right'] = opt_con.m_right
        self.opt_chain[underlying][c_id]['m_multiplier'] = opt_con.m_multiplier
        self.opt_chain[underlying][c_id]['m_currency'] = opt_con.m_currency
        self.opt_chain[underlying][c_id]['m_localSymbol'] = c_id

    def _check_underlying_data(self, underlying):
        '''
        Checks if close price and IV of given underlying have been retrieved,
        and if so, cancels subscription. Returns true if all the data has
        been retrieved
        '''
        return ('close' in self.stk_data[underlying].keys() and
                'iv' in self.stk_data[underlying].keys())

    def get_as_dataframe(self):  # TODO Under test
        self.connection.reqCurrentTime()  # TODO WTF?

    def _get_account_summary(self, accounts_list, snapshot):  # TODO under test
        self.output_queue.put(
            (self.reqId, 'reqAccountUpdates', accounts_list, snapshot))
        self.reqId += 1

    def _parsePortfolioData(self, msg):  # TODO Under test
        '''
        Parses a updatePortfolio message to get data on every position we
        currently hold at our portfolio
        '''
        symbol = msg.contract.m_localSymbol

        self.portfolio_positions[symbol]['contract'] = msg.contract
        self.portfolio_positions[symbol]['position'] = msg.position
        self.portfolio_positions[symbol]['marketPrice'] = msg.marketPrice
        self.portfolio_positions[symbol]['averageCost'] = msg.averageCost
        self.portfolio_positions[symbol]['unrealizedPNL'] = msg.unrealizedPNL

        logging.info('[PORTFOLIO] ' + str(msg.position) + ' ' + str(symbol) +
                     ' bought @ ' + str(msg.averageCost) + ', now valued @ ' +
                     str(msg.marketPrice) + ' (PL: ' + str(msg.unrealizedPNL) +
                     ')')


class IBAPI_ClientIdInUse(Exception):
    pass


class MultiDict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
