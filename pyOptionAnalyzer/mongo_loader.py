from pymongo import MongoClient, DESCENDING, ASCENDING
from datetime import datetime


if __name__ == '__main__':
    client = MongoClient('localhost:27017')
    db = client.smartcondor

    # Insert an user in users table
    db.users.insert(
        {'name': 'Roman', 'email': 'romanrdgz@gmail.com', 'country': 'Spain'})

    db.underlyings.create_index([
        ('timestamp', DESCENDING), ('ticker', ASCENDING)])

    db.options.create_index([
        ('timestamp', DESCENDING), ('ticker', ASCENDING),
        ('contract_id', ASCENDING)])

    # Insert strategies
    db.strategies.insert(
        {'type': 'Calendar', 'title': 'SPY Calendar test 1',
         'author': 'romanrdgz@gmail.com', 'ticker': 'SPY', 'debit': 2.28,
         'options': [158120313, 178959067], 'profit_loss': [0],
         'timestamp': [datetime.now()]})
    db.strategies.insert(
        {'type': 'Calendar', 'title': 'SPY Calendar test 2',
         'author': 'romanrdgz@gmail.com', 'ticker': 'SPY', 'debit': 2.28,
         'options': [221884168, 178764641], 'profit_loss': [0],
         'timestamp': [datetime.now()]})
    db.strategies.insert(
        {'type': 'Diagonal', 'title': 'SPY Diagonal test 1',
         'author': 'romanrdgz@gmail.com', 'ticker': 'SPY', 'debit': 2.28,
         'options': [221884168, 178959067], 'profit_loss': [0],
         'timestamp': [datetime.now()]})

    db.strategies.create_index([
        ('timestamp', DESCENDING), ('ticker', ASCENDING),
        ('title', ASCENDING)])
