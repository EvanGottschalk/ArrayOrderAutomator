# PURPOSE - This program allows users to create simple orders & complex order arrays on cryptocurrency exchanges

# ConnectToExchange.py is used to create the actual communication via API to an exchange
from ConnectToExchange import ConnectToExchange
# QuadraticFormula.py is used to calculate "circular" array orders
from QuadraticFormula import *
# GetCurrentTime.py is used to get specific date and time information
from GetCurrentTime import GetCurrentTime

from AudioPlayer import AudioPlayer

import copy
import random

# Pandas and Pyplot are optional libraries for charting
try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import matplotlib.pyplot as pyplot
except ImportError:
    pyplot = None

# This function will create the OperateExchange class in a non-local scope, making it more secure
def main():
    OE = OperateExchange()
    OE.main_loop()
    del OE

class OperateExchange:
    def __init__(self):
        self.confirmation = False
        self.AP = AudioPlayer()
        self.CTE = ConnectToExchange()
        self.GCT = GetCurrentTime()
        self.orderSettings = {'Exchange': 'Coinbase', \
                              'Account': 'Main', \
                              'Symbol': 'BTC/USD', \
                              'Side': 'sell', \
                              'Amount': 5000, \
                              'Order Type': 'Limit', \
                              'Price': 30000}
        self.arrayOrderSettings = {'Granularity': 50, \
                                   'Spread': 2000, \
                                   'End Price': 28000, \
                                   'Steepness': 0, \
                                   'Slope': 1, \
                                   'Minimum Order Size': 1, \
                                   'Style': 'Linear', \
                                   'Multiplicative Factor': 0, \
                                   'Quick Granularity Intensity': 0, \
                                   'Quick Granularity Start %': 'default', \
                                   'Quick Granularity End %': 'default', \
                                   'Slow Granularity Multiplier': 0, \
                                   'Maximum Amount': 0, \
                                   'Readjust to Execute Maximum Amount': False, \
                                   'End Spread Start %': 0, \
                                   'End Spread Multiplier': 0}
        self.arrayOrderStyles_dict = {'1': 'Uniform', \
                                      '2': 'Linear', \
                                      '3': 'Circular', \
                                      '4': 'Transposed Circular', \
                                      '5': 'Parabolic', \
                                      '6': 'Fibonacci', \
                                      '7': 'Multiplicative'}
        self.arrayOrderParameters = {'Number of Orders': 0, \
                                     'Total Order Amount': 0, \
                                     'Lowest Price Order Price': 0, \
                                     'Lowest Price Order Amount': 0, \
                                     'Highest Price Order Price': 0, \
                                     'Highest Price Order Amount': 0, \
                                     'Entry at Full Execution': 0, \
                                     'Individual Order Settings': []}
        self.current_price = False
        self.fake_ID_count = 0
        self.arrayOrderLedger = {}
        self.arrayOrderHistory = {}
        self.tradeHistoryDict = {}
        self.tradeHistoryList = []
        self.tradeSessionDetails = {'Session Total PNL': 0}
        self.arrayOrderStyles_list = []
        for key in self.arrayOrderStyles_dict:
            self.arrayOrderStyles_list.append(self.arrayOrderStyles_dict[key])

    def main_loop(self):
        print('OE : main_loop initiated')

    def correctCloseDecimals(self, value):
        initial_value = value
        if '.99999' in str(value):
            value = int(round(value))
        elif '.099999' in str(value):
            value = float(round(value, 1))
        elif '.0099999' in str(value):
            value = float(round(value, 2))
        elif '.00099999' in str(value):
            value = float(round(value, 3))
        elif '.000099999' in str(value):
            value = float(round(value, 4))
        elif '.0000099999' in str(value):
            value = float(round(value, 5))
        elif '.00000' in str(value):
            value = int(value)
        elif '00000000000000' in str(value) and str(value).index('.') < str(value).index('00000000000000'):
            value = float(str(value).split('00000000000000')[0])
        elif '0000000000000' in str(value) and str(value).index('.') < str(value).index('0000000000000'):
            value = float(str(value).split('0000000000000')[0])
        elif '99999999999999' in str(value) and str(value).index('.') < str(value).index('99999999999999'):
            print('a', value)
            value = str(value).split('99999999999999')[0]
            print('b', value)
            remaining_decimal_places = len(str(value).split('.')[1])
            print('c', remaining_decimal_places)
            value = float(value)
            print('d', value)
            value = float(value + (1 / (10 ** remaining_decimal_places)))
            print('e', value)
        if initial_value != value:
            print('OE : correctCloseDecimals closed up some decimals!')
        return(value)

    def checkSymbolInput(self, symbol_input):
        try:
            symbol_input = str(symbol_input)
            if not(symbol_input in self.CTE.availableSymbols[self.CTE.exchange_name]):
                if symbol_input == 'DOGE/USD':
                    self.CTE.availableSymbols[self.CTE.exchange_name].append('DOGE/USD')
                elif symbol_input == 'BTCUSD':
                    self.CTE.availableSymbols[self.CTE.exchange_name].append('BTCUSD')
                else:
                    symbol_input = False
        except:
            symbol_input = False
        return(symbol_input)

    def checkAccountInput(self, exchange_input, account_input):
        print(exchange_input, account_input)
        try:
            account_input = str(account_input)
            if exchange_input.lower() == 'default':
                exchange_input = self.CTE.exchangeAccounts['Default Exchange']
            try:
                if not(self.CTE.exchangeAccounts[exchange_input][account_input]):
                    account_input = False
            except:
                account_input = False
        except:
            account_input = False
        return(account_input)

    def checkSideInput(self, side_input):
        try:
            side_input = str(side_input)
            if side_input.lower() == 'buy':
                side_input = 'buy'
            elif side_input.lower() == 'sell':
                side_input = 'sell'
            else:
                side_input = False
        except:
            side_input = False
        return(side_input)

    def checkAmountInput(self, amount_input):
        try:
            amount_input = int(amount_input)
            #print(amount_input / self.arrayOrderSettings['Granularity'], self.arrayOrderSettings['Spread'] ** 2)
            if amount_input < 0:
                amount_input = False
            if amount_input < self.arrayOrderSettings['Spread'] / self.arrayOrderSettings['Granularity']:
                amount_input = False
                print('\nERROR! Unable to create array order.\n    Cause: amount is too small for the spread.')
            #elif amount_input / self.arrayOrderSettings['Granularity'] > (self.arrayOrderSettings['Spread'] * 10) ** 2:
            #    amount_input = False
            #    print('\nERROR! Unable to create array order.\n    Cause: amount is too large for the spread.')
        except:
            amount_input = False
        return(amount_input)

    def checkPriceInput(self, price_input):
        try:
            price_input = float(price_input)
            symbol = self.orderSettings['Symbol']
            if price_input < 0:
                price_input = False
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                if price_input % .5 != 0:
                    price_input = False
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                price_input = round(float(price_input), 2)
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                price_input = round(float(price_input), 4)
        except:
            price_input = False
        return(price_input)

    def checkGranularityInput(self, granularity_input):
        try:
            granularity_input = float(granularity_input)
            symbol = self.orderSettings['Symbol']
            if granularity_input < 0:
                granularity_input = False
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                if granularity_input % .5 != 0:
                    granularity_input = False
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                granularity_input = round(float(granularity_input), 2)
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                granularity_input = round(float(granularity_input), 4)
        except:
            granularity_input = False
        return(granularity_input)

    def checkSpreadInput(self, spread_input):
        try:
            spread_input = float(spread_input)
            symbol = self.orderSettings['Symbol']
            if spread_input < 0:
                spread_input = False
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                if spread_input % .5 != 0:
                    spread_input = False
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                spread_input = round(float(spread_input), 2)
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                spread_input = round(float(spread_input), 4)
            if self.orderSettings['Amount'] < spread_input / self.arrayOrderSettings['Granularity']:
                spread_input = False
                print('\nERROR! OE Unable to create array order.\n    Cause: spread is too large for the trade amount.')
            #elif self.orderSettings['Amount'] / self.arrayOrderSettings['Granularity'] > 20 * (spread_input ** 2):
            #    spread_input = False
            #    print('\nERROR! OE Unable to create array order.\n    Cause: spread is too small for the trade amount.')
        except:
            spread_input = False
        return(spread_input)

    def checkEndPriceInput(self, end_price_input):
        try:
            end_price_input = float(end_price_input)
            symbol = self.orderSettings['Symbol']
            if end_price_input < 0:
                end_price_input = False
                print('\nERROR! OE Unable to create array order.\n    Cause: input value is negative.')
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                if end_price_input % .5 != 0:
                    end_price_input = False
                    print('\nERROR! OE Unable to create array order.\n    Cause: improper decimals for symbol.')
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                end_price_input = round(float(end_price_input), 2)
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                end_price_input = round(float(end_price_input), 4)
            if self.orderSettings['Side'] == 'buy':
                if end_price_input > self.orderSettings['Price']:
                    end_price_input = False
                    print('\nERROR! OE Unable to create array order.\n    Cause: end price is too high for entry price.')
            elif self.orderSettings['Side'] == 'sell':
                if end_price_input < self.orderSettings['Price']:
                    end_price_input = False
                    print('\nERROR! OE Unable to create array order.\n    Cause: end price is too low for entry price.')
        except:
            end_price_input = False
        return(end_price_input)

    def checkSteepnessInput(self, steepness_input):
        try:
            steepness_input = float(steepness_input)
        except:
            steepness_input = False
        steepness_input = round(steepness_input, 2)
        return(steepness_input)

    def checkSlopeInput(self, slope_input):
        try:
            slope_input = float(slope_input)
            if slope_input <= 0:
                print('\nOE : INPUT ERROR! Input a positive float value for Slope.')
        except:
            slope_input = False
            print('\nOE : INPUT ERROR! Input a positive float value for Slope.')
        slope_input = round(slope_input, 3)
        return(slope_input)

    def checkMinimumOrderSizeInput(self, minimum_order_size_input):
        try:
            minimum_order_size_input = int(minimum_order_size_input)
            if minimum_order_size_input < 0:
                minimum_order_size_input = False
        except:
            minimum_order_size_input = False
        return(minimum_order_size_input)

    def checkMaximumAmountInput(self, maximum_amount_input):
        try:
            maximum_amount_input = float(maximum_amount_input)
            if maximum_amount_input < 0:
                maximum_amount_input = False
            elif maximum_amount_input > self.orderSettings['Amount']:
                maximum_amount_input = self.orderSettings['Amount']
        except:
            maximum_amount_input = False
        return(maximum_amount_input)

    def checkQuickGranularityIntensityInput(self, quick_granularity_intensity_input):
        try:
            quick_granularity_intensity_input = int(quick_granularity_intensity_input)
            if quick_granularity_intensity_input < 0:
                quick_granularity_intensity_input = False
        except:
            quick_granularity_intensity_input = False
        return(quick_granularity_intensity_input)

    def checkQuickGranularityStartInput(self, quick_granularity_start_input):
        try:
            quick_granularity_start_input = float(quick_granularity_start_input)
            if quick_granularity_start_input < 0:
                quick_granularity_start_input = False
            elif quick_granularity_start_input >= 1:
                quick_granularity_start_input = quick_granularity_start_input / 100
                if quick_granularity_start_input >= 1:
                    quick_granularity_start_input = False
        # The Quick Granularity Start Input is checked against the End because the start can't be after the end
            if self.arrayOrderSettings['Quick Granularity End %'] == 'default':
                current_quick_granularity_end_percent = 1/3
            else:
                current_quick_granularity_end_percent = self.arrayOrderSettings['Quick Granularity End %']
            if current_quick_granularity_end_percent < quick_granularity_start_input:
                quick_granularity_start_input = False
                print('\nOE : Quick Granularity Start % NOT changed because the input Start % is greater than the current End %.')
        except:
            quick_granularity_start_input = False
        return(quick_granularity_start_input)

    def checkQuickGranularityEndInput(self, quick_granularity_end_input):
        try:
            quick_granularity_end_input = float(quick_granularity_end_input)
            if quick_granularity_end_input < 0:
                quick_granularity_end_input = False
            elif quick_granularity_end_input > 1:
                quick_granularity_end_input = quick_granularity_end_input / 100
                if quick_granularity_end_input > 1:
                    quick_granularity_end_input = False
        # The Quick Granularity End Input is checked against the Start because the end can't be before the start
            if self.arrayOrderSettings['Quick Granularity Start %'] == 'default':
                current_quick_granularity_start_percent = 0
            else:
                current_quick_granularity_start_percent = self.arrayOrderSettings['Quick Granularity Start %']
            if current_quick_granularity_start_percent > quick_granularity_end_input:
                quick_granularity_end_input = False
                print('\nOE : Quick Granularity End % NOT changed because the input End % is less than the current Start %.')
        except:
            quick_granularity_end_input = False
        return(quick_granularity_end_input)    
    

    def checkStyleInput(self, style_input):
        try:
            style_input = self.arrayOrderStyles_dict[style_input]
        except:
            if not(style_input in self.arrayOrderStyles_list):
                style_input = False
        return(style_input)

    def checkMultiplicativeFactorInput(self, multiplicative_factor_input):
        try:
            multiplicative_factor_input = float(multiplicative_factor_input)
        except:
            multiplicative_factor_input = False
        multiplicative_factor_input = round(multiplicative_factor_input, 2)
        return(multiplicative_factor_input)

    def createArrayOrder(self, *args):
    # This first part implements the array order with the current settings
        if (args[0] == 'use_current_settings') or (args[0] == 'update_current_parameters') or (args[0] == 'update_via_end_price'):
            self.CTE.exchange = self.CTE.connect(self.orderSettings['Exchange'], self.orderSettings['Account'])
            self.orderSettings['Attempt Execution'] = False
            symbol = self.orderSettings['Symbol']
            granularity = self.arrayOrderSettings['Granularity']
            if args[0] == 'update_via_end_price':
                end_price = self.arrayOrderSettings['End Price']
                if self.orderSettings['Side'] == 'buy':
                    spread = self.orderSettings['Price'] - end_price
                elif self.orderSettings['Side'] == 'sell':
                    spread = end_price - self.orderSettings['Price']
                self.arrayOrderSettings['Spread'] = spread
            else:
                spread = self.arrayOrderSettings['Spread']
            steepness_degree = self.arrayOrderSettings['Steepness']
            minimum_order_size = self.arrayOrderSettings['Minimum Order Size']
            style = self.arrayOrderSettings['Style']
            if style == 'Multiplicative':
                multiplicative_factor = self.arrayOrderSettings['Multiplicative Factor']
            else:
                multiplicative_factor = 0
            try:
                quick_granularity_intensity = self.arrayOrderSettings['Quick Granularity Intensity']
                try:
                    qg_start_percent = self.arrayOrderSettings['Quick Granularity Start %']
                    qg_end_percent = self.arrayOrderSettings['Quick Granularity End %']
                except:
                    qg_start_percent = 'default'
                    qg_end_percent = 'default'
                try:
                    slow_granularity_multiplier = self.arrayOrderSettings['Slow Granularity Multiplier']
                except:
                    slow_granularity_multiplier = 0
            except:
                quick_granularity_intensity = 0
            try:
                maximum_amount = self.arrayOrderSettings['Maximum Amount']
            except:
                maximum_amount = 0
                self.arrayOrderSettings['Maximum Amount'] = 0
            try:
                readjust_to_execute_maximum_amount = self.arrayOrderSettings['Readjust to Execute Maximum Amount']
            except:
                readjust_to_execute_maximum_amount = 0
            try:
                slope = self.arrayOrderSettings['Slope']
            except:
                slope = 0
            try:
                end_spread_start_percent = self.arrayOrderSettings['End Spread Start %']
                end_spread_multiplier = self.arrayOrderSettings['End Spread Multiplier']
            except:
                end_spread_start_percent = 0
                end_spread_multiplier = 0
        else:
            style = ''
            quick_granularity_intensity = 0
            maximum_amount = 0
            readjust_to_execute_maximum_amount = 0
        #arg 0 : create order?
            try:
                args[0].append('cancel_execution_attempt')
            except:
                args[0]['Attempt Execution'] = False
            try:
                self.orderSettings = self.createOrder(args[0])[0]
            except:
                self.orderSettings = self.createOrder()[0]
            self.orderSettings['Order Type'] = 'limit'
        #arg 1 : Dict of parameters?
            try:
                granularity_input = float(args[1]['Granularity'])
            except:
                try:
                    granularity_input = float(args[1])
                except:
                    granularity_input = 0
            try:
                spread_input = args[1]['Spread']
            except:
                try:
                    spread_input = args[2]
                except:
                    spread_input = 0
            try:
                steepness_input = float(args[1]['Steepness'])
            except:
                try:
                    steepness_input = float(args[3])
                except:
                    steepness_input = 0
            try:
                minimum_order_size_input = int(args[1]['Minimum Order Size'])
            except:
                try:
                    minimum_order_size_input = int(args[4])
                except:
                    minimum_order_size_input = self.arrayOrderSettings['Minimum Order Size']
                    #print('Minimum Order Size set to default: 1')
            try:
                style_input = args[1]['Style']
            except:
                try:
                    style_input = args[5]
                except:
                    style_input = False
            try:
                slope_input = args[1]['Slope']
            except:
                try:
                    slope_input = args[6]
                except:
                    slope_input = 0
        #arg 1 : granularity
            while type(granularity_input) != float:
                granularity_input = input('\nWhat granularity would you like to use? The default is ' + str(self.arrayOrderSettings['Granularity']) + '\n\nGranularity : ')
                granularity_input = self.checkGranularityInput(granularity_input)
            granularity = granularity_input
        #arg 2 : spread
            while type(spread_input) != int: 
                spread_input = input('\nWhat spread would you like to use? The default is ' + str(self.arrayOrderSettings['Spread']) + '\n\nSpread : ')
                spread_input = self.checkSpreadInput(spread_input)
            spread = spread_input
        #arg 3 : steepness
            while type(steepness_input) != float:
                steepness_input = input('\nWhat steepness degree would you like to use? The default is ' + str(self.arrayOrderSettings['Steepness']) + '\n\nSteepness : ')
                steepness_input = self.checkSteepnessInput(steepness_input)
            steepness_degree = steepness_input
        #arg 4 : minimum order size
            while type(minimum_order_size_input) != int: 
                minimum_order_size_input = input('\nWhat would you like the minimum order size to be? The default is ' + str(self.arrayOrderSettings['Minimum Order Size']) + '\n\nMinimum Order Size : ')
                minimum_order_size_input = self.checkMinimumOrderSizeInput(minimum_order_size_input)
            minimum_order_size = minimum_order_size_input
        #arg 5 : style    
            while not(style_input in self.arrayOrderStyles_list):
                style_input = input('\nWhat style of order creation would you like to use?\n(1) : Uniform\n(2) : Linear\n(3) : Circular' + \
                                  '\n(4) : Transposed Circular\n(5) : Parabolic\n(6) : Fibonacci\n(7) : Multiplicative\n\nStyle : ')
                style_input = self.checkStyleInput(style_input)
            style = style_input
            if style == 'Multiplicative':
                factor_input = False
                while not(factor_input):
                    factor_input = input('\nWhat multiplicative factor would you like to use?\n\nMultiplicative Factor : ')
                    try:
                        factor_input = float(factor_input)
                    except:
                        factor_input = False
                multiplicative_factor = factor_input
            else:
                multiplicative_factor = 0
        #arg 6 : slope
            while type(slope_input) != float:
                slope_input = input('\nWhat slope would you like to use? The default is 1\n\nSlope : ')
                slope_input = self.checkSlopeInput(slope_input)
            slope = slope_input
    # Important variables are assigned
        if self.orderSettings['Side'] == 'buy':
            side_multiplier = -1
        elif self.orderSettings['Side'] == 'sell':
            side_multiplier = 1
        self.arrayOrderSettings['Granularity'] = granularity
        if not(args[0] == 'update_via_end_price'):
            self.arrayOrderSettings['Spread'] = spread
            self.arrayOrderSettings['End Price'] = self.orderSettings['Price'] + (spread * side_multiplier)
        self.arrayOrderSettings['Steepness'] = steepness_degree
        self.arrayOrderSettings['Slope'] = slope
        self.arrayOrderSettings['Minimum Order Size'] = minimum_order_size
        self.arrayOrderSettings['Style'] = style
        self.arrayOrderSettings['Multiplicative Factor'] = multiplicative_factor
        self.arrayOrderSettings['Slow Granularity Multiplier'] = slow_granularity_multiplier
        effective_amount = self.orderSettings['Amount']
        price = self.orderSettings['Price']
        side = self.orderSettings['Side']
        if 1 < 0:#self.orderSettings['Amount'] < spread / granularity:
            print('\n!!! Array Order Error! Unable to create array order. Cause: spread is too large for the trade amount.')
        else:
    # Array Order Calculation
        # Displays text describing settings to be used
            print('\nOE : - Order Settings -')
            for key in self.orderSettings:
                print('        ' + str(key) + ': ' + str(self.orderSettings[key]))
            print('\nOE : - Array Order Settings -')
            for key in self.arrayOrderSettings:
                print('        ' + str(key) + ': ' + str(self.arrayOrderSettings[key]))
            print('\n\nOE : Calculating array order..........................................................\n')
            number_of_orders = int(spread / granularity) + 1
        # This while loop ensures that the number of orders isn't larger than the order amount
            if number_of_orders > self.orderSettings['Amount']:
                if self.orderSettings['Symbol'] == 'BTC' or self.orderSettings['Symbol'] == 'BTC/USD' or \
                   self.orderSettings['Symbol'] == 'BTC/USDT':
                    granularity_modifier = .5
                elif self.orderSettings['Symbol'] == 'LTC' or self.orderSettings['Symbol'] == 'LTC/USD' or \
                     self.orderSettings['Symbol'] == 'LTC/USDT' or self.orderSettings['Symbol'] == 'LTC/BTC':
                    granularity_modifier = .01
                elif self.orderSettings['Symbol'] == 'DOGE' or self.orderSettings['Symbol'] == 'DOGE/USD' or \
                     self.orderSettings['Symbol'] == 'DOGE/USDT' or self.orderSettings['Symbol'] == 'DOGE/BTC':
                    granularity_modifier = .0001
                else:
                    granularity_modifier = .5
                while number_of_orders > self.orderSettings['Amount']:
                    granularity += granularity_modifier                
                    number_of_orders = int(spread / granularity) + 1
                    print('OE : Granularity CHANGED to ' + str(granularity) + ' so that the number of orders ' + str(number_of_orders) + \
                          ' is less than the intended total array order amount ' + str(self.orderSettings['Amount']))
                granularity = granularity * 2
                number_of_orders = int(spread / granularity) + 1
                print('\nOE : Granularity DOUBLED to ' + str(granularity) + ' so the shape of the array can be expressed!')
        # Variables are initialized
            array_of_orders = []
            weighted_order_list = []
            total_order_amount = 0
            count = 0
        # Uniform Arrays
            if style == 'Uniform':
                amount_per_order = self.orderSettings['Amount'] / number_of_orders
                remainder_waiting = False
                for num in range(number_of_orders):
                    individual_order = copy.deepcopy(self.orderSettings)
                    individual_order['Amount'] = amount_per_order
                    while individual_order['Amount'] - int(individual_order['Amount']) != 0:
                        if remainder_waiting:
                            individual_order['Amount'] += remainder
                            remainder_waiting = False
                        else:
                            remainder = individual_order['Amount'] - int(individual_order['Amount'])
                            remainder = self.correctCloseDecimals(remainder)
                            individual_order['Amount'] = int(individual_order['Amount'])
                            remainder_waiting = True
                        count +=1
                    individual_order['Price'] = self.orderSettings['Price'] + ((granularity * num) * side_multiplier)
                    individual_order['Price'] = self.correctCloseDecimals(individual_order['Price'])
                    array_of_orders.append(individual_order)
                    weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                    total_order_amount += individual_order['Amount']
        # Non-Uniform Arrays
            elif style == 'Linear' or \
                 style == 'Circular' or \
                 style == 'Transposed Circular' or \
                 style == 'Parabolic' or \
                 style == 'Fibonacci' or \
                 style == 'Multiplicative':
                amount_modifier = 1
                amount_modifier_modifier = .1
                array_shape_lenience = .005
                potentialArrayOrderLog = []
                if 'Transposed' in style:
                    transpose = spread
                else:
                    transpose = 0
                array_calculation_loop = True
                while array_calculation_loop:
                    count += 1
                    array_of_orders = []
                    weighted_order_list = []
                    fibonacci_series = []
                    fibonacci_number = 1
                    total_order_amount = 0
                    remainder = 0
                    for num in range(number_of_orders):
                        individual_order = copy.deepcopy(self.orderSettings)
                        if num == 0 or num == 1:
                            fibonacci_number = 1
                        else:
                            fibonacci_number = fibonacci_series[len(fibonacci_series) - 1] + fibonacci_series[len(fibonacci_series) - 2]
                        fibonacci_series.append(fibonacci_number)
                    # Linear
                        if style == 'Linear':
                            amount = num * granularity
                    # Parabolic
                        elif style == 'Parabolic':
                            amount = ((num) ** 2)* granularity
                    # Fibonacci
                        elif style == 'Fibonacci':
                            amount = fibonacci_number * granularity
                    # Multiplicative
                        elif style == 'Multiplicative':
                            amount = (multiplicative_factor ** (num)) * granularity
                    # Circular
                        elif 'Circular' in style:
                            a = 1
                            b = (-2) * spread
                            c = ((num + transpose) * granularity) ** 2
                            #print(a, b, c)
                            quadratic_solutions = quadratic_formula(a, b, c)
                            amount = max(quadratic_solutions)
                            if (amount <= 0) or (amount > spread):
                                amount = min(quadratic_solutions)
                    # Steepness is calculated and applied
                        steepness_modification = 1 / ((((number_of_orders - (num * .5)) / number_of_orders)) ** steepness_degree)
                        amount = amount * steepness_modification
                    # amount_modifier is applied
                        individual_order['Amount'] = int((amount * amount_modifier) + remainder)
                    # Price is raised to 1 if 0 and the remainder is calcluated
                        if individual_order['Amount'] <= minimum_order_size:
                            individual_order['Amount'] = minimum_order_size
                        remainder = float(amount * amount_modifier) - int(amount * amount_modifier)
                        individual_order['Price'] = self.orderSettings['Price'] + ((granularity * num) * side_multiplier)
                        if num < number_of_orders - transpose:
                            array_of_orders.append(individual_order)
                            weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                            total_order_amount += individual_order['Amount']
                # potentialArrayOrderLog is updated with this new arrangement of orders
                    new_log_entry = {'Array of Orders': array_of_orders, \
                                     'Weighted Order List': weighted_order_list, \
                                     'Total Order Amount': total_order_amount}
                    potentialArrayOrderLog.append(new_log_entry)
                # amount_modifier is modified to find the perfect solution
                    if (total_order_amount < self.orderSettings['Amount'] * (1 - array_shape_lenience)) or \
                       (total_order_amount > self.orderSettings['Amount'] * (1 + array_shape_lenience)):
                        array_calculation_loop = True
                        #random_number = random.random()
                        #random_number = int(random_number * 20) + 10
                        if count % 30 == 0:
                            amount_modifier_modifier = amount_modifier_modifier * .9
                        if total_order_amount < self.orderSettings['Amount']:
                            amount_modifier += amount_modifier_modifier
                        else:
                            amount_modifier -= amount_modifier_modifier
                        if count % 100 == 0:
                            array_shape_lenience += .001
                        if amount_modifier_modifier == 0:
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            print('\n --- ARRAY ORDER CALCULATION FAILED! ---')
                            count = 50000
    ##                        amount_modifier = 1
    ##                        amount_modifier_modifier = .1
    ##                        array_shape_lenience = .005
    ##                        count = 0
    ##                        minimum_order_size = minimum_order_size + 1
    ##                        self.arrayOrderSettings['Minimum Order Size'] = minimum_order_size
    ##                        print('!!! WARNING !!! --- Minimum Order Size changed automatically to ' + str(minimum_order_size) + '!')
                        if count % 10000 == 0:
                            print('\nOE : Count:', count, '\nRatio:', total_order_amount / self.orderSettings['Amount'], '\nAmount Modifier:', amount_modifier, \
                                   '\nAmount Modifier Modifier:', amount_modifier_modifier, '\nArray Shape Lenience:', array_shape_lenience)
                        if count % 50000 == 0 or (count % 10000 == 0 and style == 'Multiplicative'):
                            print('\nOE : Count:', count, '\nRatio:', total_order_amount / self.orderSettings['Amount'], '\nAmount Modifier:', amount_modifier, \
                                   '\nAmount Modifier Modifier:', amount_modifier_modifier, '\nArray Shape Lenience:', array_shape_lenience)
                            print('OE : Count has reached ' + str(count) + ', so createArrayOrder is using its best guess from the potentialArrayOrderLog')
                            largest_total_amount_below_intended_amount = 0
                            for potential_array_order_arrangement in potentialArrayOrderLog:
                                if potential_array_order_arrangement['Total Order Amount'] <= self.orderSettings['Amount']:
                                    if potential_array_order_arrangement['Total Order Amount'] > largest_total_amount_below_intended_amount:
                                        largest_total_amount_below_intended_amount = potential_array_order_arrangement['Total Order Amount']
                                        array_of_orders = potential_array_order_arrangement['Array of Orders']
                                        weighted_order_list = potential_array_order_arrangement['Weighted Order List']
                                        total_order_amount = potential_array_order_arrangement['Total Order Amount']
                                        array_calculation_loop = False
                    else:
                        array_calculation_loop = False
                            
    ## These are further modifications for after the array order has been arranged
            total_order_amount_reduced = False
            total_order_amount_increased = False
        # If the total amount of the array order is greater than the intended amount, this reduces the last order's amount so the total matches the intended amount
            if total_order_amount > self.orderSettings['Amount']:
                extra_amount = total_order_amount - self.orderSettings['Amount']
                array_of_orders[len(array_of_orders) - 1]['Amount'] -= extra_amount
                del weighted_order_list[len(weighted_order_list) - 1]
                weighted_order_list.append(array_of_orders[len(array_of_orders) - 1]['Amount'] * array_of_orders[len(array_of_orders) - 1]['Price'])
                total_order_amount -= extra_amount
                total_order_amount_reduced = True
                print('OE : Ending order amount reduced by ' + str(extra_amount) + ' so the total order amount is equal to the intended order amount at ' + str(total_order_amount))
        # Increases the size of the final order if the total amount is less than the intended amount
            if total_order_amount < self.orderSettings['Amount']:
                missing_amount = self.orderSettings['Amount'] - total_order_amount
                array_of_orders[len(array_of_orders) - 1]['Amount'] += missing_amount
                del weighted_order_list[len(weighted_order_list) - 1]
                weighted_order_list.append(array_of_orders[len(array_of_orders) - 1]['Amount'] * array_of_orders[len(array_of_orders) - 1]['Price'])
                total_order_amount += missing_amount
                total_order_amount_increased = True
                print('OE : Ending order amount increased by ' + str(missing_amount) + ' so the total order amount equal to the intended order amount at ' + str(total_order_amount))
        #* This lets us know if the total order amount was both too small and too big, which should never happen
            if total_order_amount_reduced and total_order_amount_increased:
                print('OE : *******************************')
                print('OE : *******************************      WEIRD THING! The total_order_amount was both too small AND too big!')
                print('OE : *******************************')
            # If Quick Granularity is being used, this reduces the number of orders further from the starting price
            if quick_granularity_intensity and qg_start_percent and gq_end_percent:
                print('qg_start_percent', qg_start_percent)
                print('qg_end_percent', qg_end_percent)
                number_of_orders = len(array_of_orders)
                order_count = 0
                stored_amount = 0
                storage_duration = 0
                new_array_of_orders = []
                new_weighted_order_list = []
                if quick_granularity_intensity > 0:
                    if qg_start_percent == 'default':
                        qg_start_percent = 0
                    if qg_end_percent == 'default':
                        qg_end_percent = (1/3)
                if side == 'buy':
                    qg_start_price = price - (qg_start_percent * spread)
                    qg_end_price = price - (qg_end_percent * spread)
                else:
                    print('qg_start_percent', qg_start_percent)
                    qg_start_price = price + (qg_start_percent * spread)
                    qg_end_price = price + (qg_end_percent * spread)
                for individual_order in array_of_orders:
                    order_count += 1
                    if quick_granularity_intensity == 'Medium':
                        if qg_start_percent == 'default':
                            qg_start_percent = 0
                        if qg_end_percent == 'default':
                            qg_end_percent = .5
                    # Orders are collected & treated as normal when within the Quick Granularity range
                        if (order_count >= (number_of_orders * qg_start_percent)) and (order_count < (number_of_orders * qg_end_percent)):
                            new_array_of_orders.append(individual_order)
                            new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                        else:
                            if (storage_duration == 0) or (order_count == number_of_orders):
                                individual_order['Amount'] = individual_order['Amount'] + stored_amount
                                stored_amount = 0
                                storage_duration = 1
                                new_array_of_orders.append(individual_order)
                                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                            else:
                                storage_duration -= 1
                                stored_amount += individual_order['Amount']                            
                    elif quick_granularity_intensity == 'High':
                    # High intensity has no default settings for a start & end of Quick Granularity because it changes the granularity in both the middle & final thirds, instead
                    # of in just one section
                        if order_count > number_of_orders * (2/3):
                            if (storage_duration == 0) or (order_count == number_of_orders):
                                individual_order['Amount'] = individual_order['Amount'] + stored_amount
                                stored_amount = 0
                                storage_duration = 2
                                new_array_of_orders.append(individual_order)
                                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                            else:
                                storage_duration -= 1
                                stored_amount += individual_order['Amount']
                        elif order_count > number_of_orders * (1/3):
                            if storage_duration == 0:
                                individual_order['Amount'] = individual_order['Amount'] + stored_amount
                                stored_amount = 0
                                storage_duration = 1
                                new_array_of_orders.append(individual_order)
                                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                            else:
                                storage_duration -= 1
                                stored_amount += individual_order['Amount']
                        else:
                            new_array_of_orders.append(individual_order)
                            new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                    elif type(quick_granularity_intensity) == int:
                        # Orders are treated as normal when within the Quick Granularity range
                            #print(order_count, number_of_orders, qg_start_percent, qg_end_percent, number_of_orders * qg_start_percent, number_of_orders * qg_end_percent)
                            if (order_count >= (number_of_orders * qg_start_percent)) and (order_count < (number_of_orders * qg_end_percent)):
                                new_array_of_orders.append(individual_order)
                                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                            else:
                                if order_count == number_of_orders:
                                    ending_price = individual_order['Price']
                                    ending_amount = individual_order['Amount']
                                    new_array_of_orders[len(new_array_of_orders) - 1]['Price'] = individual_order['Price']
                                    new_array_of_orders[len(new_array_of_orders) - 1]['Amount'] += individual_order['Amount']
                                    new_array_of_orders[len(new_array_of_orders) - 1]['Amount'] += stored_amount
                                    new_weighted_order_list[len(new_weighted_order_list) - 1] = new_array_of_orders[len(new_array_of_orders) - 1]['Amount'] * \
                                                                                                new_array_of_orders[len(new_array_of_orders) - 1]['Price']
                                elif storage_duration == 0:
                                    individual_order['Amount'] += stored_amount
                                    stored_amount = 0
                                    storage_duration = quick_granularity_intensity
                                    new_array_of_orders.append(individual_order)
                                    new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
                                else:
                                    storage_duration -= 1
                                    stored_amount += individual_order['Amount']
                array_of_orders = new_array_of_orders
                weighted_order_list = new_weighted_order_list
                number_of_orders = len(array_of_orders)
                # Slow Granularity Multiplier is applied to increase the spread between orders that come after the Quick Granularity End %
                if side == 'buy':
                    slow_granularity_multiplier = 4
                else:
                    slow_granularity_multiplier = 3
                if slow_granularity_multiplier:
                    price_multiplier = slow_granularity_multiplier - 1
                    new_array_of_orders = []
                    new_weighted_order_list = []
                    order_count = 0
                    quick_granularity_order_count = 0
                    slow_granularity_spread = spread * (1 - qg_end_percent)
                    for order in array_of_orders:
                        order_count += 1
                        new_order = order
                        if new_order['Side'].lower() == 'buy':
                            if order['Price'] >= qg_end_price:
                                quick_granularity_order_count += 1
                            else:
                                percent_into_slow_granularity = (qg_end_price - order['Price']) / slow_granularity_spread
                                price_modification = price_multiplier * (percent_into_slow_granularity * slow_granularity_spread)
                                new_order['Price'] -= price_modification
                        elif new_order['Side'].lower() == 'sell':
                            if order['Price'] <= qg_end_price:
                                quick_granularity_order_count += 1
                            else:
                                percent_into_slow_granularity = (order['Price'] - qg_end_price) / slow_granularity_spread
                                price_modification = price_multiplier * (percent_into_slow_granularity * slow_granularity_spread)
                                new_order['Price'] += price_modification
                        new_array_of_orders.append(new_order)
                        new_weighted_order_list.append(new_order['Amount'] * new_order['Price'])
                array_of_orders = new_array_of_orders
                weighted_order_list = new_weighted_order_list
            try:
                # End Spread Multiplier is applied
                if end_spread_multiplier:
                    price_multiplier = end_spread_multiplier - 1
                    new_array_of_orders = []
                    new_weighted_order_list = []
                    order_count = 0
                    normal_spread_order_count = 0
    ##                    slow_granularity_spread = spread * (1 - qg_end_percent)
    ##                    print('slow_granularity_spread', slow_granularity_spread)
    ##                    print('qg_end_price', qg_end_price)
                    if side.lower() == 'buy':
                        end_spread_start_price = price - (end_spread_start_percent * spread)
                        end_spread_end_price = price - spread
                        end_spread = end_spread_start_price - end_spread_end_price
                        for order in array_of_orders:
                            order_count += 1
                            new_order = order
    ##                    print(order['Price'], order['Amount'])
                            if order['Price'] >= end_spread_start_price:
                                order_count += 1
                            else:
                                percent_into_end_spread = (end_spread_start_price - order['Price']) / end_spread
    ##                                print('percent_into_end_spread', percent_into_end_spread)
                                price_modification = price_multiplier * (percent_into_end_spread * end_spread)
                                new_order['Price'] -= price_modification
                            new_array_of_orders.append(new_order)
                            new_weighted_order_list.append(new_order['Amount'] * new_order['Price'])
                    elif side.lower() == 'sell':
                        end_spread_start_price = price + (end_spread_start_percent * spread)
                        end_spread_end_price = price + spread
                        end_spread = end_spread_end_price - end_spread_start_price
                        for order in array_of_orders:
                            order_count += 1
                            new_order = order
    ##                        print(order['Price'], order['Amount'])
                            if order['Price'] <= end_spread_start_price:
                                order_count += 1
                            else:
                                percent_into_end_spread = (order['Price'] - end_spread_start_price) / end_spread
    ##                                print('percent_into_end_spread', percent_into_end_spread)
                                price_modification = price_multiplier * (percent_into_end_spread * end_spread)
                                new_order['Price'] += price_modification
                            new_array_of_orders.append(new_order)
                            new_weighted_order_list.append(new_order['Amount'] * new_order['Price'])
                    array_of_orders = new_array_of_orders
                    weighted_order_list = new_weighted_order_list
            # This reorganizes the Array Order so that smaller orders are always closer to the begining of the array than the end
                new_array_of_orders = []
                new_weighted_order_list = []
                for order_index in range(len(array_of_orders)):
                    if order_index > 0:
                        if array_of_orders[order_index]['Amount'] < array_of_orders[order_index - 1]['Amount']:
                            larger_amount = array_of_orders[order_index - 1]['Amount']
                            array_of_orders[order_index - 1]['Amount'] = array_of_orders[order_index]['Amount']
                            array_of_orders[order_index]['Amount'] = larger_amount
            # If Maximum Amount is being used, this removes orders past a certain price point so the total amount of the array order is a specific amount
                if maximum_amount:
    ##                sum_of_order_amounts = 0
    ##                total_order_amount = 0
    ##                accumulate_orders = True
    ##                new_array_of_orders = []
    ##                new_weighted_order_list = []
    ##                for individual_order in array_of_orders:
    ##                    if accumulate_orders:
    ##                        sum_of_order_amounts += individual_order['Amount']
    ##                        if sum_of_order_amounts < maximum_amount:
    ##                            new_array_of_orders.append(individual_order)
    ##                            total_order_amount += individual_order['Amount']
    ##                            new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
    ##                        elif sum_of_order_amounts == maximum_amount:
    ##                            accumulate_orders = False
    ##                            new_array_of_orders.append(individual_order)
    ##                            total_order_amount += individual_order['Amount']
    ##                            new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
    ##                        elif sum_of_order_amounts > maximum_amount:
    ##                            accumulate_orders = False
    ##                            ending_order_modified = 1
    ##                            extra_amount = sum_of_order_amounts - maximum_amount
    ##                            individual_order['Amount'] -= extra_amount
    ##                            total_order_amount += individual_order['Amount']
    ##                            new_array_of_orders.append(individual_order)
    ##                            new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
    ##                array_of_orders = new_array_of_orders
    ##                weighted_order_list = new_weighted_order_list
    ##                number_of_orders = len(array_of_orders)
    ##                print('OE : Maximum Amount was applied and now the total order amount is ' + str(total_order_amount) + ' spread across ' + str(number_of_orders) + ' orders')
                    newArrayOrderInfo = self.applyMaximumAmount(array_of_orders, maximum_amount)
                    total_order_amount = newArrayOrderInfo['Total Order Amount']
                    number_of_orders = newArrayOrderInfo['Total Number of Orders']
                    array_of_orders = newArrayOrderInfo['Array of Orders']
                    weighted_order_list = newArrayOrderInfo['Weighted Order List']
                    effective_amount = maximum_amount
                # This will readjust the Maximum Amount so that the amounts of the orders that are on the wrong side of the current price and won't be executed
                # can be added to the Maximum Amount. This will make it so that the sum of the amount of orders that get placed is equal to the Maximum Amount
                    if readjust_to_execute_maximum_amount:
                        total_amount_too_small = True
                        last_sum_of_inexecutable_amounts = False
                        while total_amount_too_small:
                            sum_of_inexecutable_amounts = 0
                            if self.orderSettings['Side'] == 'buy':
                                for individual_order in array_of_orders:
                                    if individual_order['Price'] > self.current_price:
                                        sum_of_inexecutable_amounts += individual_order['Amount']
                            elif self.orderSettings['Side'] == 'sell':
                                for individual_order in array_of_orders:
                                    if individual_order['Price'] < self.current_price:
                                        sum_of_inexecutable_amounts += individual_order['Amount']
                            if sum_of_inexecutable_amounts > 0:
                                maximum_amount += sum_of_inexecutable_amounts
                                self.arrayOrderSettings['Maximum Amount'] = maximum_amount
                                newArrayOrderInfo = self.applyMaximumAmount(array_of_orders, maximum_amount)
                                total_order_amount = newArrayOrderInfo['Total Order Amount']
                                number_of_orders = newArrayOrderInfo['Total Number of Orders']
                                array_of_orders = newArrayOrderInfo['Array of Orders']
                                weighted_order_list = newArrayOrderInfo['Weighted Order List']
                                print('OE : Maximum Amount READJUSTED to ' + str(maximum_amount) + ' from ' + str(true_maximum_amount) + \
                                      ' because orders summing to ' + str(sum_of_inexecutable_amounts) + ' cannot to be placed because they are on the wrong side of the current price.')
            ##                else:
            ##                    total_amount_too_small = False
                            if sum_of_inexecutable_amounts == last_sum_of_inexecutable_amounts:
                                total_amount_too_small = False
                            last_sum_of_inexecutable_amounts = sum_of_inexecutable_amounts
            # Slope - this changes the slope of the array order. NOTE - This changes the amount of the array order!
                if slope:
                    new_weighted_order_list = []
                    new_total_order_amount = 0
                    for order in array_of_orders:
                        new_amount = int(slope * order['Amount'])
                        if new_amount < order['Amount']:
                            new_amount += 1
                        order['Amount'] = new_amount
                        new_total_order_amount += new_amount
                        new_weighted_order_list.append(new_amount * order['Price'])
                    weighted_order_list = new_weighted_order_list
                    total_order_amount = new_total_order_amount
        ## No settings changed past this point. Orders are saved, displayed & executed. No settings changed past this point
            # Assigns values to arrayOrderParameters dict
                self.arrayOrderParameters['Number of Orders'] = len(array_of_orders)
                self.arrayOrderParameters['Total Order Amount'] = total_order_amount
            # When a Maximum Amount is used, orders are created in reverse, so maximum_amount affects whether the lowest-priced order is at the start or end
                if (self.orderSettings['Side'] == 'sell' and not(maximum_amount)) or (self.orderSettings['Side'] == 'buy' and maximum_amount):
                    self.arrayOrderParameters['Lowest Price Order Amount'] = array_of_orders[0]['Amount']
                    self.arrayOrderParameters['Lowest Price Order Price'] = array_of_orders[0]['Price']
                    self.arrayOrderParameters['Highest Price Order Amount'] = array_of_orders[len(array_of_orders) - 1]['Amount']
                    self.arrayOrderParameters['Highest Price Order Price'] = array_of_orders[len(array_of_orders) - 1]['Price']
                elif (self.orderSettings['Side'] == 'buy' and not(maximum_amount)) or (self.orderSettings['Side'] == 'sell' and maximum_amount):
                    self.arrayOrderParameters['Lowest Price Order Amount'] = array_of_orders[len(array_of_orders) - 1]['Amount']
                    self.arrayOrderParameters['Lowest Price Order Price'] = array_of_orders[len(array_of_orders) - 1]['Price']
                    self.arrayOrderParameters['Highest Price Order Amount'] = array_of_orders[0]['Amount']
                    self.arrayOrderParameters['Highest Price Order Price'] = array_of_orders[0]['Price']
                self.arrayOrderParameters['Entry at Full Execution'] = sum(weighted_order_list) / total_order_amount
                self.arrayOrderParameters['Individual Order Settings'] = array_of_orders
                self.arrayOrderParameters['Effective Amount'] = effective_amount
                try:
                    self.arrayOrderParameters['Quick Granularity Start Price'] = qg_start_price
                    self.arrayOrderParameters['Quick Granularity End Price'] = qg_end_price
                except:
                    self.arrayOrderParameters['Quick Granularity Start Price'] = False
                    self.arrayOrderParameters['Quick Granularity End Price'] = False
            except Exception as error:
                self.CTE.inCaseOfError(**{'error': error, \
                                          'description': 'when belf becomes welf', \
                                          'program': 'OE', \
                                          'line_number': traceback.format_exc().split('line ')[1].split(',')[0], \
                                          'number_of_attempts': 1})
                belf = welf
        # Displays text describing current parameters
            print('\nOE : - Array Order Parameters -')
            for key in self.arrayOrderParameters:
                if key != 'Individual Order Settings':
                    print('        ' + str(key) + ': ' + str(self.arrayOrderParameters[key]))
            if total_order_amount_increased:
                print('        Extra Order Increased By: ' + str(int(missing_amount)))
            if total_order_amount_reduced:
                print('        Ending Order Reduced By: ' + str(int(extra_amount)))
            print('_________________________________________')
        # Saves current orders to CSV and makes a bar chart
            if pd:
                dataframe_of_orders = pd.DataFrame(array_of_orders, columns = ['Exchange', 'Symbol', 'Side', 'Amount', 'Order Type', 'Price'])
                dataframe_of_orders.to_csv('Array of Orders.csv')
                if not(args[0] == 'update_current_parameters') and not(args[0] == 'update_via_end_price'):
                    self.graphArrayOrders(array_of_orders)
        # Executes orders
            if not(args[0] == 'use_current_settings') and not(args[0] == 'update_current_parameters') and not(args[0] == 'update_via_end_price'):
                self.confirmation = input('\nAre you sure you want to execute these orders?\n(1) : Yes\n(2) : No\n\nInput : ')
                if (self.confirmation == '1') or (self.confirmation == 'yes') or (self.confirmation == 'Yes'):
                    self.confirmation = True
                else:
                    self.confirmation = False
                if self.confirmation:
                    self.executeArrayOrders(array_of_orders)

    def applyMaximumAmount(self, array_of_orders, maximum_amount):
        sum_of_order_amounts = 0
        total_order_amount = 0
        accumulate_orders = True
        new_array_of_orders = []
        new_weighted_order_list = []
        price_dict = {}
        for order in array_of_orders:
            price_dict[order['Price']] = order
            array_order_side = order['Side']
        while (accumulate_orders) and (len(price_dict) > 0):
            if array_order_side.lower() == 'buy':
                individual_order = price_dict[min(price_dict)]
                del price_dict[min(price_dict)]
            else:
                individual_order = price_dict[max(price_dict)]
                del price_dict[max(price_dict)]
            sum_of_order_amounts += individual_order['Amount']
            if sum_of_order_amounts < maximum_amount:
                new_array_of_orders.append(individual_order)
                total_order_amount += individual_order['Amount']
                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
            elif sum_of_order_amounts >= maximum_amount:
                accumulate_orders = False
                extra_amount = sum_of_order_amounts - maximum_amount
                individual_order['Amount'] -= extra_amount
                total_order_amount += individual_order['Amount']
                new_array_of_orders.append(individual_order)
                new_weighted_order_list.append(individual_order['Amount'] * individual_order['Price'])
        if accumulate_orders:
            print('OE : Strange occurence - the price_dict became empty before the Maximum Amount was reached!')
            self.AP.playSound('Tim Allen Huh')
        array_of_orders = new_array_of_orders
        weighted_order_list = new_weighted_order_list
        number_of_orders = len(array_of_orders)
        newArrayOrderInfo = {'Total Order Amount': total_order_amount, \
                             'Total Number of Orders': number_of_orders, \
                             'Array of Orders': array_of_orders, \
                             'Weighted Order List': weighted_order_list}
        print('OE : Maximum Amount was applied and now the total order amount is ' + str(total_order_amount) + ' spread across ' + str(number_of_orders) + ' orders')
        return(newArrayOrderInfo)
        

    def graphArrayOrders(self, array_of_orders):
        if pyplot:
            if pd:
                dataframe_of_orders = pd.DataFrame(array_of_orders, columns = ['Exchange', 'Symbol', 'Side', 'Amount', 'Order Type', 'Price'])
                order_index = 0
                entry_bar = -1
                list_of_prices = []
                # These for loops mark the entry position at full execution on the bar chart
                if self.orderSettings['Side'] == 'buy':
                    side_color = 'green'
                    for order in array_of_orders:
                        list_of_prices.append(order['Price'])
                        if order['Price'] < self.arrayOrderParameters['Entry at Full Execution']:
                            if entry_bar < 0:
                                entry_bar = order_index
                        order_index += 1        
                elif self.orderSettings['Side'] == 'sell':
                    side_color = 'red'
                    for order in array_of_orders:
                        list_of_prices.append(order['Price'])
                        if order['Price'] > self.arrayOrderParameters['Entry at Full Execution']:
                            if entry_bar < 0:
                                entry_bar = order_index
                        order_index += 1
                spread = max(list_of_prices) - min(list_of_prices)
                bar_width = spread / 100
                pyplot.clf()
                self.array_order_bar_chart = pyplot.bar(list_of_prices, list(dataframe_of_orders['Amount']), color=side_color, width=bar_width)
                self.array_order_bar_chart[entry_bar].set_color('blue')
                pyplot.ion()
                pyplot.show()
            else:
                print('OE : ERROR! Failed to plot Array Order because Pandas is not imported.')
        else:
            print('OE : ERROR! Failed to plot Array Order because Pyplot is not imported.')

    def createOrder(self, *args):
        if type(args[0]) == list:
            args = args[0]
        elif type(args[0]) == dict:
            args_list = []
            args_list.append(args[0]['Exchange'])
            args_list.append(args[0]['Symbol'])
            args_list.append(args[0]['Side'])
            args_list.append(args[0]['Amount'])
            args_list.append(args[0]['Order Type'])
            args_list.append(args[0]['Price'])
            try:
                args_list.append(args[0]['Attempt Execution'])
            except:
                shit = 'balls'
            args = args_list
    #arg 0 : exchange
        try:
            self.CTE.exchange = args[0]
            self.CTE.exchange.fetchTicker('BTC/USDT')
        except:
            try:
                exchange_name = args[0]
                self.CTE.exchange = self.CTE.connect(exchange_name)
                self.CTE.exchange.fetchTicker('BTC/USDT')
            except:
                exchange_name = input('\nWhich exchange would you like to use?\n(1) : Coinbase\n(2) : Binance\n\nExchange : ')
                if exchange_name == '1':
                    exchange_name = 'Coinbase'
                elif exchange_name == '2':
                    exchange_name = 'Binance'
                self.CTE.exchange = self.CTE.connect(exchange_name)
        self.orderSettings['Exchange'] = exchange_name
        self.orderSettings['Account'] = self.CTE.currentConnectionDetails['Account Name']
    #arg 1 : symbol
        try:
            symbol = args[1]
        except:
            symbol = input('\nWhat asset would you like to trade?\n(1) : BTC/USD (2) : ETH/USD\n\nAsset : ')
        if symbol == '1':
            symbol = 'BTC/USD'
        elif symbol == '2':
            symbol = 'ETH/USD'
        self.orderSettings['Symbol'] = symbol
    #arg 2 : side
        try:
            side = args[2]
        except:
            side = input('\nAre you buying or selling?\n(1) : Buy\n(2) : Sell\n\nSide: ')
        if side == '1':
            side = 'buy'
        elif side == '2':
            side = 'sell'
        self.orderSettings['Side'] = side
    #arg 3 : amount
        try:
            amount = float(args[3])
        except:
            amount = float(input('\nWhat amount are you trading?\nAmount: '))
        self.orderSettings['Amount'] = amount
    #arg 4: order_type
        try:
            order_type = args[4]
        except:
            order_type = input('\nIs this a Market or Limit order?\n(1) : Limit\n(2) : Market\n\nType: ')
        if order_type == '1':
            order_type = 'limit'
        elif order_type == '2':
            order_type = 'market'
        self.orderSettings['Order Type'] = order_type
    #arg 5 : price
        try:
            price = args[5]
        except:
            if order_type == 'limit':
                price = input('\nAt what price would you like to open this limit order?\nPrice: ')
            elif order_type == 'market':
                price = 'market'
        if price == 'margin':
            ticker_info = self.CTE.exchange.fetchTicker(symbol)
            if side == 'buy':
                price = ticker_info['bid']
            else:
                price = ticker_info['ask']
            print('Margin Price: ' + str(price))
        price = float(price)
        self.orderSettings['Price'] = price
    #Display Order
        print('\n_____________________________\n\n- Single Order Parameters -')
        for key in self.orderSettings:
            print('    ' + str(key) + ': ' + str(self.orderSettings[key]))
        print('_____________________________')
    #arg 6 : attempt_execution
        try:
            attempt_execution = args[6]
        except:
            attempt_execution = True
        if (attempt_execution == 'execute') or (attempt_execution == True) or (attempt_execution == 1):
            self.confirmation = input('\nAre you sure you want to execute this order?\n(1) : Yes\n(2) : No\n\nType: ')
            if (self.confirmation == '1') or (self.confirmation == 'yes') or (self.confirmation == 'Yes'):
                self.confirmation = True
            else:
                self.confirmation = False
            if self.confirmation:
                order = self.executeOrder(self.orderSettings)
                print(order)
                return([self.orderSettings, order])
            else:
                return([self.orderSettings, False])
        else:
            return([self.orderSettings, False])


    # This function creates triggerable market order for reducing or completely closing a position
    def createStopLossOrder(self, stop_price, symbol='BTCUSD', side='opposite_of_position', amount='current_position_size', position_dict=None, current_price=None):
        print('OE : Creating a Stop-Loss order at $' + str(stop_price))
        if side == 'opposite_of_position':
            if not(position_dict):
                position_dict = self.CTE.getPositions()
            if position_dict['Side'].lower() == 'buy':
                side = 'sell'
            else:
                side = 'buy'
        if not(current_price):
            current_price = self.CTE.fetchCurrentPrice(symbol)
        if stop_price >= current_price and side == 'sell':
            print('OE : Input ERROR! The stop_price $' + str(stop_price) + ' is greater than the current price of $' + str(current_price) + \
                  ', but the SIDE of the order is SELL! That makes it a TAKE PROFIT, not Stop-Loss!')
            order = None
        elif stop_price <= current_price and side == 'buy':
            print('OE : Input ERROR! The stop_price $' + str(stop_price) + ' is less than the current price of $' + str(current_price) + \
                  ', but the SIDE of the order is BUY! That makes it a TAKE PROFIT, not Stop-Loss!')
            order = None
        else:
            if amount == 'current_position_size':
                if not(position_dict):
                    position_dict = self.CTE.getPositions()
                amount = position_dict['Amount']
            order_settings_dict = {'Symbol': symbol, \
                                   'Order Type': 'market', \
                                   'Side': side, \
                                   'Amount': amount}
            params = {'ordType':'Stop', \
                      'triggerType':'ByLastPrice', \
                      'stopPrice': stop_price}
            order = self.executeOrder(order_settings_dict, params)
            print('OE : Stop-Loss order created!')
        if order:
            order = self.CTE.prettifyOrder(order)
        return(order)
            
            
            


    # This function creates a limit order that, when filled, will automatically have a Stop-Loss price to close the order
