# -*- coding: utf-8 -*-

from flask import Flask, jsonify
from flask_pymongo import PyMongo
from flask_restful import Api, Resource
from datetime import datetime

app = Flask(__name__)
app.config['MONGO_DBNAME'] = 'smartcondor'
mongo = PyMongo(app, config_prefix='MONGO')
APP_URL = 'http://127.0.0.1:5000'


class Underlying(Resource):
    def get(self, ticker=None, startdate=None, enddate=None):
        '''
        Gets a list of underlying close prices and IV for given ticker and
        dates between requested limits
        '''
        data = []
        error = None
        if ticker:
            # Check if date range is given
            if startdate and enddate:
                try:
                    # Check dates format
                    start_datetime = datetime.strptime(startdate, '%d%m%Y')
                    end_datetime = datetime.strptime(enddate, '%d%m%Y')
                    # Query the database
                    info = mongo.db.underlyings.find({
                        'ticker': ticker,
                        'timestamp': {
                            '$gte': start_datetime,
                            '$lte': end_datetime
                        }
                    })
                    if info:
                        data.append(info)
                except ValueError:
                    error = 'Wrong date format: use \'ddmmyyyy\''
            else:
                # No dates given, return latest day info
                info = mongo.db.underlyings.find({
                    'ticker': ticker}).limit(1).sort({'$natural': -1})
                if info:
                    data.append(info)

        return jsonify({'status': ('nok' if error else 'ok'),
                        'response': (error if error else data)})


class OptionData(Resource):
    def get(self, ticker=None, right=None, strike=None, expiry=None,
            samples=1):
        data = []
        error = None
        query = {}
        if ticker:
            query['ticker'] = ticker
            # Check if expiry date is given
            if expiry:
                try:
                    # Check date format
                    query['expiry'] = datetime.strptime(expiry, '%d%m%Y')
                except ValueError:
                    error = 'Wrong date format: use \'ddmmyyyy\''

            # Check if right is given
            if (right.upper() == 'P') or (right.upper() == 'C'):
                query['right'] = right.upper()
            else:
                error = ('Wrong right format: use \'C\' for calls '
                         'or \'P\' for puts')

            # Check if strike is given and it is a positive number
            if strike:
                try:
                    value = float(strike)
                    if value < 0:
                        error = 'Wrong strike format: must be positive'
                    else:
                        query['strike'] = strike
                except ValueError:
                    error = 'Wrong strike format: must be a number'

        # Query the database
        info = mongo.db.options.find(query).limit(samples).sort(
            {'$natural': -1})
        if info:
            data.append(info)

        return jsonify({'status': ('nok' if error else 'ok'),
                        'response': (error if error else data)})


api = Api(app)
api.add_resource(Underlying, '/underlying/<string:ticker>/')
api.add_resource(Underlying, '/underlying/<string:ticker>/'
                             '<string:startdate>/'
                             '<string:enddate>')
api.add_resource(OptionData, '/optiondata/<string:ticker>/'
                             '<string:right>/'
                             '<string:strike>/'
                             '<string:expiry>')
api.add_resource(OptionData, '/optiondata/<string:ticker>/'
                             '<string:right>/'
                             '<string:strike>/'
                             '<string:expiry>/'
                             '<int:samples>')

if __name__ == '__main__':
    app.run(debug=True)
