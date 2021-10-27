# This program is a cryptocurrency trading bot that profits by creating and modifying groups of orders
# Array Orders are groups of open limit orders on cryptocurrency exchanges, each with different volumes and prices
# Array Orders are calculated by OperateExchange

import pickle
import pathlib
import pandas as pd
import copy
import traceback

# AudioPlayer is an optional module for adding audio alerts, which trigger under certain circumstances
from AudioPlayer import AudioPlayer

# GetCurrentTime.py has functions for easily acquiring the current date or time separately or together, and other time functions
from GetCurrentTime import GetCurrentTime

# ConvertTimestamp is a handy tool for converting timestamp values to amounts of time measured in minutes/hours/etc.
from ConvertTimestamp import ConvertTimestamp

# OperateExchange is the program which this calculates the arrangements of the groups of orders created by ArrayOrderAutomator
from OperateExchange import OperateExchange

# This function will create the ArrayOrderAutomator class in a non-local scope, making it more secure
def main():
    AOA = ArrayOrderAutomator()
    AOA.main()
    del AOA

class ArrayOrderAutomator:
    def __init__(self):
        self.OE = OperateExchange()
        self.GCT = GetCurrentTime()
        self.CT = ConvertTimestamp()
        self.AP = AudioPlayer()
        self.automationSessionData = {'Start Time': '', \
                                      'Run Time': '', \
                                      'Error Log': [], \
                                      'Session Total PNL': ''}
        self.automationSettings = {'Account': 'Main', \
                                   'Symbol': 'BTC/USD', \
                                   'Number of Entry Orders': 90, \
                                                            #65, \
                                   'Exit Strategy': 'Profit at Entry', \
                                   # ^ This determines how the orders that close positions are calculated
                                   'Rebuild Strategy': 'No Rebuild', \
                                   # ^ This determines the amount of an entry order to rebuild that has been partly filled
                                   'Quick Granularity Strategy': False, \
                                   # ^ This determines if Quick Granularity is used and how it is used
                                   'Stop-Loss Strategy': 'Based on Entry Spread %', \
                                   # ^ This determines if stop-loss orders are used how their prices are calculated
                                   # The options are: 'Static %', 'Based on Entry Spread %'
                                   'Initial Starting Price': False, \
                                   'Starting Price Gap %': .0001, \
                                   # ^ This determines the small price gap between the position entry price and the first order in an exit Array Order
                                   'Entry Steepness': 2.1, \
                                   'Exit Steepness': 0, \
                                   'Entry Style': 'Linear', \
                                   'Exit Style': 'Linear', \
                                   'Quick Granularity Intensity': 1, \
                                   'Long Entry Spread %': .0215, \
                                   'Short Entry Spread %': .0215, \
                                   'Long Exit Spread %': .01, \
                                   'Short Exit Spread %': .01, \
                                   'Stop-Loss Spread %': .043, \
                                   'Stop-Loss Modifier %': .00200, \
                                   # 15% seem to be the max change possible in a very short period
                                   'Refresh Rate': 3, \
                                   'Long Shift Gap': 60, \
                                   'Short Shift Gap': 60, \
                                   'Long Entry Amount': 12000, \
                                   'Short Entry Amount': 11000, \
                                   'Exit Amount': 5, \
                                   #^ This could also be a % of the Long or Short Amount (side being determined by the side of the position)
                                   #maybe get rid of Exit Amount and just use 0 - always treat the side you're on differently from the other
                                   'Spread Adjustment Gap': .03, \
                                   # ^ This is the minimum % difference the current position amount and the spread need to recreate the order (Original & O+)
                                   'Exit Amount Adjustment Gap': .05, \
                                   # ^ This is the minimum % difference the total array order amount and the exit amount need to recreate the order (O+ & Profit at Midpoint)
                                   'Minimum Exit Spread': 70, \
                                   # ^ This is the smallest the spread can possibly be set to (Profit at Midpoint)
                                   'Modified Rebuild Gap': .001, \
                                   # ^ This is the a % gap implemented when exiting a position to prevent buying/selling right at the entry price, which hardly changes it
                                   # It could be a % of the current price instead
                                   'Midpoint Profit Modifier': .20, \
                                   # ^ This makes the exit spread slightly larger so more of the order is in profit (Profit at Midpoint)
                                   'Quick Granularity Spread %': .4, \
                                   # ^ This determines how broad the low-granularity section of an entry array order will be
                                   'Quick Granularity Adjustment Gap': None, \
                                   # ^ This is the minimum % the current_price needs to deviate from the Quick Granularity Start % and
                                   #   away from the Array Order Starting Price for an entry order to be shifted
                                   'Quick Granularity Berth': .020, \
                                   # ^ This is the percent of Quick Granularity orders that are placed on the inexecutable side of current_price in case the
                                   #   price starts to go our way
                                   'Quick Granularity Berth Adjustment Gap': .0125, \
                                   # ^ This is the minimum % the current_price needs to deviate from the Quick Granularity Start %  and
                                   #   towards the Array Order Starting Price for an entry order to be shifted
                                   'Slow Granularity Multiplier': 5, \
                                   # ^ The spread beyond the Quick Granularity % is multiplied by this number
                                   # Relief Orders are uniform Array Orders created on the wrong side of the position, reducing the risk of getting stuck in a trade
                                   # Relief Order % is the percentage amount of the current position size to be bought/sold on the wrong side
                                   # Relief Order Trigger Amount is the minimum position amount necessary to initiate the use of Relief Orders
                                   'Relief Order %': .075, \
                                   'Relief Trigger Amount': 0}
        self.activeArrayOrderNumbers = {'Long': '', \
                                        'Short': '', \
                                        'Long Relief': '', \
                                        'Short Relief': ''}
        self.stopLossOrder = ''
        self.openStopLossOrders = {'Open Orders': {}, \
                                   'Total Amount': 0}
        self.exitStrategies = {1: 'Original', \
                               2: 'Original+', \
                               3: 'Profit at Midpoint', \
                               4: 'Profit at Entry'}
        self.rebuildStrategies = {1: 'Aggressive', \
                                  2: 'No Rebuild', \
                                  3: 'Amount Missing'}
        self.currentPositionDict = {'Entry Price': 1, \
                                    'Side': '', \
                                    'Leverage': 1, \
                                    'Amount': 1, \
                                    'Liqudation Price': 1, \
                                    'Stop-Loss': 0, \
                                    'Raw Positions List': []}
        self.latestUpdateTimestamps = {'Current Price': '', \
                                       'Current Position': '', \
                                       'Stop-Loss Order': '', \
                                       'Active Orders': ''}
        self.marketsToCheck = ['DOGE/USD', 'ETH/USD', 'LTC/USD']
        self.main_loop = True
        self.exiting = False
        self.initial_orders_created = False
        self.settings_loaded_from_file = False
        self.order_created_this_loop = False
        self.testing = False
        self.automation_log = []
        self.updateAutomationLog()

    def main(self):
        try:
            while self.main_loop:
                print('AOA : Welcome to the ArrayOrderAutomator!')
            # Step 1 - Initiate automation loop
                input_valid = False
                accounts_file = open('accounts.txt', 'r')
                options_dict = {}
                for account in accounts_file:
                    account = account.split('\n')[0]
                    options_dict[str(len(options_dict) + 1)] = account
                options_dict[str(len(options_dict) + 1)] = 'choose'
                options_dict[str(len(options_dict) + 1)] = 'load'
                options_dict[str(len(options_dict) + 1)] = 'test'
                options_dict['0'] = 'quit'
                while not(input_valid) and self.main_loop:
                    for option in options_dict:
                        if options_dict[option] == 'choose':
                            print('(' + option + ') : Choose an initial starting price')
                        elif options_dict[option] == 'load':
                            print('(' + option + ') : Load initial settings from pickle file')
                        elif options_dict[option] == 'test':
                            print('(' + option + ') : Use test environment')
                        elif options_dict[option] != 'quit':
                            print('(' + option + ') : ' + options_dict[option] + ' Array Order Automation')       
                    print('(0) : Quit\n')
                    user_input = input('Input: ')
                    user_choice = options_dict.get(user_input)
                    if user_choice == 'choose':
                        starting_price_input = False
                        while not(starting_price_input):
                            starting_price_input = input('AOA : Input the price you would like to start at.\n' + \
                                                         '\nInitial Starting Price: $')
                            try:
                                starting_price_input = float(starting_price_input)
                            except:
                                print('AOA : Invalid initial starting price! Please try again. :)')
                                starting_price_input = False
                        self.automationSettings['Initial Starting Price'] = starting_price_input
                        print('AOA : Input accepted! Initial Starting Price set to $' + str(starting_price_input) + '\n')
                    elif user_choice == 'load':
                        print('AOA : Loading pickle file......................')
                        long_array_settings = pickle.load(open(str(pathlib.Path().absolute()) + '\\_ArrayOrderAutomator_Settings_Backup\\Long.pickle', 'rb'))
                        short_array_settings = pickle.load(open(str(pathlib.Path().absolute()) + '\\_ArrayOrderAutomator_Settings_Backup\\Short.pickle', 'rb'))
                        long_array_settings['Array Order Number'] = 1
                        short_array_settings['Array Order Number'] = 2
                        self.activeArrayOrderNumbers['Long'] = 1
                        self.activeArrayOrderNumbers['Short'] = 2
                        self.OE.arrayOrderLedger[1] = long_array_settings
                        self.OE.arrayOrderLedger[2] = short_array_settings
                        print('\nAOA : Pickle file loaded!')
                        self.settings_loaded_from_file = True
                    elif user_choice == 'test':
                        print('AOA : OK! Entering test environment...')
                        self.testing = True
                        self.main_loop = False
                        account_name = 'Main'
                    elif user_choice == 'quit':
                        self.main_loop = False
                        print('AOA : OK! Quitting...')
                        account_name = 'QUIT'
                    elif user_choice:
                        account_name = user_choice
                        input_valid = True
                    else:
                        print('AOA : Invalid input! Please try again.')
                        input_valid = False
                if not(account_name == 'QUIT'):                    
                    self.exchange = self.OE.CTE.connect('default', account_name)
                    self.automationSettings['Account'] = account_name
                    print('AOA : OK! Beginning the Array Order Automation Loop on ' + account_name + ' account')
                    self.orderAutomationLoop()
        except Exception as error:
            print('CRITICAL ERROR! ArrayOrderAutomator has crashed!')
            self.OE.CTE.inCaseOfError(**{'error': error, \
                                         'description': 'running ArrayOrderAutomator - CRITICAL error!', \
                                         'program': 'AOA', \
                                         'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
            self.AP.playSound('Kill Bill Siren')

    def orderAutomationLoop(self):
        self.automate_orders = True
        self.loop_count = 0
        self.automationSessionData['Start Time'] = self.GCT.getDateTimeString()
        self.automationSessionData['Start Timestamp'] = self.GCT.getTimeStamp()
        self.starting_balance = float(self.OE.CTE.getBalances()['Spot'][self.automationSettings['Symbol'].split('/')[0]]['total'])
        print('\n\n\n\nAOA : ***** Array Order Automation Loop START *****\n')
        print('\nAOA : Automation Start Time: ' + str(self.automationSessionData['Start Time']))
        print('\nAOA : Starting Balance: ' + str(self.starting_balance))
        print('\nAOA :     -Automation Settings-')
        for thing in self.automationSettings:
            print('            ' + thing + ': ' + str(self.automationSettings[thing]))
        run_time_seconds = 0
        last_second = int(self.automationSessionData['Start Timestamp'])
        refresh_count = 0
        # This cancels any orders that you have open (unless they are for a different cryptocurrency)
        use_cancel_all = True
        for symbol in self.marketsToCheck:
            if self.OE.CTE.fetchOpenOrders(symbol=symbol, pause_time=0, maximum_number_of_attempts=1, alert=False) != []:
                use_cancel_all = False
        if use_cancel_all:
            self.OE.CTE.exchange.cancel_all_orders()
        else:
            self.OE.derGroup({'Symbol': self.automationSettings['Symbol']})
        self.previousPositionDict = {'Amount': 0}
        self.currentPositionLog = {'Entry Amount Closed': 0, \
                                   'Exit Amount Closed': 0, \
                                   'Entry Amount Rebuilt': 0}
        self.initializing = True
        while self.automate_orders:
            current_second = int(self.GCT.getTimeStamp())
            if current_second != last_second:
                run_time_seconds = (current_second - int(self.automationSessionData['Start Timestamp']))
                last_second = current_second
                refresh_count += 1
##            # This displays the run time
##                if run_time_seconds % 5 == 0:
##                    self.displayRunTime(run_time_seconds)
            # This creates & updates orders
                if (refresh_count == self.automationSettings['Refresh Rate']) or (run_time_seconds <= self.automationSettings['Refresh Rate']) or self.testing:
                    refresh_count = 0
                    self.loop_count += 1
                    print('\nAOA : --- Order Refresh #' + str(self.loop_count) + ' ! ---')
        # 0: Variables are updated
                    if self.testing:
                        self.fetchTestInput()
                    else:
                        self.currentPrice = None
                        self.currentPositionDict = False
                        number_of_attempts = 0
                        while not(self.currentPrice) and not(self.currentPositionDict):
                            try:
                                number_of_attempts += 1
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                self.currentPositionDict = self.OE.CTE.getPositions()
                            except Exception as error:
                                self.OE.CTE.inCaseOfError(**{'error': error, \
                                                          'description': 'checking current price and position', \
                                                          'program': 'OE', \
                                                          'line_number': traceback.format_exc().split('line ')[1].split(',')[0], \
                                                          'pause_time': 5, \
                                                          'number_of_attempts': number_of_attempts})
                                self.currentPositionDict = False
                        if self.currentPositionDict['Amount'] < self.previousPositionDict['Amount']:
                            self.currentPositionLog['Exit Amount Closed'] += (self.previousPositionDict['Amount'] - self.currentPositionDict['Amount'])
                        else:
                            self.currentPositionLog['Entry Amount Closed'] += (self.currentPositionDict['Amount'] - self.previousPositionDict['Amount'])
                        if not(self.initializing):
                            self.updateActiveOrders()
                    self.order_created_this_loop = False
        # I: Initial Array Orders are Created
                    print('\nAOA : #1 - Initial Array Orders are Created')
                # Initial Long array order
                    print('\nAOA : Checking LONG Array Order...')
                    self.exitCheck()
                    if self.activeArrayOrderNumbers['Long'] == '':
                        if self.currentPositionDict['Amount'] > 0:
                            if self.exiting and self.currentPositionDict['Side'].lower() == 'sell':
                                print('\nAOA : No order found but we are in a short position! Creating LONG EXIT order at $' + str(self.OE.current_price))
                            else:
                                print('\nAOA : No order found! Creating LONG ENTRY order at $' + str(self.OE.current_price))
                        else:
                            print('\nAOA : No order found! Creating LONG ENTRY order at $' + str(self.OE.current_price))
                        self.createArrayOrder('buy')
                        self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                    self.currentPositionDict = self.OE.CTE.getPositions()
                # Initial Short array order
                    print('\nAOA : Checking SHORT Array Order...')
                    if self.activeArrayOrderNumbers['Short'] == '':
                        if self.currentPositionDict['Amount'] > 0:
                            if self.exiting and self.currentPositionDict['Side'].lower() == 'buy':
                                print('\nAOA : No order found but we are in a long position! Creating SHORT EXIT order at $' + str(self.OE.current_price))
                            else:
                                print('\nAOA : No order found! Creating SHORT ENTRY order at $' + str(self.OE.current_price))
                        else:
                            print('\nAOA : No order found! Creating SHORT ENTRY order at $' + str(self.OE.current_price))
                        self.createArrayOrder('sell')
                        self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                # Initial Array Orders are created from pickle file instead
                    if self.settings_loaded_from_file:
                        print('\nAOA : Array settings have been loaded from pickle file and are being rebuilt!')
                        self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Long'], {'Quick Rebuild': True, \
                                                                                         'Current Price': self.OE.current_price})
                        self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Short'], {'Quick Rebuild': True, \
                                                                                          'Current Price': self.OE.current_price})
                        print('\nAOA : Array orders from file are rebuilt!')
                        self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                    self.initial_orders_created = True
                    self.settings_loaded_from_file = False
                    if self.initializing:
                        self.initializing = False
#######################################################################################################
####    Reasons to cancel and recreate orders:
####        1. Long or Short Shift Gap
####            a. If the current_price is too far from the entry price of an ENTRY array order
####        2. Mode Change
####            a. If the mode changed from EXIT to ENTRY due to closing a position after being in exit mode
####            b. If the mode changed from ENTRY to EXIT due to the position amount being equal to or greater than the Exit Amount
####            c. If the mode changed from EXITing one side to EXITing the other due to closing a position after first being in exit mode on one side and then
####                   having a position amount equal to or greater than the exit amount on the other side
####        3. Quick Granularity
####            a. If the current_price moves out of the Quick Granularity Spread of an ENTRY array order and towards the entry price of the array order
####            b. If the current_price moves out of the Quick Granularity Spread of an ENTRY array order and away from the entry price of the array order
####        4. Position Amount
####            a. If the amount of the current EXIT array order is different from the current position amount by at least the Exit Amount Adjustment Gap percent
####        5. Price Beyond Order (possibly optional because of 4a)
####            a. If a LONG EXIT array order's lowest price is above current_price or a SHORT EXIT array order's highest price is below the current_price
####
#######################################################################################################
        # II: Entry/Exit Mode & Position Side are Checked & Updated
                    print('\nAOA : #2 - Entry/Exit Mode & Position Side are Checked & Updated')
                # This is for if we go from exiting to entering
                    print('\nAOA : Checking AMOUNT to see if we should switch mode...')
                    if self.currentPositionDict['Amount'] == 0:
                        if self.exiting == 'Long' and self.currentPositionDict['Side'].lower() != 'buy':
                            print('AOA : MODE SWITCH! The LONG position closed & we are leaving EXIT mode and switching to ENTRY.')
                            self.exiting = False
                            self.inCaseOfPositionClosed()
                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                            self.createArrayOrder('sell')
                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                            self.createArrayOrder('buy')
                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        elif self.exiting == 'Short' and self.currentPositionDict['Side'].lower() != 'sell':
                            print('AOA : MODE SWITCH! The SHORT position closed & we are leaving EXIT mode and switching to ENTRY.')
                            self.exiting = False
                            self.inCaseOfPositionClosed()
                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                            self.createArrayOrder('buy')
                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                            self.createArrayOrder('sell')
                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        else:
                            long_array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Order Settings']['Price']
                            short_array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Order Settings']['Price']
                            if (long_array_order_starting_price <= self.OE.current_price and \
                               long_array_order_starting_price >= self.OE.current_price - self.automationSettings['Short Shift Gap']) or \
                               (short_array_order_starting_price >= self.OE.current_price and \
                               short_array_order_starting_price <= self.OE.current_price - self.automationSettings['Short Shift Gap']):
                                shit = 'balls'
                            else:
                                print('AOA : Mode switch? The position amount is 0 and one of the orders is too far away, so they are being remade.')
                                self.exiting = False
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                    else:
                # This is for if we go from entering to exiting
                        if not(self.exiting):
                            if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                                if self.currentPositionDict['Side'].lower() == 'sell':
                                    print('AOA : MODE SWITCH! Leaving ENTRY mode and switching to EXIT SHORT position.')
                                    self.AP.playSound('Navi Hey Listen')
                                    self.exiting = 'Short'
                                    self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                    self.createArrayOrder('buy')
                                    self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                else:
                                    print('AOA : MODE SWITCH! Leaving ENTRY mode and switching to EXIT LONG position.')
                                    self.AP.playSound('Navi Hey Listen')
                                    self.exiting = 'Long'
                                    self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                    self.createArrayOrder('sell')
                                    self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                # This is for if we go from exiting one side to exiting the other
                        else:                            
                            print('\nAOA : Checking if the SIDE of our position switched...')
                            if (self.exiting == 'Long') and (self.currentPositionDict['Side'].lower() == 'sell'):
                                if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                                    self.exiting = 'Short'
                                    print('AOA : SIDE SWITCH!!! Long position was closed and now trying to EXIT SHORT position.')
                                else:
                                    self.exiting = False
                                    print('AOA : MODE SWITCH! The SHORT position closed & we are leaving EXIT mode and switching to ENTRY.')
                                self.AP.playSound('Navi Hey Listen')
                                self.inCaseOfPositionClosed()
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                            elif (self.exiting == 'Short') and (self.currentPositionDict['Side'].lower() == 'buy'):
                                if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                                    self.exiting = 'Long'
                                    print('AOA : SIDE SWITCH!!! Short position was closed and now trying to EXIT LONG position.')
                                else:
                                    self.exiting = False
                                    print('AOA : MODE SWITCH! The LONG position closed & we are leaving EXIT mode and switching to ENTRY.')
                                self.AP.playSound('Navi Hey Listen')
                                self.inCaseOfPositionClosed()
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
        # III: Stop-Loss Order is Created, Checked and Adjusted
                    print('\nAOA : #3 - Stop-Loss Order is Created, Checked and Adjusted')
                    if self.automationSettings['Stop-Loss Strategy']:
                        self.updateStopLoss()
        # IV: Long & Short Orders are Checked and Adjusted or Shifted
                    print('\nAOA : #4a - Long Orders are Checked & Adjusted or Shifted')
            # IVa: LONG - This rebuilds or shifts the buy order
                    if self.order_created_this_loop:
                        print('AOA : SKIPPING #4a because an order was already created this run through the loop!')
                    else:
                        if self.activeArrayOrderNumbers['Long'] != '':
                            array_order_parameters = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Array Order Parameters']
                            active_order_amount = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Total Amount']
                            array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Starting Price']
                            array_order_ending_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Ending Price']
                            active_array_order_starting_price = array_order_parameters['Highest Price Order Price']
                            intended_array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Order Settings']['Price']
                            array_order_spread = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Array Order Settings']['Spread']
                            calculated_spread = self.calculateSpread('buy', array_order_starting_price)
                            qg_start_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Array Order Parameters']['Quick Granularity Start Price']
                            print('active_array_order_starting_price', active_array_order_starting_price)
                            print('array_order_starting_price', array_order_starting_price)
                            print('intended_array_order_starting_price', intended_array_order_starting_price)
                        # This shifts the order if the price has moved too far
                            if self.currentPositionDict['Side'].lower() != 'buy' and \
                               (self.OE.current_price - self.automationSettings['Long Shift Gap'] > array_order_starting_price) and \
                               ((self.currentPositionDict['Entry Price'] - self.automationSettings['Long Shift Gap'] > array_order_starting_price) or \
                               (self.currentPositionDict['Entry Price'] == 0)):
                                print('\nAOA : Shifting LONG order because the current price $' + str(self.OE.current_price) + ' is more than ' + \
                                      str(self.automationSettings['Long Shift Gap']) + \
                                      ' away from the array order entry price $' + str(array_order_starting_price))
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # This adjusts the order if in a SHORT position & the exit spread is too big for the position size
                            elif (self.automationSettings['Exit Strategy'] == 'Original' or self.automationSettings['Exit Strategy'] == 'Original+') and \
                                 self.exiting == 'Short' and self.currentPositionDict['Side'].lower() == 'sell' and \
                                 (array_order_spread > (1 + self.automationSettings['Spread Adjustment Gap']) * calculated_spread):
                                print('\nAOA : Adjusting LONG order because the current exit spread is too big for the SHORT position size.')
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
##                        # This adjusts the Quick Granularity Intensity if the current price is encroaching on the lower-granularity sections of the order
##                            elif array_order_starting_price - self.OE.current_price >= .35 * array_order_spread and \
##                                 (self.automationSettings['Exit Strategy'] == 'Original' or self.automationSettings['Exit Strategy'] == 'Original+' or \
##                                  (self.automationSettings['Exit Strategy'] == 'Profit at Midpoint' and self.currentPositionDict['Side'].lower() == 'buy')):
##                                print('\nAOA : Adjusting LONG order because the current price is encroaching on the lower-granularity sections of the order.')
##                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
##                                self.createArrayOrder('buy')
##                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # Order is remade if the current_price is moving down and away from the Quick Granularity Starting Price
                            elif not(self.exiting == 'Short') and self.automationSettings['Quick Granularity Strategy'] and \
                                 self.OE.current_price <= qg_start_price - (array_order_spread * self.automationSettings['Quick Granularity Adjustment Gap']):
                                print('\nAOA : Adjusting LONG order because the current price $' + str(self.OE.current_price) + ' has moved down to be over ' + \
                                      str(100 * self.automationSettings['Quick Granularity Adjustment Gap']) + '% away from the Quick Granularity Starting Price $' + \
                                      str(qg_start_price) + ' (Gap)')
                                self.AP.playSound('Navi Hey Listen')
                                quick_granularity_spread_dict = self.calculateQuickGranularitySpread('buy', array_order_spread, \
                                                                                                     array_order_starting_price, intended_array_order_starting_price)
                                self.modifyArrayOrder('buy', quick_granularity_spread_dict)
                        # Order is remade if the current_price is moving up towards the Quick Granularity Starting Price
                            elif not(self.exiting == 'Short') and self.automationSettings['Quick Granularity Strategy'] and \
                                 not(self.automationSettings['Rebuild Strategy'] == 'No Rebuild') and (qg_start_price < active_array_order_starting_price) and \
                                   (self.OE.current_price > qg_start_price - (array_order_spread * self.automationSettings['Quick Granularity Berth Adjustment Gap'])):
                                print('\nAOA : Adjusting LONG order because the current price $' + str(self.OE.current_price) + ' has moved up to be within ' + \
                                      str(self.automationSettings['Quick Granularity Berth Adjustment Gap']) + '% of the Quick Granularity Starting Price $' + \
                                      str(qg_start_price) + ' (Berth)')
                                self.AP.playSound('Navi Hey Listen')
                                quick_granularity_spread_dict = self.calculateQuickGranularitySpread('buy', array_order_spread, \
                                                                                                     active_array_order_starting_price, intended_array_order_starting_price)
                                self.modifyArrayOrder('buy', quick_granularity_spread_dict)
                        # This adjusts the exit amount if it's more or less than the current position size
                            elif (self.automationSettings['Exit Strategy'] == 'Original+') or (self.exiting == 'Short' and self.currentPositionDict['Side'].lower() == 'sell' and \
                                   (self.automationSettings['Exit Strategy'] == 'Profit at Midpoint' or self.automationSettings['Exit Strategy'] == 'Profit at Entry')) and \
                                   active_order_amount != self.currentPositionDict['Amount']:
                                    if self.currentPositionDict['Amount'] <= self.automationSettings['Exit Amount']:
                                        print('\nAOA : Adjusting LONG order because the current amount of active orders, ' + str(active_order_amount) + \
                                              ', is not equal to our position size ' + str(self.currentPositionDict['Amount']))
                                        self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                        self.createArrayOrder('buy')
                                        self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                    else:
                                        if self.currentPositionDict['Amount'] > active_order_amount * (1 + self.automationSettings['Exit Amount Adjustment Gap']):
                                            print('\nAOA : Adjusting LONG array order because its current total amount ' + str(active_order_amount) + ' is ' + \
                                                  str(self.automationSettings['Exit Amount Adjustment Gap'] * 100) + '% less than our position size ' + str(self.currentPositionDict['Amount']))
                                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                            self.createArrayOrder('buy')
                                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                        elif self.currentPositionDict['Amount'] < active_order_amount * (1 - self.automationSettings['Exit Amount Adjustment Gap']):
                                            print('\nAOA : Adjusting LONG array order because its current total amount ' + str(active_order_amount) + ' is ' + \
                                                  str(self.automationSettings['Exit Amount Adjustment Gap'] * 100) + '% greater than our position size ' + str(self.currentPositionDict['Amount']))
                                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                            self.createArrayOrder('buy')
                                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # This adjusts the order if its current end price is too high to even be executed
                            elif (self.OE.current_price < array_order_ending_price) and self.currentPositionDict['Side'].lower() == 'sell':
                                print('\nAOA : Adjusting LONG array order because the current price ' + str(self.OE.current_price) + \
                                      ' is lower than our lowest order at ' + str(array_order_ending_price))
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
                                self.createArrayOrder('buy')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # No special conditions were met, so this rebuilds the order
                            elif self.automationSettings['Rebuild Strategy'] != 'No Rebuild':
                                print('\nAOA : No special conditions met! Rebuilding LONG Array Order...')
                                rebuild_info_dict['Amount Rebuilt'] = 0
                            # This Modified Rebuild will rebuild only the orders below the long position entry price
                                if self.currentPositionDict['Side'].lower() == 'buy':
                                    modified_entry_price = self.currentPositionDict['Entry Price']
                                    if self.OE.current_price > self.currentPositionDict['Entry Price']:
                                        print('AOA : Implementing Modified Rebuild because the current price $' + str(self.OE.current_price) + ' is greater than our entry price $' + \
                                              str(self.currentPositionDict['Entry Price']))
                                        if self.exiting == 'Long':
                                            modified_entry_price = modified_entry_price * (1 - self.automationSettings['Modified Rebuild Gap'])
                                            print('AOA : Modified Rebuild starting at $' + str(modified_entry_price) + ' so that it starts ' + \
                                                  str(self.automationSettings['Modified Rebuild Gap'] * 100) + '% lower than our current position entry price $' + \
                                                  str(self.currentPositionDict['Entry Price']))
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Long'], {'Quick Rebuild': True, \
                                                                                                         'Modified Entry Price': modified_entry_price, \
                                                                                                         'Current Price': self.OE.current_price})
                                    elif self.exiting == 'Long':
                                        modified_entry_price = modified_entry_price * (1 - self.automationSettings['Modified Rebuild Gap'])
                                        print('AOA : Modified Rebuild starting at $' + str(modified_entry_price) + ' so that it starts ' + \
                                                  str(self.automationSettings['Modified Rebuild Gap'] * 100) + '% lower than our current position entry price $' + \
                                                  str(self.currentPositionDict['Entry Price']))
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Long'], {'Quick Rebuild': True, \
                                                                                                         'Modified Entry Price': modified_entry_price, \
                                                                                                         'Current Price': self.OE.current_price})
                            # These simply rebuild the order
                                    else:  
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Long'], {'Quick Rebuild': True, \
                                                                                                         'Current Price': self.OE.current_price})
                                else:  
                                    rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Long'], {'Quick Rebuild': True, \
                                                                                                     'Current Price': self.OE.current_price})
                          # # Variables are updated so that they are accurate for the Short Order check
                                self.currentPositionLog['Entry Amount Rebuilt'] += rebuild_info_dict['Amount Rebuilt']
                                self.currentPositionDict = self.OE.CTE.getPositions()
                                self.updateActiveOrders()
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
            # IVb: SHORT - This rebuilds or shifts the sell order
                    print('\nAOA : #4b - Short Orders are Checked & Adjusted or Shifted')
                    if self.order_created_this_loop:
                        print('AOA : SKIPPING #4b because an order was already created this run through the loop!')
                    else:
                        if self.activeArrayOrderNumbers['Short'] != '':
                            array_order_parameters = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Array Order Parameters']
                            active_order_amount = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Total Amount']
                            array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Starting Price']
                            array_order_ending_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Ending Price']
                            active_array_order_starting_price = array_order_parameters['Lowest Price Order Price']
                            intended_array_order_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Order Settings']['Price']
                            array_order_spread = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Array Order Settings']['Spread']
                            calculated_spread = self.calculateSpread('sell', array_order_starting_price)
                            qg_start_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Array Order Parameters']['Quick Granularity Start Price']
                            print('active_array_order_starting_price', active_array_order_starting_price)
                            print('array_order_starting_price', array_order_starting_price)
                            print('intended_array_order_starting_price', intended_array_order_starting_price)
                        # This shifts the order if the price has moved too far
                            if self.currentPositionDict['Side'].lower() != 'sell' and \
                               (self.OE.current_price + self.automationSettings['Short Shift Gap'] < array_order_starting_price) and \
                               ((self.currentPositionDict['Entry Price'] + self.automationSettings['Short Shift Gap'] < array_order_starting_price) or \
                               (self.currentPositionDict['Entry Price'] == 0)):
                                print('\nAOA : Shifting SHORT order because the current price $' + str(self.OE.current_price) + ' is more than ' \
                                      + str(self.automationSettings['Short Shift Gap']) + \
                                      ' away from the array order entry price $' + str(array_order_starting_price))
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # This adjusts the order if in a LONG position & the exit spread is too big for the position size
                            elif (self.automationSettings['Exit Strategy'] == 'Original' or self.automationSettings['Exit Strategy'] == 'Original+') and \
                                 self.exiting == 'Long' and self.currentPositionDict['Side'].lower() == 'buy' and \
                                 (array_order_spread > (1 + self.automationSettings['Spread Adjustment Gap']) * calculated_spread):
                                print('\nAOA : Adjusting SHORT order because the current exit spread is too big for the LONG position size.')
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
##                        # This adjusts the Quick Granularity Intensity if the current price is encroaching on the lower-granularity sections of the order
##                            elif array_order_starting_price - self.OE.current_price >= .35 * array_order_spread and \
##                                 (self.automationSettings['Exit Strategy'] == 'Original' or self.automationSettings['Exit Strategy'] == 'Original+' or \
##                                  (self.automationSettings['Exit Strategy'] == 'Profit at Midpoint' and self.currentPositionDict['Side'].lower() == 'sell')):
##                                print('\nAOA : Adjusting SHORT order because the current price is encroaching on the lower-granularity sections of the order.')
##                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
##                                self.createArrayOrder('sell')
##                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # Order is remade if the current_price is moving up and away from the Quick Granularity Starting Price
                            elif not(self.exiting == 'Long') and self.automationSettings['Quick Granularity Strategy'] and \
                                 self.OE.current_price >= qg_start_price + (array_order_spread * self.automationSettings['Quick Granularity Adjustment Gap']):
                                print('\nAOA : Adjusting SHORT order because the current price $' + str(self.OE.current_price) + ' has moved up to be over ' + \
                                      str(100 * self.automationSettings['Quick Granularity Adjustment Gap']) + '% away from the Quick Granularity Starting Price $' + \
                                      str(qg_start_price) + ' (Gap)')
                                self.AP.playSound('Navi Hey Listen')
                                quick_granularity_spread_dict = self.calculateQuickGranularitySpread('sell', array_order_spread, \
                                                                                                     array_order_starting_price, intended_array_order_starting_price)
                                self.modifyArrayOrder('sell', quick_granularity_spread_dict)
                        # Order is remade if the current_price is moving down towards the Quick Granularity Starting Price
                            elif not(self.exiting == 'Long') and self.automationSettings['Quick Granularity Strategy'] and \
                                 not(self.automationSettings['Rebuild Strategy'] == 'No Rebuild') and (qg_start_price > active_array_order_starting_price) and \
                                   (self.OE.current_price < qg_start_price + (array_order_spread * self.automationSettings['Quick Granularity Berth Adjustment Gap'])):
                                print('\nAOA : Adjusting SHORT order because the current price $' + str(self.OE.current_price) + ' has moved down to be within ' + \
                                      str(100 * self.automationSettings['Quick Granularity Berth Adjustment Gap']) + '% of the Quick Granularity Starting Price $' + \
                                      str(qg_start_price) + ' (Berth)')
                                self.AP.playSound('Navi Hey Listen')
                                quick_granularity_spread_dict = self.calculateQuickGranularitySpread('sell', array_order_spread, \
                                                                                                     active_array_order_starting_price, intended_array_order_starting_price)
                                self.modifyArrayOrder('sell', quick_granularity_spread_dict)
                        # This adjusts the exit amount if it's more or less than the current position size
                            elif (self.automationSettings['Exit Strategy'] == 'Original+') or (self.exiting == 'Long' and self.currentPositionDict['Side'].lower() == 'buy' and \
                                   (self.automationSettings['Exit Strategy'] == 'Profit at Midpoint' or self.automationSettings['Exit Strategy'] == 'Profit at Entry')) and \
                                   active_order_amount != self.currentPositionDict['Amount']:
                                    if self.currentPositionDict['Amount'] <= self.automationSettings['Exit Amount']:
                                        print('\nAOA : Adjusting SHORT order because the current amount of active orders, ' + str(active_order_amount) + \
                                              ', is not equal to our position size ' + str(self.currentPositionDict['Amount']))
                                        self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                        self.createArrayOrder('sell')
                                        self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                    else:
                                        if self.currentPositionDict['Amount'] > active_order_amount * (1 + self.automationSettings['Exit Amount Adjustment Gap']):
                                            print('\nAOA : Adjusting SHORT array order because its current total amount ' + str(active_order_amount) + ' is ' + \
                                                  str(self.automationSettings['Exit Amount Adjustment Gap'] * 100) + '% less than our position size ' + str(self.currentPositionDict['Amount']))
                                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                            self.createArrayOrder('sell')
                                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                                        elif self.currentPositionDict['Amount'] < active_order_amount * (1 - self.automationSettings['Exit Amount Adjustment Gap']):
                                            print('\nAOA : Adjusting SHORT array order because its current total amount ' + str(active_order_amount) + ' is ' + \
                                                  str(self.automationSettings['Exit Amount Adjustment Gap'] * 100) + '% greater than our position size ' + str(self.currentPositionDict['Amount']))
                                            self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                            self.createArrayOrder('sell')
                                            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # This adjusts the order if its current end price is too high to even be executed
                            elif (self.OE.current_price > array_order_ending_price) and self.currentPositionDict['Side'].lower() == 'buy':
                                print('\nAOA : Adjusting SHORT array order because the current price ' + str(self.OE.current_price) + \
                                      ' is higher than our highest order at ' + str(array_order_ending_price))
                                self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
                                self.createArrayOrder('sell')
                                self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                        # No special conditions were met, so this rebuilds the order
                            elif self.automationSettings['Rebuild Strategy'] != 'No Rebuild':
                                print('\nAOA : No special conditions met! Rebuilding SHORT Array Order...')
                                rebuild_info_dict['Amount Rebuilt'] = 0
                            # This Modified Rebuild will rebuild only the orders below the long position entry price
                                if self.currentPositionDict['Side'].lower() == 'sell':
                                    modified_entry_price = self.currentPositionDict['Entry Price']
                                    if self.OE.current_price < self.currentPositionDict['Entry Price']:
                                        print('AOA : Implementing Modified Rebuild because the current price $' + str(self.OE.current_price) + ' is less than our entry price $' + \
                                              str(self.currentPositionDict['Entry Price']))
                                        if self.exiting == 'Short':
                                            modified_entry_price = modified_entry_price * (1 + self.automationSettings['Modified Rebuild Gap'])
                                            print('AOA : Modified Rebuild starting at $' + str(modified_entry_price) + ' so that it starts ' + \
                                                  str(self.automationSettings['Modified Rebuild Gap'] * 100) + '% higher than our current position entry price $' + \
                                                  str(self.currentPositionDict['Entry Price']))
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Short'], {'Quick Rebuild': True, \
                                                                                                          'Modified Entry Price': modified_entry_price, \
                                                                                                          'Current Price': self.OE.current_price})
                                    elif self.exiting == 'Short':
                                        modified_entry_price = modified_entry_price * (1 + self.automationSettings['Modified Rebuild Gap'])
                                        print('AOA : Modified Rebuild starting at $' + str(modified_entry_price) + ' so that it starts ' + \
                                                  str(self.automationSettings['Modified Rebuild Gap'] * 100) + '% higher than our current position entry price $' + \
                                                  str(self.currentPositionDict['Entry Price']))
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Short'], {'Quick Rebuild': True, \
                                                                                                          'Modified Entry Price': modified_entry_price, \
                                                                                                          'Current Price': self.OE.current_price})
                            # These simply rebuild the order
                                    else:  
                                        rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Short'], {'Quick Rebuild': True, \
                                                                                                                              'Current Price': self.OE.current_price})
                                else:  
                                    rebuild_info_dict = self.OE.rebuildArrayOrder(self.activeArrayOrderNumbers['Short'], {'Quick Rebuild': True, \
                                                                                                                          'Current Price': self.OE.current_price})
                                self.currentPositionLog['Entry Amount Rebuilt'] += rebuild_info_dict['Amount Rebuilt']
        # V. Position & PNL is Displayed, dicts are Updated, and CSVs are Exported
                    print('\nAOA : #5 - Position & PNL are Displayed, dicts are Updated, and CSVs are Exported')
                # This displays our current position & saves the trade history
                    if self.exiting == 'Long':
                        self.updateActiveOrders()
                        print('AOA : ---------------- These two numbers should be the same:')
                        print('AOA : ----------------     currentPositionDict Amount:    ' + str(self.currentPositionDict['Amount']))
                        #print('AOA : ----------------     arrayOrderLedger Total Amount: ' + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Total Amount']))
                        try:
                            print('AOA : ----------------     arrayOrderLedger Total Amount: ' + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Total Amount']))
                        except Exception as error:
                            print('Error on line 695:', error)                            
                    elif self.exiting == 'Short':
                        self.updateActiveOrders()
                        print('AOA : ---------------- These two numbers should be the same:')
                        print('AOA : ----------------     currentPositionDict Amount:    ' + str(self.currentPositionDict['Amount']))
                        #print('AOA : ----------------     arrayOrderLedger Total Amount: ' + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Total Amount']))
                        try:
                            print('AOA : ----------------     arrayOrderLedger Total Amount: ' + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Total Amount']))
                        except Exception as error:
                            print('Error on line 695:', error)
                    session_PNL = self.OE.CTE.getBalances()['Spot'][self.automationSettings['Symbol'].split('/')[0]]['total'] - self.starting_balance
                    session_PNL_in_USD = round(self.OE.current_price * session_PNL, 2)
                    self.automationSessionData['Session Total PNL'] = session_PNL
                    print('\nAOA : *$*$*$*$*$*     Current Session PNL: ' + str('{0:.8f}'.format(session_PNL)) + ' BTC    *$*$*$*$*$*')
                    print('AOA : *$*$*$*$*$*     Current Session PNL: $' + str(session_PNL_in_USD) + '             *$*$*$*$*$*\n')
                    run_time = self.displayRunTime(run_time_seconds)
                # Saves current settings so automation can continue after a crash
                    if self.activeArrayOrderNumbers['Long'] != '':
                        pickle.dump(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']], \
                                    open(str(pathlib.Path().absolute()) + '\\_ArrayOrderAutomator_Settings_Backup\\Long.pickle', 'wb'))
                    if self.activeArrayOrderNumbers['Short'] != '':
                        pickle.dump(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']], \
                                    open(str(pathlib.Path().absolute()) + '\\_ArrayOrderAutomator_Settings_Backup\\Short.pickle', 'wb'))
                # Updates local dict with information from dict in OperateExchange
                    self.previousPositionDict = self.currentPositionDict
                    self.updateAutomationLog()
                    self.automationSessionData['Run Time'] = run_time
                    self.automationSessionData['Error Log'] = self.OE.CTE.error_log
                    trade_history_data = copy.deepcopy(self.OE.tradeHistoryList)
                    trade_history_totals_entry = {'Time': run_time, \
                                                   'Order ID': '', \
                                                   'Account': '', \
                                                   'Symbol': '', \
                                                   'Side': '$$$ PNL', \
                                                   'Amount': '$' + str(session_PNL_in_USD), \
                                                   'Price': 'BTC PNL:', \
                                                   'Closed PNL': session_PNL}
                    trade_history_data.append(trade_history_totals_entry)
                    dataframe_of_trades = pd.DataFrame(trade_history_data, columns = ['Time', 'Order ID', 'Account', 'Symbol', 'Side', 'Amount', 'Price', 'Closed PNL'])
                    dataframe_of_errors = pd.DataFrame(self.automationSessionData['Error Log'], columns = ['Time', 'Description'])
                    automation_log_column_names = []
                    for key in self.automation_log[0]:
                        automation_log_column_names.append(key)
                    dataframe_of_automation_log = pd.DataFrame(self.automation_log, columns=automation_log_column_names)
                    CSVs_saved = False
                    while not(CSVs_saved):
                        try:
                            dataframe_of_trades.to_csv('_ArrayOrderAutomator_Logs/Automated Trade History ' + self.automationSessionData['Start Time'] + '.csv')
                            dataframe_of_errors.to_csv('_ArrayOrderAutomator_Logs/ArrayOrderAutomator Error Log ' + self.automationSessionData['Start Time'] + '.csv')
                            dataframe_of_automation_log.to_csv('_ArrayOrderAutomator_Logs/Complete Automation Log ' + self.automationSessionData['Start Time'] + '.csv')
                            CSVs_saved = True
                        except Exception as error:
                            self.OE.CTE.inCaseOfError(**{'error': error, \
                                                      'description': 'trying to save ArrayOrderAutomator CSVs', \
                                                      'program': 'AOA', \
                                                      'line_number': traceback.format_exc().split('line ')[1].split(',')[0]})
                            CSVs_saved = False
                     
    def fetchTestInput(self):
        test_input = input('\nAOA : Input a test current price, or input "1" to fetch the current price\n\nInput: ')
        if test_input == '1' or automation_input.lower() == 'fetch':
            self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
        else:
            self.OE.current_price = float(test_input)
        test_input = input('\nAOA : Please choose how to fill the currentPositionDict:\n' + \
                             '(1) : Fetch values using OE.CTE.getPositions()\n' + \
                             '(2) : Fill manually\n' + \
                             '(3) : Use current values\n' + \
                             '(4) : Fill with default values\n' + \
                             '\nInput: ')
        if test_input == '1' or test_input.lower() == 'fetch':
            self.currentPositionDict = self.OE.CTE.getPositions()
        elif test_input == '2' or test_input.lower() == 'manual':
            for key in self.currentPositionDict:
                print('\n' + key)
                if key == 'Side' or key == 'Raw Positions List':
                    self.currentPositionDict[key] = input('\nInput: ')
                else:
                    self.currentPositionDict[key] = int(input('\nInput: '))
        elif test_input == '3' or test_input.lower() == 'current':
            print('OK! Continuing with the current values.')
        elif test_input == '4' or test_input.lower() == 'default':
            self.currentPositionDict['Entry Price'] = 45000
            self.currentPositionDict['Side'] = 'buy'
            self.currentPositionDict['Leverage'] = 5
            self.currentPositionDict['Amount'] = 500
            self.currentPositionDict['Liquidation Price'] = 40000
            self.currentPositionDict['Stop-Loss'] = 41000
            self.currentPositionDict['Raw Positions List'] = []
        if self.currentPositionDict['Amount'] < self.previousPositionDict['Amount']:
            self.currentPositionLog['Exit Amount Closed'] += (self.previousPositionDict['Amount'] - self.currentPositionDict['Amount'])
        else:
            self.currentPositionLog['Entry Amount Closed'] += (self.currentPositionDict['Amount'] - self.previousPositionDict['Amount']) 
        #self.OE.CTE.fetchOpenOrders() or self.updateActiveOrders()


    def calculateSpread(self, side, starting_price):
        print('AOA : Calculating Spread for ' + side + ' order starting at $' + str(starting_price) + ' ...')
    # Set Variables
        current_position_amount = self.currentPositionDict['Amount']
        current_position_side = self.currentPositionDict['Side']
        current_position_entry = self.currentPositionDict['Entry Price']
        if side.lower() == 'buy' or side.lower() == 'long':
            side_spread_percent = self.automationSettings['Long Entry Spread %']
            side_amount = self.automationSettings['Long Entry Amount']
        elif side.lower() == 'sell' or side.lower() == 'short':
            side_spread_percent = self.automationSettings['Short Entry Spread %']
            side_amount = self.automationSettings['Short Entry Amount']
        spread = side_spread_percent * starting_price
        basic_spread = spread
    # Original Exit Strategy calculation of spread
        if self.automationSettings['Exit Strategy'] == 'Original' or self.automationSettings['Exit Strategy'] == 'Original+':
            if ((side.lower() == 'buy' or side.lower() == 'long') and (self.exiting == 'Short') and (current_position_side == 'sell')) or \
               ((side.lower() == 'sell' or side.lower() == 'short') and (self.exiting == 'Long') and (current_position_side == 'buy')):
                if side.lower() == 'buy' or side.lower() == 'long':
                    side_spread_percent = self.automationSettings['Long Exit Spread %']
                elif side.lower() == 'sell' or side.lower() == 'short':
                    side_spread_percent = self.automationSettings['Short Exit Spread %']
                spread = side_spread_percent * starting_price
                spread = max(spread * .1, spread * (1 - (current_position_amount / side_amount)))
                print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(spread) + \
                           ' because we are exiting a ' + current_position_side.upper() + ' position and our current amount ' + \
                           str(self.currentPositionDict['Amount']) + ' is ' + \
                           str(round(100 * (self.currentPositionDict['Amount'] / side_amount), 2)) + \
                           '% of our ' + current_position_side + ' Amount ' + str(self.automationSettings['Short Entry Amount']))
    # Profit at Midpoint Spread Calculation
        elif self.automationSettings['Exit Strategy'] == 'Profit at Midpoint' or self.automationSettings['Exit Strategy'] == 'Profit at Entry':
            if (side.lower() == 'buy' or side.lower() == 'long') and (self.exiting == 'Short') and (current_position_side.lower() == 'sell'):
                position_gap = self.OE.current_price - current_position_entry
                exact_midpoint_spread = 2 * position_gap
                if position_gap > 0:
                    percent_change = self.automationSettings['Midpoint Profit Modifier'] + (position_gap / basic_spread)
                    modified_spread = exact_midpoint_spread * (1 + percent_change)
                    spread = max(self.automationSettings['Minimum Exit Spread'], modified_spread)
                    if spread > self.automationSettings['Minimum Exit Spread']:
                        print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(exact_midpoint_spread) + ' plus the Midpoint Profit Modifier of ' + \
                              str(100 * self.automationSettings['Midpoint Profit Modifier']) + '% and modified by the position gap of $' + str(position_gap) + ' by ' + \
                              str(100 * (position_gap / basic_spread)) + '% making it ' + str(100 * percent_change) + '% larger at $' + str(spread) + \
                              ' because we are exiting a SHORT position and the unmodified spread would make the midpoint of the array $' + \
                              str(round(self.OE.current_price + (exact_midpoint_spread / 2), 2)) + ' which is equal to our entry price $' + str(current_position_entry))
                    else:
                        print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(spread) + ' because we are exiting a SHORT position and ' + \
                              'the Minimum Exit Spread is being used')
                else:
                    spread = self.automationSettings['Minimum Exit Spread']
                    print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(spread) + ' because we are exiting a SHORT position and ' + \
                              'the Minimum Exit Spread is being used')
            elif (side.lower() == 'sell' or side.lower() == 'short') and (self.exiting == 'Long') and (current_position_side.lower() == 'buy'):
                position_gap = current_position_entry - self.OE.current_price
                exact_midpoint_spread =  2 * position_gap
                if position_gap > 0:
                    percent_change = self.automationSettings['Midpoint Profit Modifier'] + (position_gap / basic_spread)
                    modified_spread = exact_midpoint_spread * (1 + percent_change)
                    spread = max(self.automationSettings['Minimum Exit Spread'], modified_spread)
                    if spread > self.automationSettings['Minimum Exit Spread']:
                        print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(exact_midpoint_spread) + ' plus the Midpoint Profit Modifier of ' + \
                              str(100 * self.automationSettings['Midpoint Profit Modifier']) + '% and modified by the position gap of $' + str(position_gap) + ' by ' + \
                              str(100 * (position_gap / basic_spread)) + '% making it ' + str(100 * percent_change) + '% larger at $' + str(spread) + \
                              ' because we are exiting a LONG position and this spread would make the midpoint of the array $' + \
                              str(round(self.OE.current_price + (exact_midpoint_spread / 2), 2)) + ' which is equal to our entry price $' + str(current_position_entry))
                    else:
                        print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(spread) + ' because we are exiting a LONG position and ' + \
                          'the Minimum Exit Spread is being used')
                else:
                    spread = self.automationSettings['Minimum Exit Spread']
                    print('AOA : EXIT SPREAD changed from ' + str(basic_spread) + ' to ' + str(spread) + ' because we are exiting a LONG position and ' + \
                          'the Minimum Exit Spread is being used')
    # "Profit at Entry" spread is calculated by using the Minimum Exit Spread and increasing it by the size of the current position relative to the Entry Amounts
        if self.exiting and self.automationSettings['Exit Strategy'] == 'Profit at Entry':
            if side == 'buy' and self.currentPositionDict['Side'].lower() == 'sell':
                spread = self.automationSettings['Minimum Exit Spread']
                spread = spread * (1 + (self.currentPositionDict['Amount'] / self.automationSettings['Short Entry Amount']))
            elif side == 'sell' and self.currentPositionDict['Side'].lower() == 'buy':
                spread = self.automationSettings['Minimum Exit Spread']
                spread = spread * (1 + (self.currentPositionDict['Amount'] / self.automationSettings['Long Entry Amount']))
        print('AOA : Spread calculated: $' + str(spread))
        return(spread)

    def calculateStartingPrice(self, side):
        print('AOA : Calculating Starting Price for ' + side + ' order...')
        starting_price = self.OE.current_price
        if self.initial_orders_created or (not(self.initial_orders_created) and not(self.automationSettings['Initial Starting Price'])):
            if side == 'buy':
                if self.currentPositionDict['Side'].lower() == 'buy':
                    starting_price = min(self.OE.current_price, self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %']))
                elif self.currentPositionDict['Side'].lower() == 'sell':
                    if self.exiting == 'Short':
                        if self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                            starting_price = self.OE.current_price
                        elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                            starting_price = min(self.currentPositionDict['Entry Price'] - 1, self.OE.current_price)
                        else:
                            starting_price = max(self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %']), \
                                                 self.OE.current_price)
                    else:
                        starting_price = self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %'])
            elif side == 'sell':
                if self.currentPositionDict['Side'].lower() == 'sell':
                    starting_price = max(self.OE.current_price, self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %']))
                elif self.currentPositionDict['Side'].lower() == 'buy':
                    if self.exiting == 'Long':
                        if self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                            starting_price = self.OE.current_price
                        elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                            starting_price = max(self.currentPositionDict['Entry Price'] + 1, self.OE.current_price)
                            print('16')
                            print(self.currentPositionDict['Entry Price'] + 1)
                            print(self.OE.current_price)
                        else:
                            starting_price = min(self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %']), \
                                                 self.OE.current_price)
                    else:
                        starting_price = self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %'])
        elif not(self.initial_orders_created) and self.automationSettings['Initial Starting Price']:
            if side == 'buy':
                if self.currentPositionDict['Side'].lower() == 'buy':
                    starting_price = max(self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %']), \
                                         self.OE.current_price, self.automationSettings['Initial Starting Price'])
                elif self.currentPositionDict['Side'].lower() == 'sell':
                    if self.exiting == 'Short':
                        if self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                            starting_price = self.OE.current_price
                        elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                            starting_price = self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %'])
                        else:
                            starting_price = max(self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %']), \
                                                 self.OE.current_price)
                    else:
                        starting_price = self.currentPositionDict['Entry Price'] * (1 - self.automationSettings['Starting Price Gap %'])
            elif side == 'sell':
                if self.currentPositionDict['Side'].lower() == 'sell':
                    starting_price = min(self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %']), \
                                         self.OE.current_price, self.automationSettings['Initial Starting Price'])
                elif self.currentPositionDict['Side'].lower() == 'buy':
                    if self.exiting == 'Long':
                        if self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                            starting_price = self.OE.current_price
                        elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                            starting_price = self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %'])
                        else:
                            starting_price = min(self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %']), \
                                                 self.OE.current_price)
                    else:
                        starting_price = self.currentPositionDict['Entry Price'] * (1 + self.automationSettings['Starting Price Gap %'])
        print('AOA : Starting Price calculated: $' + str(starting_price))
        return(starting_price)

    def calculateQuickGranularitySpread(self, side, spread, array_order_starting_price, intended_array_order_starting_price):
        print('AOA : Calculating QG Spread for ' + side + ' order with a Spread of $' + str(spread) + \
              ', a starting price of $' + str(array_order_starting_price) + \
              ' and an intended starting price of $' + str(intended_array_order_starting_price) + ' ...')
        qg_spread_percent = self.automationSettings['Quick Granularity Spread %']
        qg_berth = self.automationSettings['Quick Granularity Berth']
        qg_spread = qg_spread_percent * spread
        if side == 'buy':
            array_order_ending_price = intended_array_order_starting_price - spread
            qg_start_price = self.OE.current_price + (spread * qg_berth)
            if qg_start_price > intended_array_order_starting_price:
                qg_start_price = intended_array_order_starting_price
            qg_end_price = qg_start_price - qg_spread
            qg_start_percent = (intended_array_order_starting_price - qg_start_price) / spread
            qg_end_percent = min(qg_start_percent + qg_spread_percent, 1)
            if qg_start_price != intended_array_order_starting_price:
                if qg_start_price < intended_array_order_starting_price:
                    print('AOA & & & & & & & Quick Granularity Start Price $' + str(qg_start_price) + ' is BELOW the LONG Array Order Starting Price $' + \
                          str(intended_array_order_starting_price) + ' which makes sense because the current price is $' + str(self.OE.current_price) + \
                          ' which creates a berth of ' + str(100 * ((qg_start_price - self.OE.current_price) / spread)) + '% (this should be at most ' + str(qg_berth) + ')')
                    self.AP.playSound('Navi Hey Listen')
                elif qg_start_price > intended_array_order_starting_price:
                    print('\nAOA : &&&&&&&&&& ERROR! &&&&&&&&&&')
                    print('AOA !!!!!!!!!! &&&&&&& Quick Granularity Start Price $' + str(qg_start_price) + ' is ABOVE the LONG Array Order Starting Price $' + \
                          str(intended_array_order_starting_price) + ' which makes no sense!')
                    self.AP.playSound('Navi Hey')
            else:
                print('AOA & & & & & & & Quick Granularity Start Price $' + str(qg_start_price) + \
                      ' is equal to the LONG Array Order Starting Price $' + str(intended_array_order_starting_price))
        elif side == 'sell':
            array_order_ending_price = intended_array_order_starting_price + spread
            qg_start_price = self.OE.current_price - (spread * qg_berth)
            if qg_start_price < intended_array_order_starting_price:
                qg_start_price = intended_array_order_starting_price
            qg_end_price = qg_start_price + qg_spread
            qg_start_percent = (qg_start_price - intended_array_order_starting_price) / spread
            qg_end_percent = min(qg_start_percent + qg_spread_percent, 1)
            if qg_start_price != intended_array_order_starting_price:
                if qg_start_price > intended_array_order_starting_price:
                    print('AOA & & & & & & & Quick Granularity Start Price $' + str(qg_start_price) + ' is ABOVE the SHORT Array Order Starting Price $' + \
                          str(intended_array_order_starting_price) + ' which makes sense because the current price is $' + str(self.OE.current_price) + \
                          ' which creates a berth of ' + str(100 * ((self.OE.current_price - qg_start_price) / spread)) + '% (this should be at most ' + str(qg_berth) + ')')
                    self.AP.playSound('Navi Hey Listen')
                elif qg_start_price < intended_array_order_starting_price:
                    print('\nAOA : &&&&&&&&&& ERROR! &&&&&&&&&&')
                    print('AOA !!!!!!!!!! &&&&&&& Quick Granularity Start Price $' + str(qg_start_price) + ' is BELOW the SHORT Array Order Starting Price $' + \
                          str(intended_array_order_starting_price) + ' which makes no sense!')
                    self.AP.playSound('Navi Hey')
            else:
                print('AOA & & & & & & & Quick Granularity Start Price $' + str(qg_start_price) + \
                      ' is equal to the SHORT Array Order Starting Price $' + str(intended_array_order_starting_price))

        quick_granularity_spread_dict = {'Quick Granularity Start %': qg_start_percent, \
                                         'Quick Granularity End %': qg_end_percent}
        print('AOA : QG Spread calculated!')
        print(quick_granularity_spread_dict)
        return(quick_granularity_spread_dict)

    def calculateGranularity(self, side, spread, number_of_orders):
        qg_spread_percent = self.automationSettings['Quick Granularity Spread %']
        qg_intensity = self.automationSettings['Quick Granularity Intensity']
        if not(self.exiting) or \
           (self.exiting == 'Long' and self.currentPositionDict['Side'].lower() == 'buy' and side == 'buy') or \
           (self.exiting == 'Short' and self.currentPositionDict['Side'].lower() == 'sell' and side == 'sell'):
            granularity = ((spread * qg_spread_percent) + ((spread * (1 - qg_spread_percent)) / (qg_intensity + 1))) / (number_of_orders - 1)
        #granularity = spread / number_of_orders
        if granularity <= 0:
            symbol = self.OE.orderSettings['Symbol']
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                granularity = .5
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                granularity = .01
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                granularity = .0001
        return(granularity)

    def calculateStopPrice(self):
    # To-Do:
    #   -Enable awareness of "levels"; if a falling stop loss is 50029, make it 49950 instead
        print('AOA : Calculating Stop-Loss Price...........')
        if self.currentPositionDict['Side'].lower() == 'buy':
            intended_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Array Order Parameters']['Highest Price Order Price']
            if self.automationSettings['Stop-Loss Strategy'] == 'Static %':
                stop_price = intended_starting_price * (1 - self.automationSettings['Stop-Loss Spread %'])
            elif self.automationSettings['Stop-Loss Strategy'] == 'Based on Entry Spread %':
                stop_price = intended_starting_price * (1 - self.automationSettings['Long Entry Spread %']) * (1 - self.automationSettings['Stop-Loss Modifier %'])
            else:
                print('AOA : No recognized Stop-Loss Strategy was found! Stop-Loss Price NOT calculated!')
                stop_price = None
        elif self.currentPositionDict['Side'].lower() == 'sell':
            intended_starting_price = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Array Order Parameters']['Lowest Price Order Price']
            if self.automationSettings['Stop-Loss Strategy'] == 'Static %':
                stop_price = intended_starting_price * (1 + self.automationSettings['Stop-Loss Spread %'])
            elif self.automationSettings['Stop-Loss Strategy'] == 'Based on Entry Spread %':
                stop_price = intended_starting_price * (1 + self.automationSettings['Short Entry Spread %']) * (1 + self.automationSettings['Stop-Loss Modifier %'])
            else:
                print('AOA : No recognized Stop-Loss Strategy was found! Stop-Loss Price NOT calculated!')
                stop_price = None
        else:
            print('AOA : No current position open! This means no Stop-Loss Price is to be calculated.')
            stop_price = None
        print('AOA : Stop-Loss Price calculated to be $' + str(stop_price))
        return(stop_price)
                    

    def createArrayOrder(self, side):
    # Settings default to entry settings, which includes original basic Spread calculation
        if side == 'sell':
            symbol = self.OE.orderSettings['Symbol']
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                self.OE.current_price += .5
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                self.OE.current_price += .01
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                self.OE.current_price += .0001
        starting_price = self.calculateStartingPrice(side)
        spread = self.calculateSpread(side, starting_price)
        style = self.automationSettings['Entry Style']
        steepness = self.automationSettings['Entry Steepness']
        quick_granularity_intensity = self.automationSettings['Quick Granularity Intensity']
        qg_start_percent = None
        qg_end_percent = None
        maximum_amount = None
        relief_amount = None
    # Creates BUY order
        if side == 'buy':
            amount = self.automationSettings['Long Entry Amount']
            if self.currentPositionDict['Side'].lower() == 'sell':
            # Exiting SHORT
                if self.exiting == 'Short':
                # Original Exit Strategy
                    if self.automationSettings['Exit Strategy'] == 'Original':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                # Original+ Exit Straetgy
                        if '+' in self.automationSettings['Exit Strategy']:
                            maximum_amount = self.currentPositionDict['Amount']
                # Profit at Midpoint Exit Strategy
                    elif self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                        amount = self.currentPositionDict['Amount']
                        quick_granularity_intensity = False
                # Profit at Entry Exit Strategy
                    elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                        amount = self.currentPositionDict['Amount']
                        quick_granularity_intensity = False
                        # amount is reduced to complement a Relief Order if the current position size is large enough
                        if self.automationSettings['Relief Order %'] and self.automationSettings['Relief Trigger Amount']:
                            if self.automationSettings['Relief Trigger Amount'] >= amount:
                                relief_amount = amount * self.automationSettings['Relief Order %']
                                amount = amount * (1 - self.automationSettings['Relief Order %'])
            end_price = starting_price - spread
            if starting_price - self.OE.current_price >= .3 * spread:
                quick_granularity_intensity = False
    # Creates SELL order
        elif side == 'sell':
            amount = self.automationSettings['Short Entry Amount']
            if self.currentPositionDict['Side'].lower() == 'buy':
            # Exiting LONG
                if self.exiting == 'Long':
                # Original Exit Strategy
                    if self.automationSettings['Exit Strategy'] == 'Original':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                # Original+ Exit Strategy
                        if '+' in self.automationSettings['Exit Strategy']:
                            maximum_amount = self.currentPositionDict['Amount']
                # Profit at Midpoint Exit Strategy
                    elif self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                        amount = self.currentPositionDict['Amount']
                        quick_granularity_intensity = False
                # Profit at Entry Exit Strategy
                    elif self.automationSettings['Exit Strategy'] == 'Profit at Entry':
                        style = self.automationSettings['Exit Style']
                        steepness = self.automationSettings['Exit Steepness']
                        amount = self.currentPositionDict['Amount']
                        quick_granularity_intensity = False
                        # amount is reduced to complement a Relief Order if the current position size is large enough
                        if self.automationSettings['Relief Order %'] and self.automationSettings['Relief Trigger Amount']:
                            if self.automationSettings['Relief Trigger Amount'] >= amount:
                                relief_amount = amount * self.automationSettings['Relief Order %']
                                amount = amount * (1 - self.automationSettings['Relief Order %'])
            end_price = starting_price + spread
            if self.OE.current_price - starting_price >= .3 * spread:
                quick_granularity_intensity = False
  #!# This is a double-check to make sure that the default exit amount is not being used with a small spread by accident
        critical_error = False
        if side.lower() == 'buy' or side.lower() == 'long':
            side_spread_percent = self.automationSettings['Long Entry Spread %']
            side_amount = self.automationSettings['Long Entry Amount']
        elif side.lower() == 'sell' or side.lower() == 'short':
            side_spread_percent = self.automationSettings['Short Entry Spread %']
            side_amount = self.automationSettings['Short Entry Amount']
        entry_spread = side_spread_percent * starting_price
        if amount == side_amount:
            if spread != entry_spread:
                critical_error = True
                print('\n\nAOA : ********************** SUSPICIOUS! The ENTRY AMOUNT of ' + str(side_amount) + ' is being used, but the ENTRY SPREAD ' + str(entry_spread) + \
                      ' is not being used, and ' + str(spread) + ' is being used instead! ************************')
                self.AP.playSound('Navi Hey')    
                self.currentPositionDict = self.OE.CTE.getPositions()
                if self.currentPositionDict['Amount'] >= .5 * amount:
                    if self.currentPositionDict['Side'].lower() == 'buy':
                        if side.lower == 'sell':
                            print('AOA : ~~~~~~~~~~~~~~~~~~~~~~~~~~ I guess it was a fluke of suspicion! The current position amount is ' + str(self.currentPositionDict['Amount']) + \
                                  ' so an order amount of ' + str(amount) + ' makes sense. ~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            critical_error = 'fluke'
                    if self.currentPositionDict['Side'].lower() == 'sell':
                        if side.lower == 'buy':
                            print('AOA : ~~~~~~~~~~~~~~~~~~~~~~~~~~ I guess it was a fluke of suspicion! The current position amount is ' + str(self.currentPositionDict['Amount']) + \
                                  ' so an order amount of ' + str(amount) + ' makes sense. ~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            critical_error = 'fluke'
        elif spread == entry_spread:
            if amount != side_amount:
                critical_error = True
                print('\n\nAOA : ********************** SUSPICIOUS! The ENTRY SPREAD ' + str(entry_spread) + ' is being used, but the ENTRY AMOUNT of ' + str(side_amount) + \
                      ' is not being used, and ' + str(amount) + ' is being used instead! ************************')
                self.AP.playSound('Navi Hey')    
                self.currentPositionDict = self.OE.CTE.getPositions()
                position_gap = self.OE.current_price - self.currentPositionDict['Entry Price']
                if position_gap < 0:
                    position_gap = (-1) * position_gap
                if position_gap * 2 > .5 * spread:
                    if self.currentPositionDict['Side'].lower() == 'buy':
                        if side.lower == 'sell':
                            print('AOA : ~~~~~~~~~~~~~~~~~~~~~~~~~~ I guess it was a fluke of suspicion! The current position gap is ' + str(position_gap) + \
                                  ' so a spread of ' + str(spread) + ' makes sense. ~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            critical_error = 'fluke'
                    if self.currentPositionDict['Side'].lower() == 'sell':
                        if side.lower == 'buy':
                            print('AOA : ~~~~~~~~~~~~~~~~~~~~~~~~~~ I guess it was a fluke of suspicion! The current position gap is ' + str(position_gap) + \
                                  ' so a spread of ' + str(spread) + ' makes sense. ~~~~~~~~~~~~~~~~~~~~~~~~~~')
                            critical_error = 'fluke'
        if critical_error == 'fluke':
            self.AP.playSound('Navi Hey Listen')
            critical_error = False
    # Granularity is calculated
        granularity = (int(spread / (.5 * self.automationSettings['Number of Entry Orders'])) / 2) + .5
        number_of_orders = int(spread / granularity) + 1
        if not(self.exiting) or \
           (side == 'buy' and self.exiting == 'Long' and self.currentPositionDict['Side'].lower() == 'buy') or \
           (side == 'sell' and self.exiting == 'Short' and self.currentPositionDict['Side'].lower() == 'sell'):
            if self.automationSettings['Quick Granularity Strategy']:
                original_granularity = granularity
                original_number_of_orders = number_of_orders
                granularity = self.calculateGranularity(side, spread, self.automationSettings['Number of Entry Orders'])
                number_of_orders = int(spread / granularity) + 1
                qg_spread_dict = self.calculateQuickGranularitySpread(side, spread, starting_price, starting_price)
                qg_start_percent = qg_spread_dict['Quick Granularity Start %']
                qg_end_percent = qg_spread_dict['Quick Granularity End %']
                print('AOA : & & & & & & & & & & & & & & & & & & &     Fancy new Quick Granularity being used!     & & & & & & & & & & & & & & & & &')
                print('\nAOA : & & & & & & & & & & & & & & & & & & &         Quick Granularity Intensity: ' + str(quick_granularity_intensity))
                print('\nAOA : & & & & & & & & & & & & & & & & & & &         Old Granularity: ' + str(original_granularity))
                print('AOA : & & & & & & & & & & & & & & & & & & &         New Granularity: ' + str(granularity))
                print('\nAOA : & & & & & & & & & & & & & & & & & & &         Old Number of Orders: ' + str(original_number_of_orders))
                print('AOA : & & & & & & & & & & & & & & & & & & &         New Number of Orders: ' + str(number_of_orders))
                print('\nAOA : & & & & & & & & & & & & & & & & & & &         Quick Granularity Start %: ' + str(100 * qg_start_percent))
                print('AOA : & & & & & & & & & & & & & & & & & & &         Quick Granularity End %: ' + str(100 * qg_end_percent))
            else:
                quick_granularity_intensity = None
####                print('GRANULARITY NOT REASSIGNED!')
####                self.AP.playSound('Tim Allen')
        else:
            if (side == 'sell' and self.exiting == 'Long' and self.currentPositionDict['Side'].lower() == 'buy') or \
               (side == 'buy' and self.exiting == 'Short' and self.currentPositionDict['Side'].lower() == 'sell'):
                if number_of_orders > amount / 2:
                    granularity = .5 + int(2 * ((spread / amount) * 2)) / 2
                elif self.automationSettings['Exit Strategy'] == 'Profit at Midpoint':
                    granularity = granularity * 2
####                else:
####                    print('GRANULARITY NOT REASSIGNED!')
####                    self.AP.playSound('Tim Allen')
####            else:
####                print('GRANULARITY NOT REASSIGNED!')
####                self.AP.playSound('Tim Allen')
##      #This makes it so that we wind up with 180 orders total while entering, instead of 120
##        if quick_granularity_intensity == 'High':
##            granularity = int(((granularity / 3) * 4)) / 2
    # Order settings are assigned and executed (if there were no critical errors)
        if critical_error:
            print('\nAOA : !!!!!!!!!!!!!!!!!!!!!!!!!! Order is NOT BEING CREATED due to a critical calculation error!!!!!!!!!!!!!!!!!!!!!!!!')
            self.AP.playSound('Navi Hey')
        else:
        # Relief Order is created if creating an exit order and Relief Order conditions are met
            if relief_amount:
                relief_spread = abs(self.OE.current_price - starting_price)
                relief_granularity = relief_spread / relief_amount
                if relief_granularity == (int(2 * relief_granularity) / 2):
                    relief_granularity = int(2 * relief_granularity) / 2
                else:
                    relief_granularity = (int(2 * relief_granularity) / 2) + .5
                self.OE.orderSettings = {'Exchange': 'Default', \
                                         'Account': self.automationSettings['Account'], \
                                         'Symbol': self.automationSettings['Symbol'], \
                                         'Side': side, \
                                         'Amount': relief_amount, \
                                         'Order Type': 'Limit', \
                                         'Price': self.OE.current_price}
                self.OE.arrayOrderSettings = {'Granularity': relief_granularity, \
                                              'Spread': relief_spread, \
                                              'End Price': starting_price, \
                                              'Steepness': 0, \
                                              'Minimum Order Size': 1, \
                                              'Style': 'Uniform', \
                                              'Quick Granularity Intensity': 0, \
                                              'Quick Granularity Start %': 0, \
                                              'Quick Granularity End %': 0}
                self.OE.createArrayOrder('update_current_parameters')
                if not(self.testing):
                    new_order = self.OE.executeArrayOrders(self.OE.arrayOrderParameters['Individual Order Settings'])
                    if side == 'buy':
                        self.activeArrayOrderNumbers['Long Relief'] = new_order['Array Order Number']
                    else:
                        self.activeArrayOrderNumbers['Short Relief'] = new_order['Array Order Number']
                print('AOA : ' + side.upper() + ' Relief Array Order created to EXIT ' + self.exiting + ' position!\n')
            # Array Order settings are assigned and executed
            self.OE.orderSettings = {'Exchange': 'Default', \
                                     'Account': self.automationSettings['Account'], \
                                     'Symbol': self.automationSettings['Symbol'], \
                                     'Side': side, \
                                     'Amount': amount, \
                                     'Order Type': 'Limit', \
                                     'Price': starting_price}
            self.OE.arrayOrderSettings = {'Granularity': granularity, \
                                          'Spread': spread, \
                                          'End Price': end_price, \
                                          'Steepness': steepness, \
                                          'Minimum Order Size': 1, \
                                          'Style': style, \
                                          'Quick Granularity Intensity': quick_granularity_intensity, \
                                          'Quick Granularity Start %': qg_start_percent, \
                                          'Quick Granularity End %': qg_end_percent, \
                                          'Maximum Amount': maximum_amount, \
                                          'Readjust to Execute Maximum Amount': False}
            self.OE.createArrayOrder('update_current_parameters')
            if not(self.testing):
                new_order = self.OE.executeArrayOrders(self.OE.arrayOrderParameters['Individual Order Settings'])
                if side == 'buy':
                    self.activeArrayOrderNumbers['Long'] = new_order['Array Order Number']
                else:
                    self.activeArrayOrderNumbers['Short'] = new_order['Array Order Number']
            if self.exiting:
                print('AOA : ' + side.upper() + ' order created to EXIT ' + self.exiting + ' position!\n')
            else:
                print('AOA : ' + side.upper() + ' ENTRY order created!\n')
  # # Position and Active Orders are updated
        self.updateActiveOrders()
        self.currentPositionDict = self.OE.CTE.getPositions()
        self.order_created_this_loop = True
    # If current_side was modified at the beginning because this created a sell order, current_price is reset back to being the 'bid' price instead of 'ask'
        if side == 'sell':
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                self.OE.current_price -= .5
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                self.OE.current_price -= .01
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                self.OE.current_price -= .0001

    def cancelArrayOrder(self, array_order_number):
        if not(self.testing):
            self.OE.cancelArrayOrder(array_order_number)


    def displayRunTime(self, seconds):
        run_time_dict = self.CT.convertTimestamp(seconds * 1000)
        if len(str(run_time_dict['Minutes'])) == 1:
            minutes_string = '0' + str(run_time_dict['Minutes'])
        else:
            minutes_string = str(run_time_dict['Minutes'])
        if run_time_dict['Days'] > 0:
            run_time_string = 'Run Time: ' + str(run_time_dict['Days']) + ' days, ' + str(run_time_dict['Hours']) + ':' + minutes_string + ' and ' + str(run_time_dict['Seconds']) + ' seconds'
        elif run_time_dict['Hours'] > 0:
            run_time_string = 'Run Time: ' + str(run_time_dict['Hours']) + ':' + minutes_string + ' and ' + str(run_time_dict['Seconds']) + ' seconds'
        elif run_time_dict['Minutes'] > 0:
            run_time_string = 'Run Time: ' + str(run_time_dict['Minutes']) + ' minutes and ' + str(run_time_dict['Seconds']) + ' seconds'
        else:
            run_time_string = 'Run Time: ' + str(run_time_dict['Seconds']) + ' seconds'
        print(run_time_string)
        return(run_time_string)

    def updateAutomationLog(self):
        new_entry = {}
        current_time = self.GCT.getDateTimeString()
        new_entry['Time'] = current_time
    # Automation Settings
        for setting in self.automationSettings:
            new_entry[setting] = self.automationSettings[setting]
    # Current Position
        for setting in self.currentPositionDict:
            value = self.currentPositionDict[setting]
            if setting in new_entry:
                setting = 'Position ' + setting    
            new_entry[setting] = value
    # Order Settings
        for setting in self.OE.orderSettings:
            value = self.OE.orderSettings[setting]
            if setting in new_entry:
                setting = 'Order ' + setting    
            new_entry[setting] = value
    # Array Order Settings
        for setting in self.OE.arrayOrderSettings:
            value = self.OE.arrayOrderSettings[setting]
            if setting in new_entry:
                setting = 'Array Setting ' + setting    
            new_entry[setting] = value
    # Array Order Parameters
        for setting in self.OE.orderSettings:
            value = self.OE.orderSettings[setting]
            if setting in new_entry:
                setting = 'Array Parameter ' + setting    
            new_entry[setting] = value
    # Other variables
        new_entry['Exiting'] = self.exiting
    # New entry is added to the log
        self.automation_log.append(new_entry)
        return(new_entry)

    def updateActiveOrders(self):
        print('AOA : Updating active array orders............................')
        all_open_orders = self.OE.CTE.fetchOpenOrders()
        buy_orders = {}
        buy_total_amount = 0
        buy_order_prices = []
        sell_orders = {}
        sell_total_amount = 0
        sell_order_prices = []
        stop_loss_orders = {}
        stop_total_amount = 0
        if all_open_orders != []:
        # Orders that are open are accumulated
            for order in all_open_orders:
                if order['type'] == 'Stop':
                    order = self.OE.CTE.prettifyOrder(order)
                    stop_loss_orders[order['ID']] = order
                    stop_total_amount += float(order['Amount'])
                else:
                    if order['side'] == 'buy':
                        buy_orders[order['id']] = order
                        buy_total_amount += float(order['amount'])
                        buy_order_prices.append(order['price'])
                    elif order['side'] == 'sell':
                        sell_orders[order['id']] = order
                        sell_total_amount += float(order['amount'])
                        sell_order_prices.append(order['price'])
        # Missing orders that aren't present in all_open_orders are recorded
            if self.activeArrayOrderNumbers['Long'] != '':
                for ID in self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Active Orders']:
                    if not(ID in buy_orders):
                        self.OE.recordClosedOrder(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Active Orders'][ID])
            if self.activeArrayOrderNumbers['Short'] != '':
                for ID in self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Active Orders']:
                    if not(ID in sell_orders):
                        self.OE.recordClosedOrder(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Active Orders'][ID])
        # arrayOrderLedger is updated and the current array order parameters are displayed       
            print('\nAOA : Active array orders updated!\n')
          # Long
            if self.activeArrayOrderNumbers['Long'] != '':
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Active Orders'] = buy_orders
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Total Amount'] = buy_total_amount
                print("            Buy Orders' Total Amount: " + str(buy_total_amount))
                print("            # of Buy Orders: " + str(len(buy_orders)))
                if len(buy_orders) > 0:
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Starting Price'] = max(buy_order_prices)
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Ending Price'] = min(buy_order_prices)
                    print("            Buy Orders start at " + str(max(buy_order_prices)) + " and end at " + str(min(buy_order_prices)) + "\n")
                    print("            Intended Starting Price: " + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Order Settings']['Price']))
                else:
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Starting Price'] = False
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Ending Price'] = False
                    self.activeArrayOrderNumbers['Long'] = ''
          # Short
            if self.activeArrayOrderNumbers['Short'] != '':
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Active Orders'] = sell_orders
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Total Amount'] = sell_total_amount
                print("            Sell Orders' Total Amount: " + str(sell_total_amount))
                print("            # of Sell Orders: " + str(len(sell_orders)))
                if len(sell_orders) > 0:
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Starting Price'] = min(sell_order_prices)
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Ending Price'] = max(sell_order_prices)
                    print("            Sell Orders start at " + str(min(sell_order_prices)) + " and end at " + str(max(sell_order_prices)) + "\n")
                    print("            Intended Starting Price: " + str(self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Order Settings']['Price']))
                else:
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Starting Price'] = False
                    self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Ending Price'] = False
                    self.activeArrayOrderNumbers['Short'] = ''
        # Stop-Loss orders dict is updated
            self.openStopLossOrders['Open Orders'] = stop_loss_orders
            self.openStopLossOrders['Total Amount'] = stop_total_amount
        else:
            print('AOA : No active orders!')
            if self.activeArrayOrderNumbers['Long'] != '':
                self.activeArrayOrderNumbers['Long'] = ''
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Active Orders'] = []
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Total Amount'] = 0
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Starting Price'] = False
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Ending Price'] = False
            if self.activeArrayOrderNumbers['Short'] != '':
                self.activeArrayOrderNumbers['Short'] = ''
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Active Orders'] = []
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Total Amount'] = 0
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Starting Price'] = False
                self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Ending Price'] = False
            

    def exitCheck(self):
        print('\nAOA : Running exitCheck()...........................................')
        if self.currentPositionDict['Amount'] == 0:
            if self.exiting == 'Long' and self.currentPositionDict['Side'].lower() != 'buy':
                print('AOA : MODE SWITCH! The LONG position closed & we are leaving EXIT mode and switching to ENTRY.')
                self.inCaseOfPositionClosed()
            elif self.exiting == 'Short' and self.currentPositionDict['Side'].lower() != 'sell':
                print('AOA : MODE SWITCH! The SHORT position closed & we are leaving EXIT mode and switching to ENTRY.')
                self.inCaseOfPositionClosed()
            else:
                print('AOA : No mode switch - our current position amount is 0.')
            self.exiting = False
        else:
            if not(self.exiting):
                if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                    if self.currentPositionDict['Side'].lower() == 'sell':
                        print('AOA : MODE SWITCH! Leaving ENTRY mode and switching to EXIT SHORT position.')
                        self.AP.playSound('Navi Hey Listen')
                        self.exiting = 'Short'
                    else:
                        print('AOA : MODE SWITCH! Leaving ENTRY mode and switching to EXIT LONG position.')
                        self.AP.playSound('Navi Hey Listen')
                        self.exiting = 'Long'
                else:
                    print('AOA : No mode switch - our current position amount ' + str(self.currentPositionDict['Amount']) + \
                          ' is less than our exit amount ' + str(self.automationSettings['Exit Amount']))
            else:
                print('\nAOA : Checking if the SIDE of our position switched...')
                if (self.exiting == 'Long') and (self.currentPositionDict['Side'].lower() == 'sell'):
                    if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                        self.exiting = 'Short'
                        print('AOA : SIDE SWITCH!!! Long position was closed and now trying to EXIT SHORT position.')
                    else:
                        self.exiting = False
                        print('AOA : MODE SWITCH! The SHORT position closed & we are leaving EXIT mode and switching to ENTRY.')
                    self.AP.playSound('Navi Hey Listen')
                    self.inCaseOfPositionClosed()
                elif (self.exiting == 'Short') and (self.currentPositionDict['Side'].lower() == 'buy'):
                    if self.currentPositionDict['Amount'] >= self.automationSettings['Exit Amount']:
                        self.exiting = 'Long'
                        print('AOA : SIDE SWITCH!!! Short position was closed and now trying to EXIT LONG position.')
                    else:
                        self.exiting = False
                        print('AOA : MODE SWITCH! The LONG position closed & we are leaving EXIT mode and switching to ENTRY.')
                    self.AP.playSound('Navi Hey Listen')
                    self.inCaseOfPositionClosed()
                else:
                    print('AOA : No mode switch - we are currently exiting ' + str(self.exiting) + ', which makes sense to close our current ' + \
                          str(self.currentPositionDict['Side'].lower()) + ' position of ' + str(self.currentPositionDict['Amount']))
                    

    def modifyArrayOrder(self, side, *args):
        print('modifyArrayOrder args', args)
    # Settings default to entry settings, which includes original basic Spread calculation
        if side == 'sell':
            symbol = self.OE.orderSettings['Symbol']
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                self.OE.current_price += .5
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                self.OE.current_price += .01
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                self.OE.current_price += .0001
    # Quick Granularity Start & End modification
        qg_start_percent = args[0]['Quick Granularity Start %']
        qg_end_percent = args[0]['Quick Granularity End %']
        if side == 'buy':
            print('\nAOA : MODIFYING buy array order Quick Granularity Start & End %.................................')
            self.OE.orderSettings = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Order Settings']
            self.OE.arrayOrderSettings = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Long']]['Array Order Settings']
            self.OE.arrayOrderSettings['Quick Granularity Start %'] = qg_start_percent
            self.OE.arrayOrderSettings['Quick Granularity End %'] = qg_end_percent
        # This limits the size of the array order to prevent placing orders again at prices at which they previously closed
            if (self.automationSettings['Rebuild Strategy'] == 'No Rebuild') and (self.currentPositionDict['Side'].lower() == 'buy'):
                self.OE.arrayOrderSettings['Maximum Amount'] = self.automationSettings['Long Entry Amount'] - self.currentPositionDict['Amount']
            self.cancelArrayOrder(self.activeArrayOrderNumbers['Long'])
            self.OE.createArrayOrder('update_current_parameters')
            new_order = self.OE.executeArrayOrders(self.OE.arrayOrderParameters['Individual Order Settings'])
            self.activeArrayOrderNumbers['Long'] = new_order['Array Order Number']
        elif side == 'sell':
            print('\nAOA : MODIFYING sell array order Quick Granularity Start & End %.................................')
            self.OE.orderSettings = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Order Settings']
            self.OE.arrayOrderSettings = self.OE.arrayOrderLedger[self.activeArrayOrderNumbers['Short']]['Array Order Settings']
            self.OE.arrayOrderSettings['Quick Granularity Start %'] = qg_start_percent
            self.OE.arrayOrderSettings['Quick Granularity End %'] = qg_end_percent
        # This limits the size of the array order to prevent placing orders again at prices at which they previously closed
            if (self.automationSettings['Rebuild Strategy'] == 'No Rebuild') and (self.currentPositionDict['Side'].lower() == 'sell'):
                self.OE.arrayOrderSettings['Maximum Amount'] = self.automationSettings['Short Entry Amount'] - self.currentPositionDict['Amount']
            self.cancelArrayOrder(self.activeArrayOrderNumbers['Short'])
            self.OE.createArrayOrder('update_current_parameters')
            new_order = self.OE.executeArrayOrders(self.OE.arrayOrderParameters['Individual Order Settings'])
            self.activeArrayOrderNumbers['Short'] = new_order['Array Order Number']
        print('\nAOA : Array Order MODIFIED!')
        print('          Quick Granularity Start % changed to ' + str(100 * qg_start_percent) + '%')
        print('          Quick Granularity End % changed to ' + str(100 * qg_end_percent) + '%')
    # Position and Active Orders are updated 
        self.currentPositionDict = self.OE.CTE.getPositions()
        self.updateActiveOrders()
        self.order_created_this_loop = True
    # If current_side was modified at the beginning because this created a sell order, current_price is reset back to being the 'bid' price instead of 'ask'
        if side == 'sell':
            if symbol == 'BTC' or symbol == 'BTC/USD' or symbol == 'BTC/USDT':
                self.OE.current_price -= .5
            elif symbol == 'LTC' or symbol == 'LTC/USD' or symbol == 'LTC/USDT':
                self.OE.current_price -= .01
            elif symbol == 'DOGE' or symbol == 'DOGE/USD' or symbol == 'DOGE/USDT':
                self.OE.current_price -= .0001


    def updateStopLoss(self):
        print('AOA : Updating Stop-Loss Order............')
        expected_stop_price = self.calculateStopPrice()
        update_complete = False
        loop_count = 0
        while not(update_complete) and expected_stop_price:
            loop_count += 1
            if len(self.openStopLossOrders['Open Orders']) > 1:
                print('AOA : Huh?!?! There were multiple stop-loss orders found! Canceling them them all now...')
                self.AP.playSound('Tim Allen')
                for order_ID in self.openStopLossOrders['Open Orders']:
                    self.OE.CTE.exchange.cancelOrder(order_ID, self.openStopLossOrders['Open Orders'][order_ID]['info']['symbol'])
                self.stopLossOrder = ''
            elif len(self.openStopLossOrders['Open Orders']) == 1:
                stop_loss_order_ID = list(self.openStopLossOrders['Open Orders'])[0]
                stop_loss_order = self.openStopLossOrders['Open Orders'][stop_loss_order_ID]
                if self.stopLossOrder == '':
                    print('AOA : Huh?!?! There is a stop-loss order open but we do NOT currently have an active stop-loss order saved! Canceling it now...')
                    self.AP.playSound('Tim Allen')
                    self.OE.CTE.exchange.cancelOrder(stop_loss_order_ID, stop_loss_order['Symbol'])
                elif stop_loss_order_ID != self.stopLossOrder['ID']:
                    print('AOA : Huh?!?! The ID we have saved for our stop-loss does NOT match the currently active stop-loss order! Canceling it now...')
                    self.AP.playSound('Tim Allen')
                    self.OE.CTE.exchange.cancelOrder(stop_loss_order_ID, stop_loss_order['Symbol'])
                    self.stopLossOrder = ''
                else:
                    self.stopLossOrder = self.openStopLossOrders['Open Orders'][stop_loss_order_ID]
                    if self.stopLossOrder['Amount'] != self.currentPositionDict['Amount']:
                        print('AOA : The amount of our stop-loss ' + str(self.stopLossOrder['Amount']) + \
                              ' does NOT match our position size of ' + str(self.currentPositionDict['Amount']) + '. Canceling it now...')
                        self.OE.CTE.exchange.cancelOrder(self.stopLossOrder['ID'], self.stopLossOrder['Symbol'])
                        self.stopLossOrder = ''
                    elif self.stopLossOrder['Stop Price'] + .5 < expected_stop_price or \
                         self.stopLossOrder['Stop Price'] - .5 > expected_stop_price:
                        print('AOA : The price of our stop-loss $' + str(self.stopLossOrder['Stop Price']) + \
                              ' does NOT match the expected price of $' + str(expected_stop_price) + '. Canceling it now...')
                        self.OE.CTE.exchange.cancelOrder(self.stopLossOrder['ID'], self.stopLossOrder['Symbol'])
                        self.stopLossOrder = ''
                    else:
                        print('AOA : The currently active stop-loss order matches the currently saved ID, our current position amount, and the expected price!')
                        print('        | ---------- Current Order ---------- | ---------- Expected Values -----------')
                        print('ID:     |' + stop_loss_order_ID + ' | ' + self.stopLossOrder['ID'])
                        print('Amount: |                   ' + str(self.stopLossOrder['Amount']) + '              |             ' + str(self.currentPositionDict['Amount']))
                        print('Price:  |              '    + str(self.stopLossOrder['Price']) + '              |           ' + str(expected_stop_price))
            else:
                print('AOA : No stop-loss order found!')
                self.stopLossOrder = ''
            if self.stopLossOrder == '':
                if self.exiting and self.currentPositionDict['Amount'] > 0:
                    print('AOA : Creating a new stop-loss order...........')
                    self.stopLossOrder = self.OE.createStopLossOrder(expected_stop_price, current_price=self.OE.current_price, position_dict=self.currentPositionDict)
                    print('AOA : Stop-loss order created!')
                    self.updateActiveOrders()
                    self.currentPositionDict = self.OE.CTE.getPositions()
                    self.OE.current_price = self.OE.CTE.fetchCurrentPrice()
                    update_complete = False
                else:
                    print('AOA : We are NOT in EXIT mode, so no stop-loss order is being created.')
                    update_complete = True
            else:
                print("AOA : Stop-Loss Order Update finished! It's a " + self.stopLossOrder['Side'] + \
                      " order for " + str(self.stopLossOrder['Amount']) + \
                      " at $" + str(self.stopLossOrder['Stop Price']))
                update_complete = True
            if loop_count >= 3 and not(update_complete):
                print("AOA : Huh?!?! updateStopLoss() has looped " + str(loop_count) + " times! That's weird...")
                self.AP.playSound('Tim Allen')
            if loop_count >= 7 and not(update_complete):
                print("AOA : updateStopLoss() FAILED! It looped " + str(loop_count) + " times without success!")
                self.AP.playSound('Kill Bill Siren')
                break

                
        

    def inCaseOfPositionClosed(self):
        print('AOA : !!!!!!!!!!!!!!!*************        Position Closed        *************!!!!!!!!!!!!!!!')
        session_PNL = self.OE.CTE.getBalances()['Spot'][self.automationSettings['Symbol'].split('/')[0]]['total'] - self.starting_balance
        session_PNL_in_USD = round(self.OE.current_price * session_PNL, 2)
        self.automationSessionData['Session Total PNL'] = session_PNL
        print('\nAOA : *$*$*$*$*$*     Current Session PNL: ' + str('{0:.8f}'.format(session_PNL)) + ' BTC    *$*$*$*$*$*')
        print('AOA : *$*$*$*$*$*     Current Session PNL: $' + str(session_PNL_in_USD) + '             *$*$*$*$*$*\n')
        self.AP.playSound('Buffy Theme Song Ending Drumroll TRIMMED')
        self.previousPositionDict = {'Amount': 0}
        self.currentPositionLog = {'Entry Amount Closed': 0, \
                                   'Exit Amount Closed': 0, \
                                   'Entry Amount Rebuilt': 0}
        

# This will create the ArrayOrderAutomator class in a non-local scope, making it more secure
if __name__ == "__main__":
    main()