##    def createStopLimitOrder(self):
##    This function needs to be fleshed out. Below is the basic code
##    !!!!!! The below code to actually EXECUTE the order should be moved to executeOrder()
##        exchange.createOrder(symbol='BTCUSD', \
##                             type='limit', \
##                             side='buy', \
##                             amount=1, \
##                             price=63000, \
##                             params={'timeInForce':'PostOnly', 'stopLossEp': 610000000})


    def validateOrder(self, *args):
# This function still needs to be fleshed out
        if type(args[0]) == list:
            array_of_orders = args[0]
        elif len(args) > 1:
            array_of_orders = args
        else:
            order = args[0]
    # This function should now check to see if the current account & exchange has:
    #   -the correct symbol(s)
    #   -enough funds to put the order(s) in
        print('!!! WARNING !!! validateOrder has not been finished!')
        return(True)

    def executeArrayOrders(self, array_of_orders):
        order_count = 0
        new_active_orders = {}
        inactive_order_settings = []
        all_orders = []
        order_settings_by_ID = {}
        order_settings_by_price = {}
        total_amount = 0
        side = array_of_orders[0]['Side']
        order_count = 0
        for order_settings in array_of_orders:
            failed_to_post = False
            order_count += 1
            if order_count % 5 == 0:
                self.current_price = self.CTE.fetchCurrentPrice()
        # This price check eliminates the unnecessary posting of orders that are so far off-side they can't be executed
            if side == 'buy':
                if order_settings['Price'] > 1.01 * self.current_price:
                    failed_to_post = True
            elif side == 'sell':
                if order_settings['Price'] < .99 * self.current_price:
                    failed_to_post = True
        # This attempts to execute the order
            if not(failed_to_post):
                try:
                    order = self.executeOrder(order_settings)
                    if order['status'] == 'open':
                        new_active_orders[order['id']] = order
                    else:
                        inactive_order_settings.append(order_settings)
                    total_amount += float(order['amount'])
                    order_settings_by_ID[order['id']] = order_settings
                    order_settings_by_price[order['price']] = order_settings
                except:
                    print('!!!!!!!!!!!!     ERROR! Failed to post order:', order_settings)
                    failed_to_post = True
            if failed_to_post:
                inactive_order_settings.append(order_settings)
                order_settings_by_ID['FakeID_' + str(self.fake_ID_count)] = order_settings
                self.fake_ID_count += 1
        array_order_number = len(self.arrayOrderLedger) + 1
        self.arrayOrderLedger[array_order_number] = {}
        self.arrayOrderLedger[array_order_number]['Array Order Number'] = array_order_number
        self.arrayOrderLedger[array_order_number]['Order Settings'] = copy.deepcopy(self.orderSettings)
        self.arrayOrderLedger[array_order_number]['Array Order Settings'] = copy.deepcopy(self.arrayOrderSettings)
        self.arrayOrderLedger[array_order_number]['Array Order Parameters'] = copy.deepcopy(self.arrayOrderParameters)
        self.arrayOrderLedger[array_order_number]['Active Orders'] = new_active_orders
        #self.arrayOrderLedger[array_order_number]['Inactive Order Settings'] = inactive_order_settings
        self.arrayOrderLedger[array_order_number]['Order Settings by ID'] = order_settings_by_ID
        self.arrayOrderLedger[array_order_number]['Total Amount'] = total_amount
        self.arrayOrderLedger[array_order_number]['Lowest Price Order'] = order_settings_by_price[min(order_settings_by_price)]
        self.arrayOrderLedger[array_order_number]['Highest Price Order'] = order_settings_by_price[max(order_settings_by_price)]
        if side == 'buy':
            self.arrayOrderLedger[array_order_number]['Starting Price'] = self.arrayOrderLedger[array_order_number]['Highest Price Order']
            self.arrayOrderLedger[array_order_number]['Ending Price'] = self.arrayOrderLedger[array_order_number]['Lowest Price Order']
        else:
            self.arrayOrderLedger[array_order_number]['Starting Price'] = self.arrayOrderLedger[array_order_number]['Lowest Price Order']
            self.arrayOrderLedger[array_order_number]['Ending Price'] = self.arrayOrderLedger[array_order_number]['Highest Price Order']        
        self.arrayOrderHistory[array_order_number] = {'Inactive Orders': []}
        return(self.arrayOrderLedger[array_order_number])

    
    def executeOrder(self, order_settings_dict, params={}):
        params['timeInForce'] = 'PostOnly'
        # this `if` should be replaced with a more robust Contract vs. Spot feature
        
        if order_settings_dict['Symbol'] == 'BTC/USD':
            order_settings_dict['Symbol'] = 'BTCUSD'
        final_order_settings = {'symbol': order_settings_dict['Symbol'], \
                                'type': order_settings_dict['Order Type'], \
                                'side': order_settings_dict['Side'], \
                                'amount': order_settings_dict['Amount'], \
                                'params': params}
        if order_settings_dict.get('Price'):
            final_order_settings['price'] = order_settings_dict['Price']
        order = self.CTE.exchange.createOrder(**final_order_settings)
        self.confirmation = False
        return(order)

    def rebuildArrayOrder(self, *args):
        if type(args[0]) == int:
            array_order_number = args[0]
            #array_of_orders = self.arrayOrderLedger[array_order_number]['Active Orders']
        else:
            array_order_dict = args[0]
            #array_of_orders = array_order_dict['Active Orders']
            array_order_number = array_order_dict['Array Order Number']
        array_order_side = self.arrayOrderLedger[array_order_number]['Order Settings']['Side']
        array_order_exchange = self.arrayOrderLedger[array_order_number]['Order Settings']['Exchange']
        array_order_account = self.arrayOrderLedger[array_order_number]['Order Settings']['Account']
        array_order_symbol = self.arrayOrderLedger[array_order_number]['Order Settings']['Symbol']
    # This should connect CTE to the exchange of the order to be rebuilt in the case that it is not already connected to it
        original_exchange_name = False
        print('Current Exchange Name:', self.CTE.exchange_name, 'Current Exchange:', str(self.CTE.exchange), '\nArray Order Exchange:', array_order_exchange)
        if self.CTE.currentConnectionDetails['Account Name'] != array_order_account or self.CTE.currentConnectionDetails['Exchange Name'] != array_order_exchange:
            print('Original Exchange Name:', original_exchange_name)
            original_exchange_name = self.CTE.exchange_name
            self.CTE.connect(array_order_exchange + ' ' + array_order_account)
        try:
            quick_rebuild = args[1]['Quick Rebuild']
        except:
            quick_rebuild = False
        try:
            modified_entry_price = args[1]['Modified Entry Price']
        except:
            modified_entry_price = False
        try:
            current_price = args[1]['Current Price']
        except:
            current_price = self.CTE.exchange.fetchTicker(array_order_symbol)['bid']
        try:
            amount_multiplier = args[1]['Amount Multiplier']
        except:
            amount_multiplier = 1
        try:
            record_PNL = args[1]['Record PNL']
        except:
            record_PNL = False
    # Maximum Amount: this is the maximum total value of orders to rebuild
        try:
            max_amount = args[1]['Maximum Amount']
        except:
            max_amount = False

    # These 'new' variables will replace entries in the arrayOrderLedger to update them
        new_active_orders = {}
        new_inactive_order_settings = []
        new_order_settings_by_ID = {}
        new_total_amount = 0
        all_open_orders = self.CTE.fetchOpenOrders(symbol=array_order_symbol)
        open_order_IDs = []
        for order in all_open_orders:
            open_order_IDs.append(order['id'])
        orders_to_rebuild = {}
    # This checks to see if the order is already open by checking if its ID is in the list of IDs of open orders
        for ID in self.arrayOrderLedger[array_order_number]['Order Settings by ID']:
            order_settings = self.arrayOrderLedger[array_order_number]['Order Settings by ID'][ID]
            if ID in open_order_IDs:
                new_active_orders[ID] = self.arrayOrderLedger[array_order_number]['Active Orders'][ID]
                new_order_settings_by_ID[ID] = order_settings
                new_total_amount += order_settings['Amount']
            else:
            # If there is a modified entry price for Quick Rebuild, this will check if the order is within range
                order_within_range = False
                if not(modified_entry_price):
                    order_within_range = True
                else:
                    if order_settings['Side'].lower() == 'buy':
                        if order_settings['Price'] <= modified_entry_price:
                            order_within_range = True
                    elif order_settings['Side'].lower() == 'sell':
                        if order_settings['Price'] >= modified_entry_price:
                            order_within_range = True
            # This checks if the price is above your sell order/below your buy order, which would make it unexecutable
                if order_settings['Side'].lower() == 'buy':
                    if order_settings['Price'] > current_price:
                        order_within_range = False
                elif order_settings['Side'].lower() == 'sell':
                    if order_settings['Price'] < current_price:
                        order_within_range = False
                if order_within_range:
                    orders_to_rebuild[ID] = order_settings
                else:
                    new_inactive_order_settings.append(order_settings)
                    new_order_settings_by_ID[ID] = order_settings
        #orders_exist_in_a_row_count = 0
        #for order in array_of_orders:
    # A dict of prices is constructed to ensure orders are rebuilt starting with the most profitable and ending with the least
        price_dict = {}
        for ID in orders_to_rebuild:
            price_dict[orders_to_rebuild[ID]['Price']] = ID
    # This rebuilds the orders that are missing & within range
        if len(orders_to_rebuild) > 0:
            cease_rebuild = False
        else:
            cease_rebuild = True
        amount_rebuilt = 0
        while not(cease_rebuild) and (len(price_dict) > 0):
            if array_order_side.lower() == 'buy':
                ID = price_dict[min(price_dict)]
                del price_dict[min(price_dict)]
            else:
                ID = price_dict[max(price_dict)]
                del price_dict[max(price_dict)]
            order_settings = orders_to_rebuild[ID]
            if max_amount:
                if order_settings['Amount'] + amount_rebuilt >= max_amount:
                    if amount_rebuilt >= max_amount:
                        cease_rebuild = True
                        print('OE : Rebuild CEASED! Maximum Amount of ' + str(max_amount) + ' was reached at ' + str(order_settings['Price']))
                    else:
                        order_settings['Amount'] = max_amount - amount_rebuilt
                        print('OE : Rebuilding order at ' + str(order_settings['Price']) + ' with modified amount ' + str(order_settings['Amount']) + ' to fit within Maximum Amount.')
            if not(cease_rebuild):
                if record_PNL:
                    try:
                        order = self.CTE.exchange.fetchOrder(symbol=order_settings['Symbol'], id=ID)
                        if order['status'] == 'closed':
                            if order['filled'] > 0:
                                self.recordClosedOrder(order)
                    except:
                        print('OE : Failed to record PNL of order ' + ID + ' while rebuilding an array order')
                print('OE : Rebuilding ' + order_settings['Side'] + ' order for ' + str(order_settings['Amount']) + ' at $' + str(order_settings['Price']))
                new_order = False
                number_of_attempts = 0
                while not(new_order):
                    number_of_attempts += 1
                    try:
                        new_order = self.executeOrder(order_settings)
                        amount_rebuilt += order_settings['Amount']
                    except Exception as error:
                        self.CTE.inCaseOfError(**{'error': error, \
                                                  'description': 'rebuilding an array order', \
                                                  'program': 'OE', \
                                                  'line_number': traceback.format_exc().split('line ')[1].split(',')[0], \
                                                  'number_of_attempts': number_of_attempts})
                        new_order = False
                        if number_of_attempts > 0:
                            new_order = 'SKIP'
                            print('OE : Rebuild of order for ' + str(order_settings['Amount']) + ' SKIPPED due to ' + str(number_of_attempts) + ' failed attempts!')
                if new_order == 'SKIP':
                    new_order_settings_by_ID['FakeID_' + str(self.fake_ID_count)] = order_settings
                    self.fake_ID_count += 1
                else:
                    new_active_orders[new_order['id']] = new_order
                    new_order_settings_by_ID[new_order['id']] = order_settings
                    new_total_amount += new_order['amount']
            # Checks to see if all the orders have been rebuilt
                if len(price_dict) == 0:
                    cease_rebuild = True
        if not(cease_rebuild):
            print('OE : Strange rebuild occurence - the price_dict became empty before the Maximum Amount was reached!')
            self.AP.playSound('Tim Allen Huh')
    # These loops iterate through the new list of active orders to determine the new starting and end prices
        starting_price = False
        ending_price = False
        if array_order_side.lower() == 'buy':
            for ID in new_active_orders:
                order_settings = new_active_orders[ID]
                if not(starting_price):
                    starting_price = order_settings['price']
                if not(ending_price):
                    ending_price = order_settings['price']
                if order_settings['price'] >= starting_price:
                    starting_price = order_settings['price']
                if order_settings['price'] <= ending_price:
                    ending_price = order_settings['price']
        elif array_order_side.lower() == 'sell':
            for ID in new_active_orders:
                order_settings = new_active_orders[ID]
                if not(starting_price):
                    starting_price = order_settings['price']
                if not(ending_price):
                    ending_price = order_settings['price']
                if order_settings['price'] <= starting_price:
                    starting_price = order_settings['price']
                if order_settings['price'] >= ending_price:
                    ending_price = order_settings['price']
        self.arrayOrderLedger[array_order_number]['Active Orders'] = new_active_orders
        #self.arrayOrderLedger[array_order_number]['Inactive Order Settings'] = new_inactive_order_settings
        self.arrayOrderLedger[array_order_number]['Order Settings by ID'] = new_order_settings_by_ID
        self.arrayOrderLedger[array_order_number]['Total Amount'] = new_total_amount
        self.arrayOrderLedger[array_order_number]['Starting Price'] = starting_price
        self.arrayOrderLedger[array_order_number]['Ending Price'] = ending_price
        if original_exchange_name:
            self.CTE.connect(original_exchange_name)
        return({'Rebuilt Orders': new_active_orders, \
                'Amount Rebuilt': amount_rebuilt})
                
        

    def checkArrayOrder(self, *args):
        if type(args[0]) == int:
            array_order_number = args[0]
            array_of_orders = self.arrayOrderLedger[array_order_number]['Active Orders']
        else:
            array_of_orders == args[0]
        try:
            inductive_check = args[1]['Inductive Check']
        except:
            inductive_check = False
        try:
            return_missing_orders = args[1]['Return Missing Orders']
        except:
            return_missing_orders = False
        try:
            fetch_open_orders = args[1]['Fetch Open Orders']
        except:
            fetch_open_orders = False
        try:
            prefetched_open_orders = args[1]['Prefetched Open Orders']
        except:
            prefetched_open_orders = False
        symbol = self.arrayOrderLedger[array_order_number]['Order Settings']['Symbol']
    # Original checking method
        if not(inductive_check) and not(fetch_open_orders) and not(prefetched_open_orders):
            orders_to_check = []
        # The first order(s), last order(s), and midpoint orders are added to a list to check
            active_orders = []
         #First
            try:
                orders_to_check.append(array_of_orders[0])
            except:
                shit = 'balls'
            #orders_to_check.append(array_of_orders[1])
            #orders_to_check.append(array_of_orders[2])
            #orders_to_check.append(array_of_orders[3])
            try:
                orders_to_check.append(array_of_orders[4])
            except:
                shit = 'balls'
         #Last
            try:
                orders_to_check.append(array_of_orders[len(array_of_orders) - 1])
            except:
                shit = 'balls'
            #orders_to_check.append(array_of_orders[len(array_of_orders) - 2])
            try:
                orders_to_check.append(array_of_orders[len(array_of_orders) - 3])
            except:
                shit = 'balls'
            #orders_to_check.append(array_of_orders[len(array_of_orders) - 4])
            try:
                orders_to_check.append(array_of_orders[len(array_of_orders) - 5])
            except:
                shit = 'balls'
         #Midpoint
            midpoint = int(len(array_of_orders) / 2)
            try:
                orders_to_check.append(array_of_orders[midpoint])
            except:
                shit = 'balls'
        # Orders are checked
            for order in orders_to_check:
                try:
                    order = self.CTE.exchange.fetchOrder(symbol=order['symbol'], id=order['id'])
                    if order['status'] == 'open':
                        #new_array_of_orders.append(order)
                        active_orders.append(order)
                    else:
                        try:
                            self.arrayOrderHistory[array_order_number]['Inactive Orders'].append(order)
                        except:
                            try:
                                self.arrayOrderHistory[array_order_number]['Inactive Orders'] = []
                            except:
                                self.arrayOrderHistory[array_order_number] = {}
                    # This adds the PNL to the history if the missing order was closed
                        if (order['status'] == 'closed') and (order['filled'] > 0):
                            self.recordClosedOrder(order)
                except:
                    print('ERROR! Unable to check order ' + order['id'] + '! It does not appear to exist!')
                    print(orders_to_check)
            #self.arrayOrderLedger[array_order_number]['Active Orders'] = new_array_of_orders
            if len(active_orders) == 0:
                return(False)
            else:
                return(active_orders)
    # Inductive Check - it checks the first order, then the second, then the third, and if it ever misses 3 in a row, it stops (like Quick Rebuild)
        elif inductive_check:
            active_orders = []
            missing_orders = []
            orders_exist_in_a_row = 0
            for order in array_of_orders:
                try:
                    order = self.CTE.exchange.fetchOrder(symbol=order['symbol'], id=order['id'])
                    if order['status'] == 'open':
                        active_orders.append(order)
                        orders_exist_in_a_row += 1
                    else:
                        orders_exist_in_a_row = 0
                        missing_orders.append(order)
                        try:
                            self.arrayOrderHistory[array_order_number]['Inactive Orders'].append(order)
                        except:
                            try:
                                self.arrayOrderHistory[array_order_number]['Inactive Orders'] = []
                            except:
                                self.arrayOrderHistory[array_order_number] = {}
                    # This adds the PNL to the history if the missing order was closed
                        if (order['status'] == 'closed') and (order['filled'] > 0):
                            self.recordClosedOrder(order)
                except:
                    orders_exist_in_a_row = 0
                    missing_orders.append(order)
                    try:
                        print('ERROR! Unable to check order ' + order['id'] + '! It does not appear to exist!')
                        print(order)
                    except:
                        print('ERROR! Unable to check order! It does not appear to exist!')
            self.arrayOrderLedger[array_order_number]['Active Orders'] = active_orders
            if return_missing_orders:
                return(missing_orders)
            else:
                return(active_orders)
    # Fetch Open Orders Check - this fetches all the open orders with one call to the exchange via CCXT, making it very fast & thorough, but not able to record PNL of missing orders
        elif fetch_open_orders or prefetched_open_orders:
            array_order_side = self.arrayOrderLedger[array_order_number]['Order Settings']['Side']
            new_active_orders = {}
            new_total_amount = 0
            try:
                missing_orders = self.arrayOrderHistory[array_order_number]['Inactive Orders']
            except:
                missing_orders = []
            missing_order_IDs = []
            orders_to_check = self.arrayOrderLedger[array_order_number]['Active Orders']
            if prefetched_open_orders:
                all_open_orders = prefetched_open_orders
            else:
                all_open_orders = self.CTE.fetchOpenOrders(symbol=symbol)
            open_order_IDs = []
            for order in all_open_orders:
                open_order_IDs.append(order['id'])
            for ID in orders_to_check:
                if ID in open_order_IDs:
                    new_active_orders[ID] = orders_to_check[ID]
                    new_total_amount += orders_to_check[ID]['amount']
                else:
                    missing_orders.append(orders_to_check[ID])
                    missing_order_IDs.append(ID)
            #missing_order_settings = self.arrayOrderLedger[array_order_number]['Inactive Order Settings']
            #for order_ID in missing_order_IDs:
            #    missing_order_settings.append(self.arrayOrderLedger[array_order_number]['Order Settings by ID'][order_ID])
        # These loops iterate through the new list of active orders to determine the new starting and end prices
            starting_price = False
            ending_price = False
            if array_order_side.lower() == 'buy':
                for ID in new_active_orders:
                    order_settings = new_active_orders[ID]
                    if not(starting_price):
                        starting_price = order_settings['price']
                    if not(ending_price):
                        ending_price = order_settings['price']
                    if order_settings['price'] >= starting_price:
                        starting_price = order_settings['price']
                    if order_settings['price'] <= ending_price:
                        ending_price = order_settings['price']
            elif array_order_side.lower() == 'sell':
                for ID in new_active_orders:
                    order_settings = new_active_orders[ID]
                    if not(starting_price):
                        starting_price = order_settings['price']
                    if not(ending_price):
                        ending_price = order_settings['price']
                    if order_settings['price'] <= starting_price:
                        starting_price = order_settings['price']
                    if order_settings['price'] >= ending_price:
                        ending_price = order_settings['price']
        # arrayOrderLedger is updated
            self.arrayOrderLedger[array_order_number]['Active Orders'] = new_active_orders
            #self.arrayOrderLedger[array_order_number]['Inactive Order Settings'] = missing_order_settings
            self.arrayOrderLedger[array_order_number]['Starting Price'] = starting_price
            self.arrayOrderLedger[array_order_number]['Ending Price'] = ending_price
            self.arrayOrderLedger[array_order_number]['Total Amount'] = new_total_amount

            self.arrayOrderHistory[array_order_number]['Inactive Orders'] = missing_orders
            if return_missing_orders:
                return(missing_orders)
            else:
                return(new_active_orders)
            
                
            
        

    def cancelArrayOrder(self, *args):
        if type(args[0]) == int:
            array_order_number = args[0]
            array_of_orders = []
            for ID in self.arrayOrderLedger[array_order_number]['Active Orders']:
                array_of_orders.append(self.arrayOrderLedger[array_order_number]['Active Orders'][ID])
            if len(array_of_orders) > 0:
                print('OE : CANCELING ' + self.arrayOrderLedger[array_order_number]['Order Settings']['Side'] + ' Array Order #' + str(array_order_number) + \
                      ' starting at $' + str(array_of_orders[0]['price']) + ' and ending at $' + str(array_of_orders[len(array_of_orders) - 1]['price']))
            else:
                print('OE : FAILED to CANCEL Array Order #' + str(array_order_number) + ' because it is an empty list!')
        else:
            array_of_orders = args[0]
            if len(array_of_orders) > 0:
                print('OE : CANCELING ' + self.arrayOrderLedger[array_order_number]['Array Order Settings']['Side'] + ' Array Order starting at $' + \
                      str(array_of_orders[0]['price']) + ' and ending at $' + str(array_of_orders[len(array_of_orders) - 1]['price']))
            else:
                print('OE : FAILED to CANCEL Array Order because it is an empty list!')
        for order in array_of_orders:
            if order['symbol'] == 'BTC/USD':
                symbol = 'BTCUSD'
            try:
                order = self.CTE.exchange.cancelOrder(order['id'], symbol)
            except:
                #print('OE : Missing Order while canceling an array order: ' + str(order['id']))
                try:
                    order = self.CTE.exchange.fetchOrder(order['id'], symbol)
                # This adds the PNL to the history if the missing order was closed
                    if (order['status'] == 'closed') and (order['filled'] > 0):
                        self.recordClosedOrder(order)
                except:
                    try:
                        print('OE : ERROR! Failed to record missing order ' + str(order['id']))
                    except:
                        print('OE : ERROR! Failed to record missing order!')
            self.arrayOrderHistory[array_order_number]['Inactive Orders'].append(order)
