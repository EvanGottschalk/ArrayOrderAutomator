# This program is for connecting to and retrieving information from cryptocurrency exchanges using the CCXT library

import os
import sys
import traceback

import pickle
import math
import pathlib
import pandas as pd
from datetime import datetime

# AudioPlayer.py uses the playsound library to create audio alerts for errors or other significant events
from AudioPlayer import AudioPlayer

# GetCurrentTime.py has functions for easily acquiring the current date or time separately or together, and other time functions
from GetCurrentTime import GetCurrentTime

# CustomEncryptor.py is used to access encrypted API keys
from CustomEncryptor import CustomEncryptor

# CCXT is the fantastic library that makes the interaction with cryptocurrency exchanges possible
import ccxt

# This function will create the ConnectToExchange class in a non-local scope, making it more secure
def main():
    CTE = ConnectToExchange()
    CTE.main_loop()
    del CTE

class ConnectToExchange:
    def __init__(self):
        # Toggle silent_mode to True to prevent all print statements that aren't error messages
        self.silent_mode = False
        self.GCT = GetCurrentTime()
        self.AP = AudioPlayer()
        self.CE = CustomEncryptor.CustomEncryptor()
        # The improved_columns are simply the normal columns of an OHLCV, but with capitalization and a 'Time' column added. This variable helps with CSV exports
        self.improved_columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'Time']
        # The timeframes_All dict contains the most common time durations that cryptocurrency exchanges use in graphs of price over time
        self.timeframes_All = {'1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h', '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'}
        # The activity logs are a history of every connection or other exchange-related action that has been made
        # The Master Activity Log has every action from all time
        # The Daily Activity Logs are broken up into individual days
        self.activityLog_Current = {}
        self.activity_log_location = 'Activity Logs/'
        if not(os.path.isdir('ConnectToExchange/Activity Logs')):
            os.makedirs('ConnectToExchange/Activity Logs')
        # Information about any errors that occur are stored in error_log and exported to CSV
        self.error_log = []
        # This dict stores the API information for each account & exchange
        # Fill this in with the exchanges & account names you use
        # Enter your favorite exchange + account pair as 'Default' if you want the connect() function to connect with no inputs
        self.exchangeAccounts = {'Coinbase': {'apiKey Length': 32, \
                                              'secret Length': 88, \
                                              'Main': {'apiKey': '', 'secret': ''}, \
                                              'Long': {'apiKey': '', 'secret': ''}, \
                                              'Short': {'apiKey': '', 'secret': ''}}, \
                                 'Binance': {'apiKey Length': 64, \
                                             'secret Length': 64, \
                                             'Main': {'apiKey': '', 'secret': ''}}, \
                                 'Kraken': {'apiKey Length': 36, \
                                            'secret Length': 91, \
                                            'Main': {'apiKey': '', 'secret': ''}, \
                                            'Long 50x': {'apiKey': '', 'secret': ''}, \
                                            'Short 50x': {'apiKey': '', 'secret': ''}, \
                                            'Long 50x Quick': {'apiKey': '', 'secret': ''}, \
                                            'Short 50x Quick': {'apiKey': '', 'secret': ''}, \
                                            'Monty': {'apiKey': '', 'secret': ''}}, \
                                 'Default': 'Kraken Main', \
                                 'Default Exchange': 'Kraken', \
                                 'Default Account': 'Main', \
                                 'Default Type': 'spot'}
        self.currentConnectionDetails = {'Exchange Name': '',
                                         'Account Name': '', \
                                         'Time of Acccess': str(datetime.now())}
        # availableSymbols contains lists of the cryptocurrencies tradeable on a given exchange
        # Whenever connect() is used, availableSymbols will be updated to have the exchange name as a new key and a list of the available symbols as the value
        self.availableSymbols = {}
        # EMA_smoother is an int that is used in calculating exponential moving averages. The most common value to use is 2. Feel free to change it
        self.EMA_smoother = 2
        self.balances = None
        self.exchange = None

    def main_loop(self):
        print('CTE : main_loop initiated')
        exchange = self.connect()
        # I run getOHLCVs() on the 1 minute timeframe in the main loop to build up OHLCV data on my own machine via updateMasterOHLCVs()
        # This is optional, but useful because it is usually difficult to get minute-to-minute data through APIs unless the data is very recent
        self.getOHLCVs('default', 'BTC', '1m', 1999, {}, 'no')

    # This is the primary function of the class. It creates the connections to cryptocurrency exchanges using API keys
    def connect(self, *args):
        connected = False
        while not(connected):
        # This is for the case where the user calls connect() with no inputs
            if len(args) == 0:
                try:
                    exchange_name = self.exchangeAccounts['Default Exchange']
                    account_name = self.exchangeAccounts['Default Account']
                except:
                    exchange_name = input('To which exchange would you like to connect?\n    Exchange Name: ')
                    account_name = input('Which account on that exchange would you like to use?\n    Account Name: ')
            elif len(args) == 1:
            # This is for the case where the user inputs a dictionary containing the exchange & account names
                if type(args[0]) == dict:
                    exchange_name = args[0]['Exchange Name']
                    account_name = args[0]['Account Name']
            # This else is for the case where the user enters just one string
                else:
                    if args[0].lower() == 'default':
                        args = [self.exchangeAccounts['Default']]
                # This if is for the case where the string is both the exchange name and account name separated by a space
                    if ' ' in args[0]:
                        split_name = args[0].split(' ')
                        exchange_name = split_name[0]
                        split_account_name = split_name[1:len(split_name)]
                        account_name = ''
                        for word in split_account_name:
                            account_name += word
                            if not(word == split_account_name[len(split_account_name) - 1]):
                                account_name += ' '
                # This else assumes the 1 string entered is the exchange name, and assigns the account_name to be the default account
                    else:
                        exchange_name = args[0]
                        account_name = self.exchangeAccounts['Default Account']
        # This is for the case where the user calls connect() with 2 inputs - the exchange name followed by the account name
            elif len(args) == 2:
                exchange_name = args[0]
                account_name = args[1]
        # This swaps in the default exchange or account if 'default' was used as an input
            if exchange_name.lower() == 'default':
                exchange_name = self.exchangeAccounts['Default Exchange']
            if account_name.lower() == 'default':
                account_name = self.exchangeAccounts['Default Account']                
        # The exchange name & account have been chosen. Now the appropriate API information is retrieved
            if self.exchangeAccounts[exchange_name][account_name]['apiKey'] == '':
                self.fetch_API_key(exchange_name, account_name)
            if len(self.exchangeAccounts[exchange_name][account_name]['apiKey']) > 100:
                if self.CE:
                    try:
                        key = self.CE.decrypt(self.exchangeAccounts[exchange_name][account_name]['apiKey'])[0:36]
                        secret = self.CE.decrypt(self.exchangeAccounts[exchange_name][account_name]['secret'])[0:91]
                    except:
                        print('CTE : ERROR! Failed to decrypt API key file.')
                        connected = False
                        continue
                else:
                    key = self.exchangeAccounts[exchange_name][account_name]['apiKey']
                    secret = self.exchangeAccounts[exchange_name][account_name]['secret']
            else:
                key = self.exchangeAccounts[exchange_name][account_name]['apiKey']
                secret = self.exchangeAccounts[exchange_name][account_name]['secret']
            try:
        # The API key has been retrieved. Now the connection to the exchange will be made
            # Connects to Binance
                if exchange_name == 'Binance':
                    self.exchange = ccxt.binance({'apiKey': key, \
                                                  'secret': secret, \
                                                  'timeout': 30000, \
                                                  'enableRateLimit': True, \
                                                  'options': {'adjustForTimeDifference': True}})           
            # Connects to Kraken
                elif exchange_name == 'Kraken':
                    self.exchange = ccxt.kraken({'apiKey': key, \
                                                 'secret': secret, \
                                                 'timeout': 30000, \
                                                 'enableRateLimit': True, \
                                                 'options': {'adjustForTimeDifference': True, \
                                                             'defaultType': 'spot', \
                                                             'postOnly': True}})
            except:
                print('CTE : ERROR! Failed to connect to ' + exchange_name)
                connected = False
            connected = True
            del key, secret
    # Now that the exchange has been connected to, variables are assigned and the ActivityLog is updated
        self.currentConnectionDetails['Exchange Name'] = exchange_name
        self.currentConnectionDetails['Account Name'] = account_name
        self.exchange_name = exchange_name
        self.account_name = account_name
        date = self.GCT.getDateString()
        timestamp = self.GCT.getTimeStamp()
        time = self.GCT.getTimeString()
        self.availableSymbols[exchange_name] = list(self.exchange.loadMarkets())
    # If balances have already been fetched, they may refer to a different exchange or account. This updates self.balances to prevent confusion
        if self.balances:
            self.balances = self.getBalances()
      # This section creates new entries in the Master Activity Log and Daily Activity Logs if they have not been used yet
        try:
            self.activityLog_Master = pickle.load(open(self.activity_log_location + exchange_name + '_ActivityLog_Master.pickle', 'rb'))
            if not(self.silent_mode):
                print('\nCTE : ' + exchange_name + ' ' + account_name + ' Master Activity Log loaded!')
            largestTimestamp = max(self.activityLog_Master)
            if not(self.silent_mode):
                print('CTE : The most recent activity was on ' + self.activityLog_Master[largestTimestamp]['Date'] + '!')
        except:
            self.activityLog_Master = {}
            if not(self.silent_mode):
                print('CTE : No past Activity Log found!')
        try:
            self.activityLog_Daily = pickle.load(open(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.pickle', 'rb'))
            if not(self.silent_mode):
                print('CTE : Daily Activity Log loaded!')
        except:
            self.activityLog_Daily = {'Date': date, \
                                      'Activity Log': {}}
            if not(self.silent_mode):
                print('CTE : No Daily Activity Log found for today!')
      # This section creates new activity log entries and saves them
        self.currentConnectionDetails['Time of Access'] = str(datetime.now())
        self.activityLog_Current[timestamp] = {'Activity': 'Connected', \
                                               'Date': date, \
                                               'Time': time}
        self.activityLog_Master.update(self.activityLog_Current)
        self.activityLog_Daily['Activity Log'][time] = {'Activity': 'Connected', \
                                                        'Time': time, \
                                                        'Timestamp': timestamp}
        pickle.dump(self.activityLog_Master, open(self.activity_log_location + exchange_name + '_ActivityLog_Master.pickle', 'wb'))
        pickle.dump(self.activityLog_Daily, open(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.pickle', 'wb'))
        daily_log_dataframe = pd.DataFrame(self.activityLog_Daily['Activity Log'])
        daily_log_dataframe = daily_log_dataframe.T
        daily_log_dataframe.to_csv(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.csv')
        master_log_dataframe = pd.DataFrame(self.activityLog_Master)
        master_log_dataframe = master_log_dataframe.T
        master_log_dataframe.to_csv(self.activity_log_location + exchange_name + '_ActivityLog_Master.csv')
        return(self.exchange)

    # This is the primary function of the class. It creates the connections to cryptocurrency exchanges using API keys
    def connect_NEW(self, exchange_name=None, account_name=None):
        if not(exchange_name) or str(exchange_name).lower() == 'default':
            exchange_name = self.exchangeAccounts['Default Exchange']
        if not(account_name) or str(account_name).lower() == 'default':
            account_name = self.exchangeAccounts['Default Account']
        connected = False
        # The API information matching exchange_name and account_name is retrieved and read
        if self.exchangeAccounts[exchange_name][account_name]['apiKey'] == '':
            self.fetch_API_key(exchange_name, account_name)
        if len(self.exchangeAccounts[exchange_name][account_name]['apiKey']) > 100:
            try:
                key = self.CE.decrypt(self.exchangeAccounts[exchange_name][account_name]['apiKey'])[0:36]
                secret = self.CE.decrypt(self.exchangeAccounts[exchange_name][account_name]['secret'])[0:91]
            except Exception as error:
                self.inCaseOfError(**{'error': error, \
                                      'description': 'reading API key file', \
                                      'program': 'CTE', \
                                      'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
        else:
            key = self.exchangeAccounts[exchange_name][account_name]['apiKey']
            secret = self.exchangeAccounts[exchange_name][account_name]['secret']
        try:
            # The API connection to the exchange is made
            self.exchange = ccxt.kraken({'apiKey': key, \
                                         'secret': secret, \
                                         'timeout': 30000, \
                                         'enableRateLimit': True, \
                                         'options': {'adjustForTimeDifference': True, \
                                                     'defaultType': self.exchangeAccounts['Default Type'], \
                                                     'postOnly': True}})
            connected = True
        except Exception as error:
            self.inCaseOfError(**{'error': error, \
                                  'description': 'connecting to the exchange', \
                                  'program': 'CTE', \
                                  'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
            connected = False
        del key, secret
        if not(connected):
            print('CTE : ERROR! Failed to connect to exchange.')
            return(None)
        else:
            # Variables are assigned and the ActivityLog is updated
            self.currentConnectionDetails['Exchange Name'] = exchange_name
            self.currentConnectionDetails['Account Name'] = account_name
            self.exchange_name = exchange_name
            self.account_name = account_name
            date = self.GCT.getDateString()
            timestamp = self.GCT.getTimeStamp()
            time = self.GCT.getTimeString()
            self.availableSymbols[exchange_name] = list(self.exchange.loadMarkets())
            # Balances are automatically updated if they have been previously fetched
            if self.balances:
                self.balances = self.getBalances()
            # New entries are added to the Master Activity Log and Daily Activity Logs
            try:
                self.activityLog_Master = pickle.load(open(self.activity_log_location + exchange_name + '_ActivityLog_Master.pickle', 'rb'))
                if not(self.silent_mode):
                    print('\nCTE : ' + exchange_name + ' ' + account_name + ' Master Activity Log loaded!')
                largestTimestamp = max(self.activityLog_Master)
                if not(self.silent_mode):
                    print('CTE : The most recent activity was on ' + self.activityLog_Master[largestTimestamp]['Date'] + '!')
            except FileNotFoundError:
                self.activityLog_Master = {}
                if not(self.silent_mode):
                    print('CTE : No past Activity Log found!')
            try:
                self.activityLog_Daily = pickle.load(open(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.pickle', 'rb'))
                if not(self.silent_mode):
                    print('CTE : Daily Activity Log loaded!')
            except FileNotFoundError:
                self.activityLog_Daily = {'Date': date, \
                                          'Activity Log': {}}
                if not(self.silent_mode):
                    print('CTE : No Daily Activity Log found for today!')
            # A new activity log entry is created and saved
            self.currentConnectionDetails['Time of Access'] = str(datetime.now())
            self.activityLog_Current[timestamp] = {'Activity': 'Connected', \
                                                   'Date': date, \
                                                   'Time': time}
            self.activityLog_Master.update(self.activityLog_Current)
            self.activityLog_Daily['Activity Log'][time] = {'Activity': 'Connected', \
                                                            'Time': time, \
                                                            'Timestamp': timestamp}
            pickle.dump(self.activityLog_Master, open(self.activity_log_location + exchange_name + '_ActivityLog_Master.pickle', 'wb'))
            pickle.dump(self.activityLog_Daily, open(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.pickle', 'wb'))
            daily_log_dataframe = pd.DataFrame(self.activityLog_Daily['Activity Log'])
            daily_log_dataframe = daily_log_dataframe.T
            daily_log_dataframe.to_csv(self.activity_log_location + exchange_name + '_ActivityLog_Daily_' + date + '.csv')
            master_log_dataframe = pd.DataFrame(self.activityLog_Master)
            master_log_dataframe = master_log_dataframe.T
            master_log_dataframe.to_csv(self.activity_log_location + exchange_name + '_ActivityLog_Master.csv')
            return(self.exchange)

# This function is for retrieving API keys from a .txt file
# Each file should have the API information for one account, end in '_API.txt', and have the API key on the first line and the API secret on the second line
    def fetch_API_key(self, exchange_name, account_name):
        file_name = exchange_name + '_' + account_name + '_API.txt'
        API_key_file = False
        try:
            API_key_file = open(file_name, 'r')
        except:
            drive_list = ['D', 'E', 'F', 'G', 'H', 'I']
            for drive in drive_list:
                try:
                    API_location = drive + ':/API Keys/'
                    API_key_file = open(API_location + file_name, 'r')
                except:
                    del API_location
        if API_key_file:
            line_index = 0
            for line in API_key_file:
                if line_index == 0:
                    self.exchangeAccounts[exchange_name][account_name]['apiKey'] = line.split('\n')[0]
                elif line_index == 1:
                    self.exchangeAccounts[exchange_name][account_name]['secret'] = line.split('\n')[0]
                line_index += 1
        else:
            print('CTE : ERROR! Failed to find API Key file.')

# This function is for retrieving information about open trading positions
    def getPositions(self, exchange=None):
        if exchange:
            self.connect(exchange)
        elif not(self.exchange):            
            self.connect(self.exchangeAccounts['Default'])
        positions = False
        number_of_attempts = 0
        while not(positions):
            number_of_attempts += 1
            try:
                positions = self.exchange.fetch_positions(None, {'currency':'BTC'})
            except Exception as error:
                positions = False
                self.inCaseOfError(**{'error': error, \
                                      'description': 'fetching positions', \
                                      'program': 'CTE', \
                                      'line_number': traceback.format_exc().split('line ')[1].split(',')[0], \
                                      'number_of_attempts': number_of_attempts})
        # positions_dict is a tidier version of the raw position information retrieved by exchange.fetch_positions()
        positions_dict = {}
        positions_dict['Entry Price'] = float(positions[0]['avgEntryPrice'])
        positions_dict['Side'] = positions[0]['side']
        positions_dict['Leverage'] = float(positions[0]['leverage'])
        positions_dict['Amount'] = float(positions[0]['size'])
        positions_dict['Liqudation Price'] = float(positions[0]['liquidationPrice'])
        try:
            positions_dict['Stop Loss'] = float(positions[0]['stopLoss'])
        except:
            positions_dict['Stop Loss'] = False
        positions_dict['Raw Positions List'] = positions
        if not(self.silent_mode):
            print('CTE : Current POSITION fetched')
            for key in positions_dict:
                if key != 'Raw Positions List':
                    print('        ' + key + ': ' + str(positions_dict[key]))
        return(positions_dict)

# This function fetches the user's transaction history
# Users choose the symbol to look up, the type of transaction to look up, and the number of days of history they would like to see
    def getTransactionHistory(self, *args):
        if not(self.exchange):
            self.connect()
        if len(args) == 3:
            symbol = args[0]
            transaction_type = args[1]
            number_of_days = args[2]
        if len(args) == 2:
            symbol = args[0]
            transaction_type = args[1]
            number_of_days = False
        elif len(args) == 1:
            symbol = args[0]
            transaction_type = False
            number_of_days = False
        elif len(args) == 0:
            symbol = False
            transaction_type = False
            number_of_days = False
        while not(symbol):
            symbol = input("\nWhich symbol's transaction history would you like?\n").upper()
            if not(symbol.isalpha()):
                print('INPUT ERROR! Please enter the abbreviation of a cryptocurrency.')
                symbol = False
        while not(transaction_type):
            transaction_type = input("\nWhich type of transaction would you like?\n(1) Trade\n(2) Funding\n\nTransaction Type: ")
            if transaction_type == '1' or transaction_type.lower() == 'trade':
                transaction_type = 'Trade'
            elif transaction_type == '2' or transaction_type.lower() == 'funding':
                transaction_type = 'Funding'
            if (transaction_type != 'Trade') and (transaction_type != 'Funding'):
                print('INPUT ERROR! Please enter "1", "2", "trade" or "funding".')
                transaction_type = False
        while not(number_of_days):
            number_of_days = input("\nHow many days of history would you like?\n")
            try:
                number_of_days = int(number_of_days)
                square_root = math.sqrt(number_of_days)
            except:
                print('INPUT ERROR! Please enter a positive integer.')
                number_of_days = False
        if symbol == 'BTC':
            symbol = 'BTC/USD'
        elif len(symbol) < 5:
            symbol = symbol + '/BTC'
    # fetchMyTrades() retrieves the raw transaction history using CCXT
        rawTransactionHistory = self.exchange.fetchMyTrades(symbol, since=self.exchange.milliseconds() - (86400000 * number_of_days))
        transaction_history_dict = {}
        cleaned_history_dict = {}
        index = 0
    # This for loop tidies up the transactions to be readable in a CSV
        for transaction in rawTransactionHistory:
            if transaction['info']['tradeType'] in transaction_type:
                additional_dict = {}
                obsolete_keys = []
                for key in transaction:
                    if type(transaction[key]) == dict:
                        obsolete_keys.append(key)
                        for key_B in transaction[key]:
                            additional_dict[key_B + ' (' + key + ')'] = transaction[key][key_B]
                transaction.update(additional_dict)
                for key in obsolete_keys:
                    del transaction[key]
                cleaned_history_dict[index] = transaction
                index += 1
        transaction_history_Dataframe = pd.DataFrame(cleaned_history_dict)
        transaction_history_Dataframe = transaction_history_Dataframe.transpose()
        transaction_history_Dataframe.to_csv('Transaction History.csv')
        return(transaction_history_Dataframe)

                
# This function retrieves one's current account balances
    def getBalances(self, *args):
        self.balances = {}
    # Optional inputs, such as a cryptocurrency symbol, an exchange name, and an account name are interpreted from the input(s)
        if len(args) > 0:
            if type(args[0]) == str:
                symbol = args[0]
            elif type(args[0]) == dict:
                try:
                    symbol = args[0]['Symbol']
                except:
                    symbol = 'all'
                try:
                    exchange_name = args[0]['Exchange Name']
                except:
                    exchange_name = False
                try:
                    account_name = args[0]['Account Name']
                except:
                    account_name = False
                if exchange_name:
                    if account_name:
                        self.connect(exchange_name, account_name)
                    else:
                        self.connect(exchange_name, 'default')
                else:
                    if account_name:
                        self.connect('default', account_name)
                    else:
                        self.connect('default')
        else:
            symbol = 'all'
        if not(self.exchange):
            self.connect()
        exchange_name = self.currentConnectionDetails['Exchange Name']
    # Spot Wallet balances are fetched and organized
        try:
            raw_spot_balances = self.exchange.fetch_balance()
            spot_balances = {}
            for key in raw_spot_balances:
                if key == key.upper():
                    if (symbol == 'all') or (key == symbol.upper()):
                        spot_balances[key] = raw_spot_balances[key]                    
            self.balances['Spot'] = spot_balances
        except Exception as error:
            self.inCaseOfError(**{'error': error, \
                                  'description': 'fetching Spot balances', \
                                  'program': 'CTE', \
                                  'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
    # Contract Trade Account balances are fetched and organized
        contract_balances = {}
        for available_symbol in self.availableSymbols[exchange_name]:
            if (symbol == 'all') or (available_symbol == symbol.upper()):
                available_symbol = available_symbol.split('/')[0]
                contract_balances[available_symbol] = {}
                try:
                    if available_symbol == 'BTC':
                        raw_contract_balance = self.exchange.fetch_balance(params={'type': 'swap', 'currency': available_symbol})
                        contract_balances[available_symbol]['free'] = float(raw_contract_balance[available_symbol]['free'])
                        contract_balances[available_symbol]['used'] = float(raw_contract_balance[available_symbol]['used'])
                        contract_balances[available_symbol]['total'] = float(raw_contract_balance[available_symbol]['total'])
                        contract_balances[available_symbol]['dict'] = raw_contract_balance
                except Exception as error:
                    self.inCaseOfError(**{'error': error, \
                                          'description': 'fetching ' + available_symbol + ' Contract balance', \
                                          'program': 'CTE', \
                                          'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
        self.balances['Contract'] = contract_balances
        return(self.balances)


# This function retrieves the user's balances but leaves out symbols that the user doesn't have any of
    def getNonzeroBalances(self, *args):
        if len(args) == 1:
            self.connect(args[0])
        else:
            try:
                shit = self.exchange
            except:
                self.connect('binance')
        nonzeroBalances = {}
        balances = self.getBalances(self.exchange)
        for key in balances:
            try:
                if (balances[key]['free'] > 0) or (balances[key]['used'] > 0) or (balances[key]['total'] > 0):
                    nonzeroBalances[key] = {'free': 0, 'used': 0, 'total': 0}
                    nonzeroBalances[key]['free'] = balances[key]['free']
                    nonzeroBalances[key]['used'] = balances[key]['used']
                    nonzeroBalances[key]['total'] = balances[key]['total']
            except:
                zero = 0
        for key in nonzeroBalances:
            if not(self.silent_mode):
                print(key, nonzeroBalances[key]['free'])
        return(nonzeroBalances)

# This function returns information about the user's currently open orders
    def checkOrders(self, *args):
        if len(args) == 1:
            mainSymbol = args[0]
            try:
                shit = self.exchange
            except:
                self.connect('binance')
        elif len(args) == 2:
            mainSymbol = args[0]
            self.connect(args[1])
        else:
            mainSymbol = 'all'
            try:
                shit = self.exchange
            except:
                self.connect('binance')
        if mainSymbol == 'all':
            symbolsInOrder = {}
            for symbol in self.symbols_All:
                if self.balances[symbol.split('/')[0]]['used'] > 0:
                    symbolsInOrder[symbol] = self.balances[symbol.split('/')[0]]['used']
            #print(symbolsInOrder)
            return(symbolsInOrder)
        else:
            quantityInOrder = self.balances[mainSymbol.split('/')[0]]['used']
            #print(quantityInOrder)
            return(quantityInOrder)
    
# This function returns the current bid price of an asset (which is essentially its current price)
    def getCurrentBid(self, *args):
    #arg 0 : symbol
        try:
            symbol = args[0]
        except:
            symbol = 'BTC/USD'
    #arg 1 : exchange
        try:
            self.exchange = args[1]
            self.exchange.fetchTicker('BTC/USDT')
        except:
            try:
                self.exchange.fetchTicker('BTC/USDT')
            except:
                self.exchange = self.connect(self.exchangeAccounts['Default'])
        current_bid = self.exchange.fetchTicker(symbol)['bid']
        return(current_bid)

# This function returns the Open, High, Low, Close, and Volume values for a particular asset and with a particular timeframe
    def getOHLCVs(self, *args):
    #arg 0 : exchange
        if not(self.exchange):
            try:
                self.exchange = self.connect(args[0])
            except:
                self.exchange = self.connect()
    #arg 1 : symbol
        try:
            symbol = args[1]
        except:
            symbol = input("\nWhich symbol's OHLCV would you like?\nSymbol : ")
        if symbol == 'BTC':
            symbol = 'BTC/USD'
    #arg 2 : timeframe
        try:
            timeframe = args[2]
        except:
            timeframe = input('\nWhich timeframe should be used for the OHLCV?\n(1) : 1m\n(2) : 1h\n(3) : 1D\n\nTimeframe : ')
            if timeframe == '1':
                timeframe = '1m'
            elif timeframe == '2':
                timeframe = '1h'
            elif timeframe == '3':
                timeframe = '1D'
    #arg 3 : limit
        try:
            ohlcv_limit = args[3]
        except:
            ohlcv_limit = 1999
    #arg 4 : improvement_modifiers
        try:
            improvement_modifiers = args[4]
        except:
            improvement_modifiers = {}
    #arg 5 : export
        try:
            export = args[5]
        except:
            export = str(input('\nWould you like to export the OHLCVs to CSV?\n(1) Yes\n(2) No\nInput: '))
        if export == '1' or export.lower() == 'yes':
            export = True
        else:
            export = False
        if not(self.silent_mode):
            print('CTE : Fetching OHLCVs............................')
        OHLCVs = self.exchange.fetchOHLCV(symbol, timeframe, limit=ohlcv_limit)
        if not(self.silent_mode):
            print('CTE : OHLCVs fetched!')
    # This adds the date & time to each OHLCV
        for OHLCV in OHLCVs:
            OHLCV.append(self.GCT.convert_TimeStampToDateTime(OHLCV[0]))
        self.updateMasterOHLCVs(OHLCVs, timeframe)
        OHLCVs = pd.DataFrame(OHLCVs, columns=self.improved_columns)
        if improvement_modifiers != {}:
            improved_OHLCVs = self.improveOHLCVs(OHLCVs, improvement_modifiers)
            if export:
                current_time_string = self.GCT.getDateTimeString()
                OHLCVs.to_csv('_OHLCV_Repository/OHLCVs ' + current_time_string + '.csv')
                improved_OHLCVs.to_csv(path_or_buf='_OHLCV_Repository/ImprovedOHLCVs ' + current_time_string + '.csv')
            return(improved_OHLCVs)
        else:
            if export:
                current_time_string = self.GCT.getDateTimeString()
                OHLCVs.to_csv('_OHLCV_Repository/OHLCVs ' + current_time_string + '.csv')
            return(OHLCVs)

# This function calculates numerous moving averages and other analytical data using the raw OHLCVs
    def improveOHLCVs(self, OHLCVs, modifiers):
        if not(self.silent_mode):
            print('\nCTE : Improving OHLCVs...')
        if type(OHLCVs) == list:
            OHLCVs = pd.DataFrame(OHLCVs, columns=self.improved_columns)
        try:
            self.which_OHLC = modifiers['Which OHLC']
        except:
            self.which_OHLC = 'Close'
        mean_price = sum(OHLCVs[self.which_OHLC]) / len(OHLCVs[self.which_OHLC])
    # This is no longer necessary because we always add the date & time
##    # Adds the date to each OHLCV
##        if not(self.silent_mode):
##            print('improveOHLCVs : Dates are being added...')
##        date_list = []
##        for timestamp in OHLCVs['Timestamp']:
##            date = self.GCT.convert_TimeStampToDate(int(timestamp))
##            date_list.append(date)
##        OHLCVs['Date'] = date_list
    # Adds a Standard Deviation value to each OHLCV
        if not(self.silent_mode):
            print('CTE : The standard deviation is being added...')
        difference_list = []
        squared_difference_list = []
        variance_list = []
        standard_deviation_list = []
        for price in OHLCVs[self.which_OHLC]:
            difference_from_mean = price - mean_price
            difference_list.append(difference_from_mean)
            squared_difference_list.append(difference_from_mean * difference_from_mean)
        variance = sum(squared_difference_list) / len(squared_difference_list)
        standard_deviation = math.sqrt(variance)
        for price in OHLCVs[self.which_OHLC]:
            variance_list.append(variance)
            standard_deviation_list.append(standard_deviation)
            
    # Adds a "change" value and "% change" to each OHLCV (the amount the price rose or fell)
        if not(self.silent_mode):
            print('CTE : The change in price and & change in price since the last time interval is being added...')
        change_list = []
        change_percent_list = []
        index = 0
        for price in OHLCVs[self.which_OHLC]:
            if index == 0:
                change = 0
                change_percent = 0
            else:
                change = price - last_price
                change_percent = change / last_price
            change_list.append(change)
            change_percent_list.append(change_percent)
            last_price = price
            index += 1
        OHLCVs['Change'] = change_list
        OHLCVs['% Change'] = change_percent_list
        if ('% Change 100x' in modifiers['Indicators']) or ('% Change 1000x' in modifiers['Indicators']) or \
           ('% Change 10000x' in modifiers['Indicators']) or ('% Change 100000x' in modifiers['Indicators']):
            change_percent_100x_list = []
            change_percent_1000x_list = []
            change_percent_10000x_list = []
            change_percent_100000x_list = []
            for percent in change_percent_list:
                change_percent_100x_list.append(int(percent * 100))
                change_percent_1000x_list.append(int(percent * 1000))
                change_percent_10000x_list.append(int(percent * 10000))
                change_percent_100000x_list.append(int(percent * 100000))
            OHLCVs['% Change 100x'] = change_percent_100x_list
            OHLCVs['% Change 1000x'] = change_percent_1000x_list
            OHLCVs['% Change 10000x'] = change_percent_10000x_list
            OHLCVs['% Change 100000x'] = change_percent_100000x_list
            del change_percent_100x_list[0]
            del change_percent_1000x_list[0]
            del change_percent_10000x_list[0]
            del change_percent_100000x_list[0]
            change_percent_100x_list.append(0)
            change_percent_1000x_list.append(0)
            change_percent_10000x_list.append(0)
            change_percent_100000x_list.append(0)
            if '% Change 100x' in modifiers['Indicators']:
                OHLCVs['% Change 100x +'] = change_percent_100x_list
            if '% Change 1000x' in modifiers['Indicators']:
                OHLCVs['% Change 1000x +'] = change_percent_1000x_list
            if '% Change 10000x' in modifiers['Indicators']:
                OHLCVs['% Change 10000x +'] = change_percent_10000x_list
            if '% Change 100000x' in modifiers['Indicators']:
                OHLCVs['% Change 100000x +'] = change_percent_100000x_list
    # OBV
        if ('OBV' in modifiers['Indicators']) or ('Delta OBV' in modifiers['Indicators']) or ('MA OBV' in modifiers['Indicators']) or ('MA Delta OBV' in modifiers['Indicators']):
            if not(self.silent_mode):
                print('CTE : The OBV is being added...')
            OBV_list = []
            index = 0
            for volume in OHLCVs['Volume']:
                if index == 0:
                    OBV = 0
                else:
                    if OHLCVs['Change'][index] > 0:
                        sign_variable = 1
                    elif OHLCVs['Change'][index] < 0:
                        sign_variable = -1
                    else:
                        sign_variable = 0
                    OBV_change = volume * sign_variable
                    OBV = last_OBV + OBV_change                
                OBV_list.append(OBV)
                last_OBV = OBV
                index += 1
            OHLCVs['OBV'] = OBV_list
    # Adds various time period-based values
        if ('Indicator Time Intervals' in modifiers) and (len(modifiers['Indicator Time Intervals']) > 0):
            OHLCVs = self.modifyOHLCVs_MovingTimeInterval(OHLCVs, modifiers)
    # Adds various change-based values
        if ('Delta Intervals' in modifiers) and (len(modifiers['Delta Intervals']) > 0):
            OHLCVs = self.modifyOHLCVs_DeltaInterval(OHLCVs, modifiers)
    # Creates moving averages and moving average exponentials of other indicators
        if ('Moving Average Intervals' in modifiers) and (len(modifiers['Moving Average Intervals']) > 0):
            OHLCVs = self.modifyOHLCVs_MovingAverages(OHLCVs, modifiers)
    # Adds tiers to the amount prices changed
        if ('Change Tiers' in modifiers) and (len(modifiers['Change Tiers']) > 0):
            OHLCVs = self.modifyOHLCVs_ChangeTiers(OHLCVs, modifiers['Change Tiers'])
    # Adds trough-peak values
        if ('Trough-Peak Values' in modifiers) and modifiers['Trough-Peak Values']:
            OHLCVs = self.findTP(OHLCVs)
    # Adds a "should buy" value to each OHLCV (0 or 1)
        if not(self.silent_mode):
            print('CTE : A "Should Buy" column is being added...')
        should_buy_list = []
        index = 0        
        for change in OHLCVs['Change']:
            if index > 0:
                if change > 0:
                    should_buy_list.append(1)
                else:
                    should_buy_list.append(0)
            index += 1
        should_buy_list.append(0)
        OHLCVs['Should Buy'] = should_buy_list        
        return(OHLCVs)

# This function calculates moving averages for specific time durations
    def modifyOHLCVs_MovingTimeInterval(self, OHLCVs, modifiers):
        time_interval_list = modifiers['Indicator Time Intervals']
        indicator_list = modifiers['Indicators']
        for time_interval in time_interval_list:
            OBV_list = []
            MAV_list = []
            MA_list = []
            EMA_list = []
            change_list = []
            percent_change_list = []
            should_buy_list = []
            VWAP_list = []
            most_recent_X = []
            for row_index in OHLCVs.index:
                OHLCV = OHLCVs.ix[row_index,]
                OHLCV['index'] = row_index
                most_recent_X.append(OHLCV)
                if len(most_recent_X) > time_interval:
                    del most_recent_X[0]
            # OBV-X
                if ('OBV-X' in indicator_list) or ('Delta OBV-X' in indicator_list) or ('MA Delta OBV-X' in indicator_list) or ('EMA Delta OBV-X' in indicator_list) \
                   or ('MA OBV-X' in indicator_list) or ('EMA OBV-X' in indicator_list):
                    if row_index > 0:
                        OBV_X = 0
                        for recent_OHLCV in most_recent_X:
                            if recent_OHLCV['Change'] > 0:
                                sign_variable = 1
                            elif recent_OHLCV['Change'] < 0:
                                sign_variable = -1
                            else:
                                sign_variable = 0
                            OBV_change = recent_OHLCV['Volume'] * sign_variable
                            OBV_X = OBV_X + OBV_change
                    else:
                        OBV_X = 0
                    OBV_list.append(OBV_X)
            # MAV-X
                if ('MAV-X' in indicator_list) or ('Delta MAV-X' in indicator_list) or ('MA Delta MAV-X' in indicator_list) or ('EMA Delta MAV-X' in indicator_list) \
                   or ('MA MAV-X' in indicator_list) or ('EMA MAV-X' in indicator_list):
                    recent_volume_list = []
                    for recent_OHLCV in most_recent_X:
                        recent_volume_list.append(recent_OHLCV['Volume'])
                    MAV_X = sum(recent_volume_list) / len(recent_volume_list)
                    MAV_list.append(MAV_X)
            # MA-X
                if ('MA-X' in indicator_list) or ('Delta MA-X' in indicator_list) or ('MA Delta MA-X' in indicator_list) or ('EMA Delta MA-X' in indicator_list) \
                   or ('MA MA-X' in indicator_list) or ('EMA MA-X' in indicator_list):
                    recent_price_list = []
                    for recent_OHLCV in most_recent_X:
                        recent_price_list.append(recent_OHLCV[self.which_OHLC])
                    MA_X = sum(recent_price_list) / len(recent_price_list)
                    MA_list.append(MA_X)
            # EMA-X
                if ('EMA-X' in indicator_list) or ('Delta EMA-X' in indicator_list) or ('MA Delta EMA-X' in indicator_list) or ('EMA Delta EMA-X' in indicator_list) \
                   or ('MA EMA-X' in indicator_list) or ('EMA EMA-X' in indicator_list):
                    if row_index == 0:
                        EMA_X = OHLCV[self.which_OHLC]
                    else:
                        EMA_multiplier = self.EMA_smoother / (len(most_recent_X) + 1)
                        EMA_X = (OHLCV[self.which_OHLC] * EMA_multiplier) + (EMA_list[len(EMA_list) - 1] * (1 - EMA_multiplier))
                    EMA_list.append(EMA_X)
            # Change-X
                if ('Change-X' in indicator_list) or ('MA Change-X' in indicator_list) or ('EMA Change-X' in indicator_list):
                    change = OHLCV[self.which_OHLC] - most_recent_X[0][self.which_OHLC]
                    change_list.append(change)
            # % Change-X
                if ('% Change-X' in indicator_list) or ('MA % Change-X' in indicator_list) or ('EMA % Change-X' in indicator_list):
                    if row_index == 0:
                        percent_change = 0
                    else:
                        percent_change = 100 * (OHLCV[self.which_OHLC] - most_recent_X[0][self.which_OHLC]) / OHLCVs.ix[row_index - 1,][self.which_OHLC]
                    percent_change_list.append(percent_change)
            
            # VWAP-X
                if ('VWAP-X' in indicator_list) or ('Delta VWAP-X' in indicator_list) or ('MA Delta VWAP-X' in indicator_list) or ('EMA Delta VWAP-X' in indicator_list) \
                   or ('MA VWAP-X' in indicator_list) or ('EMA VWAP-X' in indicator_list):
                    recent_volume_list = []
                    for recent_OHLCV in most_recent_X:
                        recent_volume_list.append(recent_OHLCV['Volume'])
                    recent_volume_price_product_list = []
                    index = 0
                    for recent_OHLCV in most_recent_X:
                        recent_volume_price_product_list.append(recent_OHLCV[self.which_OHLC] * recent_volume_list[index])
                        index += 1
                    VWAP_X = sum(recent_volume_price_product_list) / sum(recent_volume_list)                    
                    VWAP_list.append(VWAP_X)
            # Should Buy-X
                if 'Should Buy-X' in indicator_list:
                # This if makes the calculation of Should Buy-X delayed by X iterations
                    if len(most_recent_X) >= time_interval:
                        if row_index < len(OHLCVs.index) - 1:
                            recent_X_prices = []
                            for recent_OHLCV in most_recent_X:
                                if recent_X_prices == []:
                                    oldest_price = recent_OHLCV[self.which_OHLC]
                                recent_X_prices.append(recent_OHLCV[self.which_OHLC])
                            if max(recent_X_prices) > oldest_price:
                                should_buy_list.append(1)
                            else:
                                should_buy_list.append(0)
                    # This if fills up the Should Buy-X's that we're missing because of the delay
                        else:
                            recent_X_prices = []
                            for recent_OHLCV in most_recent_X:
                                if recent_X_prices == []:
                                    oldest_price = recent_OHLCV[self.which_OHLC]
                                recent_X_prices.append(recent_OHLCV[self.which_OHLC])
                            while len(recent_X_prices) > 0:
                                if max(recent_X_prices) > oldest_price:
                                    should_buy_list.append(1)
                                else:
                                    should_buy_list.append(0)
                                del recent_X_prices[0]
                                try:
                                    oldest_price = recent_X_prices[0]
                                except:
                                    shit = 'balls'
            if len(OBV_list) > 0:
                OHLCVs['OBV-' + str(time_interval)] = OBV_list
            if len(MAV_list) > 0:
                OHLCVs['MAV-' + str(time_interval)] = MAV_list
            if len(MA_list) > 0:
                OHLCVs['MA-' + str(time_interval)] = MA_list
            if len(EMA_list) > 0:
                OHLCVs['EMA-' + str(time_interval)] = EMA_list
            if len(change_list) > 0:
                OHLCVs['Change-' + str(time_interval)] = change_list
            if len(percent_change_list) > 0:
                OHLCVs['% Change-' + str(time_interval)] = percent_change_list
            if len(VWAP_list) > 0:
                OHLCVs['VWAP-' + str(time_interval)] = VWAP_list
            if len(should_buy_list) > 0:
                OHLCVs['Should Buy-' + str(time_interval)] = should_buy_list
            for row_index in OHLCVs.index:
                OHLCV = OHLCVs.ix[row_index,]
                try:
                    del OHLCV['index']
                except:
                    shit = 'balls'
        return(OHLCVs)

# This function calculates the difference between an OHLCV value and that same value some time earlier
    def modifyOHLCVs_DeltaInterval(self, OHLCVs, modifiers):
        indicator_list = modifiers['Indicators']
        delta_interval_list = modifiers['Delta Intervals']
        time_interval_list = modifiers['Indicator Time Intervals']
        delta_dict_Master = {}
        for delta_interval in delta_interval_list:
            delta_dict_Master[delta_interval] = {}
            for indicator in indicator_list:
                if 'Delta' in indicator:
                    raw_indicator_name = indicator.split('Delta ')[1]
                    if '-X' in raw_indicator_name:
                        raw_indicator_name = raw_indicator_name.split('X')[0]
                        for time_interval in time_interval_list:
                            if delta_interval > 1:
                                delta_dict_Master[delta_interval]['Delta-' + str(delta_interval) + ' ' + raw_indicator_name + str(time_interval)] = []
                            elif delta_interval == 1:
                                delta_dict_Master[delta_interval]['Delta ' + raw_indicator_name + str(time_interval)] = []
                    else:
                        if delta_interval > 1:
                            delta_dict_Master[delta_interval]['Delta-' + str(delta_interval) + ' ' + raw_indicator_name] = []
                        elif delta_interval == 1:
                            delta_dict_Master[delta_interval]['Delta ' + raw_indicator_name] = []
        for delta_interval in delta_dict_Master:
            for row_index in OHLCVs.index:
                OHLCV = OHLCVs.ix[row_index,]   
                for delta_indicator in delta_dict_Master[delta_interval]:
                    if delta_interval == 1:
                        raw_indicator_name = delta_indicator.split('Delta ')[1]
                    else:
                        raw_indicator_name = delta_indicator.split('Delta-')[1].split(' ')[1]
                    if row_index > 0:
                        if row_index >= delta_interval:
                            delta_value = OHLCV[raw_indicator_name] - OHLCVs[raw_indicator_name][row_index - delta_interval]
                        else:
                            delta_value = OHLCV[raw_indicator_name] - OHLCVs[raw_indicator_name][0]
                    else:
                        delta_value = 0
                    delta_dict_Master[delta_interval][delta_indicator].append(delta_value)
    # End
        for delta_interval in delta_dict_Master:
            for column_name in delta_dict_Master[delta_interval]:
                OHLCVs[column_name] = delta_dict_Master[delta_interval][column_name]
        return(OHLCVs)

# This function calculates moving averages for prices in the OHLCVs, as well as moving averages of moving averages or moving averages of delta intervals
    def modifyOHLCVs_MovingAverages(self, OHLCVs, modifiers):
        time_interval_list = modifiers['Moving Average Intervals']
        indicator_list = modifiers['Indicators']
        moving_average_dict_Master = {}
        Emoving_average_dict_Master = {}
        nut_once = True
        for time_interval in time_interval_list:
            moving_average_dict_Master[time_interval] = {}
            moving_average_dict_Master[time_interval] = {}
            most_recent_X = []
            for row_index in OHLCVs.index:
                OHLCV = OHLCVs.ix[row_index,]
                OHLCV['index'] = row_index
                most_recent_X.append(OHLCV)
                if len(most_recent_X) > time_interval:
                    del most_recent_X[0]
                for indicator in indicator_list:
                    if 'MA ' in indicator:
                        if 'EMA ' in indicator:
                            moving_average_type = 'EMA'
                        else:
                            moving_average_type = 'MA'
                        if '-X' in indicator:
                            raw_indicator_name = indicator.split(moving_average_type + ' ')[1].split('-X')[0]
                            no_X = False
                        else:
                            raw_indicator_name = indicator.split(moving_average_type + ' ')[1]
                            no_X = True
                        for column_name in OHLCVs.columns:
                            if (raw_indicator_name in column_name) or \
                               (('Delta-' in column_name) and \
                                ('Delta' in raw_indicator_name) and \
                                (raw_indicator_name.split('Delta ')[1] in column_name)):
                                recent_value_list = []
                            # This checks for accidentally confusing the MA and the MAV (since 'MA' is in 'MAV')
                                MA_MAV_check = True
                                if 'MAV' in column_name:
                                    if 'MAV' in raw_indicator_name:
                                        MA_MAV_check = True
                                    else:
                                        MA_MAV_check = False
                            # This checks for accidentally confusing the MA and the EMA (since 'MA' is in 'EMA')
                                MA_EMA_check = True
                                if 'EMA' in column_name:
                                    if 'EMA' in raw_indicator_name:
                                        MA_EMA_check = True
                                    else:
                                        MA_EMA_check = False
                            # This checks for accidentally confusing a non-Delta indicator with a Delta column
                                delta_check = True
                                if 'Delta' in column_name:
                                    if 'Delta' in raw_indicator_name:
                                        delta_check = True
                                    else:
                                        delta_check = False
                            # This checks for accidentally confusing the OBV with OBV-X
                                OBV_check = True
                                if 'OBV' in column_name:
                                    if 'OBV-' in column_name:
                                        if no_X:
                                            OBV_check = False
                                        else:
                                            OBV_check = True
                                    else:
                                        if no_X:
                                            OBV_check = True
                                        else:
                                            OBV_check = False
                            # This checks for accidentally confusing Change with Change-X and % Change
                                change_check = True
                                if 'Change' in column_name:
                                    if 'Change-' in column_name:
                                        if no_X:
                                            change_check = False
                                        else:
                                            change_check = True
                                    else:
                                        if no_X:
                                            change_check = True
                                        else:
                                            change_check = False
                                if '%' in column_name:
                                    if '%' in raw_indicator_name:
                                        change_check = change_check
                                    else:
                                        change_check = False
                                if MA_MAV_check and MA_EMA_check and delta_check and OBV_check and change_check:
                                    for recent_OHLCV in most_recent_X:
                                        recent_value_list.append(recent_OHLCV[column_name])
                                    if moving_average_type == 'MA':
                                        moving_average_value = sum(recent_value_list) / len(recent_value_list)
                                    else:
                                        EMA_multiplier = self.EMA_smoother / (len(most_recent_X) + 1)
                                        try:
                                            moving_average_value = (most_recent_X[len(most_recent_X) - 1][self.which_OHLC] * EMA_multiplier) + \
                                                                   (moving_average_value * (1 - EMA_multiplier))
                                        except:
                                            moving_average_value = most_recent_X[len(most_recent_X) - 1][self.which_OHLC]
                                        last_EMA = moving_average_value
                                    try:
                                        moving_average_dict_Master[time_interval][moving_average_type + '-' + str(time_interval) + ' ' + column_name].append(moving_average_value)
                                    except:
                                        moving_average_dict_Master[time_interval][moving_average_type + '-' + str(time_interval) + ' ' + column_name] = [moving_average_value]
                                    if nut_once:
                                        #if len(moving_average_dict_Master[time_interval][moving_average_type + '-' + str(time_interval) + ' ' + column_name]) == 1999:
                                            #print('a', column_name, '...', raw_indicator_name, time_interval)
                                        if len(moving_average_dict_Master[time_interval][moving_average_type + '-' + str(time_interval) + ' ' + column_name]) > 1999:
                                            nut_once = False
                                            print('More than 1999 entries accumulated for this column:', column_name, '\nRaw Indicator Name:', raw_indicator_name, '\nTime Interval:', time_interval)
    # End
        for time_interval in moving_average_dict_Master:
            for column_name in moving_average_dict_Master[time_interval]:
                #print('Column Name:', column_name, time_interval)
                #print(len(moving_average_dict_Master[time_interval][column_name]))
                OHLCVs[column_name] = moving_average_dict_Master[time_interval][column_name]
        return(OHLCVs)
                            
# This function adds a "change tier" value to each price in a dataframe of OHLCVs
# "Change tiers" are subjective percent levels that a user can assign to get a better idea of how much an asset's price is changing
# The value of this function has yet to be determined
    def modifyOHLCVs_ChangeTiers(self, OHLCVs, tier_dict, *args):
        if len(args) > 0:
            time_interval = args[0]
        else:
            time_interval = 50
        most_recent_X = []
        change_tier_list = []
        for row_index in OHLCVs.index:
            OHLCV = OHLCVs.ix[row_index,]
            most_recent_X.append(OHLCV)
            if len(most_recent_X) > time_interval - 1:
                del most_recent_X[0]
            if row_index == 0:
                change_tier = 0
            else:
                change_tier = 0
                if OHLCV['% Change'] > 0:
                    for tier in tier_dict:
                        if OHLCV['% Change'] * 100 > tier_dict[tier]:
                            if tier > change_tier:
                                change_tier = tier
                else:
                    for tier in tier_dict:
                        if OHLCV['% Change'] * -100 > tier_dict[tier]:
                            if (tier * -1) < change_tier:
                                change_tier = tier * (-1)
            change_tier_list.append(change_tier)
        OHLCVs['Change Tier'] = change_tier_list
        del change_tier_list[0]
        change_tier_list.append(0)
        OHLCVs['Change Tier +'] = change_tier_list
        return(OHLCVs)

# This function returns the "Troughs" and "Peaks" in a list of prices
# A "trough" occurs when the price starts to go up after going down. "Peaks" are the opposite
# The value of this function has yet to be determined
    def findTP(self, *args):
        if len(args) == 1:
            OHLCVs = args[0]
        trough_peak_list = []
        trend_list = []
        for row_index in OHLCVs.index:
            OHLCV = OHLCVs.ix[row_index,]
            if row_index == 0 or row_index == len(OHLCVs.index) - 1:
                trough_peak_value = 0
                trend_value = 0
            else:
                last_OHLCV = OHLCVs.ix[row_index - 1,]
                next_OHLCV = OHLCVs.ix[row_index + 1,]
                if last_OHLCV[self.which_OHLC] > OHLCV[self.which_OHLC]:
                    if  next_OHLCV[self.which_OHLC] > OHLCV[self.which_OHLC]:
                        trough_peak_value = -1
                        trend_value = 0
                    elif next_OHLCV[self.which_OHLC] <= OHLCV[self.which_OHLC]:
                        trough_peak_value = 0
                        trend_value = -1
                elif last_OHLCV[self.which_OHLC] <= OHLCV[self.which_OHLC]:
                    if next_OHLCV[self.which_OHLC] < OHLCV[self.which_OHLC]:
                        trough_peak_value = 1
                        trend_value = 0
                    elif next_OHLCV[self.which_OHLC] >= OHLCV[self.which_OHLC]:
                        trough_peak_value = 0
                        trend_value = 1
            trough_peak_list.append(trough_peak_value)
            trend_list.append(trend_value)
        OHLCVs['Trough-Peak Value'] = trough_peak_list
        OHLCVs['Trend Value'] = trend_list
        return(OHLCVs)

# This function returns the current price of an asset
    def fetchCurrentPrice(self, *args):
        if not self.exchange:
            self.connect()
        try:
            symbol = args[0]['Symbol']
        except:
            symbol = 'BTC/USD'
        current_price = False
        number_of_attempts = 0
        while not(current_price):
            number_of_attempts += 1
            try:
                current_price = self.exchange.fetchTicker(symbol)['bid']
            except Exception as error:
                self.inCaseOfError(**{'error': error, \
                                      'description': 'checking the current BTC price', \
                                      'program': 'CTE', \
                                      'line_number': traceback.format_exc().split('line ')[1].split(',')[0], \
                                      'pause_time': 3, \
                                      'number_of_attempts': number_of_attempts})
                current_price = False
                if number_of_attempts % 3 == 0:
                    self.connect(self.exchangeAccounts['Default'])
        return(current_price)

# This function returns information about all of a user's open orders
    def fetchOpenOrders(self, *args):
        print('CTE : Fetching open orders...............')
        try:
            self.connect(args[0]['Exchange'])
        except:
            if not(self.exchange):
                self.connect(self.exchangeAccounts['Default'])
        try:
            symbol = args[0]['Symbol']
        except:
            symbol = 'BTCUSD'
        try:
            open_orders = self.exchange.fetchOpenOrders(symbol)
        except:
            open_orders = []
##        open_orders = False
##        number_of_attempts = 0
##        while not(open_orders):
##            number_of_attempts += 1
##            try:
##                open_orders = self.exchange.fetchOpenOrders(symbol)
##            except Exception as error:
##                self.inCaseOfError(**{'Error': error, \
##                                    'Description': 'trying to fetch open orders', \
##                                    'Program': 'CTE', \
##                                    '# of Attempts': number_of_attempts})
##                open_orders = False
##                print(number_of_attempts)
##                if number_of_attempts >= 3:
##                    open_orders = []
        if not(self.silent_mode):
            print('CTE : Open orders fetched!')
        return(open_orders)

# This function adds OHLCV information to an ever growing "master" OHLCV
# This is useful because most exchanges limit the number of data points that one can retrieve
    def updateMasterOHLCVs(self, OHLCVs, timeframe):
        master_OHLCVs = pd.read_csv(open(str(pathlib.Path().absolute()) + '/_OHLCV_Repository/Master ' + timeframe + ' OHLCVs.csv', 'rb'))
        master_latest_timestamp = int(master_OHLCVs['Timestamp'][len(master_OHLCVs['Timestamp']) - 1])
        OHLCVs_to_add = []        
        for OHLCV in OHLCVs:
            if OHLCV[0] > master_latest_timestamp:
                OHLCVs_to_add.append(OHLCV)
        OHLCVs_to_add_dataframe = pd.DataFrame(OHLCVs_to_add, columns=self.improved_columns)
        for column_name in OHLCVs_to_add_dataframe:
            if 'Unnamed' in column_name:
                del OHLCVs_to_add_dataframe[column_name]
        updated_master_OHLCVs = pd.concat([master_OHLCVs, OHLCVs_to_add_dataframe], ignore_index=True, sort=False)
        for column_name in updated_master_OHLCVs:
            if 'Unnamed' in column_name:
                del updated_master_OHLCVs[column_name]
        updated_master_OHLCVs.to_csv(str(pathlib.Path().absolute()) + '/_OHLCV_Repository/Master ' + timeframe + ' OHLCVs.csv')
        
# This function displays a message in case there is an error, and saves the information about the error to a CSV log
    def inCaseOfError(self, error=None, description=None, pause_time=0, program=None, line_number=None, number_of_attempts=1):
        print(program + ' : !!! ERROR occurred on line ' + str(line_number) + ' while ' + description)
        print(program + ' : Error: ' + str(error))
        pause_for_error = True
        starting_second = int(self.GCT.getTimeStamp())
        starting_datetime = self.GCT.getDateTimeString()
        error_dict = {'Time': starting_datetime, \
                      'Error': error, \
                      'Description': description, \
                      'Program': program, \
                      'Line #': line_number, \
                      '# of Attempts': number_of_attempts}
        self.error_log.append(error_dict)
        self.AP.playSound('Navi Hey')
        if pause_time > 0:
            print('CTE : Pausing for ' + str(pause_time) + ' seconds')
            while pause_for_error:
                current_second = int(self.GCT.getTimeStamp())
                if current_second - starting_second > pause_time:
                    pause_for_error = False
            print('CTE : Pause over! Returning to ' + description)
        return(error_dict)
        
# This will create the ConnectToExchange class in a non-local scope, making it more secure
if __name__ == "__main__":
    main()