##        try:
##            del self.arrayOrderLedger[array_order_number]
##        except:
##            print('----------- ERROR! Failed to delete order from arrayOrderLedger! ---------------')

    def cancelOrderGroup(self, group_parameters):
        print('\nOE : Canceling order group...................................')
        symbol = group_parameters['Symbol']
        try:
            lowest_cancel_price = group_parameters['Lowest Cancel Price']
            highest_cancel_price = group_parameters['Highest Cancel Price']
        except:
            lowest_cancel_price = False
            highest_cancel_price = False
        try:
            cancel_side = group_parameters['Side']
        except:
            cancel_side = False
        open_orders = False
        while not(open_orders):
            try:
                open_orders = self.CTE.fetchOpenOrders(symbol=symbol)
                if open_orders == []:
                    open_orders = 'empty list'
            except:
                open_orders = 'empty list'
        orders_to_cancel = []
        if open_orders != 'empty list':
            for order in open_orders:
                try:
                    if order['status'] == 'closed':
                        if order['filled'] > 0:
                            self.recordClosedOrder(order)
                    else:                
                    # This is for canceling orders within a certain price range
                        if lowest_cancel_price and highest_cancel_price:
                            if order['price'] >= lowest_cancel_price and order['price'] <= highest_cancel_price:
                                if cancel_side:
                                    if order['side'] == cancel_side:
                                        orders_to_cancel.append(order)
                                else:
                                    orders_to_cancel.append(order)
                    # This is if we're canceling every buy order or every sell order
                        elif cancel_side:
                            if order['side'] == cancel_side:
                                orders_to_cancel.append(order)
                    # This is if no group parameters were specified besides symbol
                        else:
                            orders_to_cancel.append(order)
                except:
                # The order must already be gone
                    shit = 'balls'
        # This actually cancels the orders
            for order in orders_to_cancel:  
                self.CTE.exchange.cancelOrder(order['id'], symbol)
            print('\nOE : Order group canceled!')
        return(orders_to_cancel)
        
            

    def recordClosedOrder(self, order):
        order_id = order['id']
        if not(order_id in self.tradeHistoryDict):
            closed_pnl = float(order['info']['closedPnlEv']) / 100000000
            self.tradeSessionDetails['Session Total PNL'] += closed_pnl
            trade_dict = {}
            trade_dict['Time'] = order['datetime']
            trade_dict['Order ID'] = order_id
            trade_dict['Account'] = self.CTE.currentConnectionDetails['Account Name']
            trade_dict['Symbol'] = order['symbol']
            trade_dict['Side'] = order['side']
            trade_dict['Amount'] = order['amount']
            trade_dict['Price'] = order['price']
            trade_dict['Closed PNL'] = closed_pnl
            self.tradeHistoryDict[order_id] = trade_dict
            self.tradeHistoryList.append(trade_dict)
            #print('Current Session PNL: ' + str(self.tradeSessionDetails['Session Total PNL']) + ' BTC')
        else:
            print('OE : ^*^ That order was already recorded!')

    def getOHLCVs(self, *args):
        try:
            self.CTE.exchange = args[0]
            self.CTE.exchange.fetchTicker('BTC/USDT')
        except:
            self.CTE.exchange = self.CTE.connect()
        try:
            symbol = args[1]
        except:
            symbol = input("\nWhich symbol's OHLCV would you like?\nSymbol : ")
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
        OHLCVs = self.CTE.exchange.fetchOHLCV(symbol, timeframe, limit=10)
        if pd:
            OHLCVs_dataframe = pd.DataFrame(OHLCVs, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        return(OHLCVs_dataframe)

# This will create the OperateExchange class in a non-local scope, making it more secure
if __name__ == "__main__":
    main()
