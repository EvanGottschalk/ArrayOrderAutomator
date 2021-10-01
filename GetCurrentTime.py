# PURPOSE - This program is for retrieving and converting time data to make it more legible

from datetime import *
import sched, time

class GetCurrentTime:
    def __init__(self):
        self.silentMode = True
        self.monthLengths = {'Jan': 31, \
                             'Feb': 28, \
                             'FebL': 29, \
                             'Mar': 31, \
                             'Apr': 30, \
                             'May': 31, \
                             'Jun': 30, \
                             'Jul': 31, \
                             'Aug': 31, \
                             'Sep': 30, \
                             'Oct': 31, \
                             'Nov': 30, \
                             'Dec': 31}
        self.monthNames = {'01': 'Jan', \
                           '02': 'Feb', \
                           '03': 'Mar', \
                           '04': 'Apr', \
                           '05': 'May', \
                           '06': 'Jun', \
                           '07': 'Jul', \
                           '08': 'Aug', \
                           '09': 'Sep', \
                           '10': 'Oct', \
                           '11': 'Nov', \
                           '12': 'Dec'}
        self.timestamp_starting_dates = {'Kraken': '1970-01-01'}
        self.timestamp_timezone_adjustments_EST = {'Kraken': -4}


    def getTimeString(self):
        currentTime = str(datetime.now())
        self.currentTimeString = currentTime.split(':')[0].split(' ')[1] + ':' + currentTime.split(':')[1] + '.' + \
                                 currentTime.split(':')[2].split('.')[0]
        return(self.currentTimeString)

    def getHourString(self):
        currentTime = str(datetime.now())
        currentHourString = currentTime.split(':')[0].split(' ')[1]
        return(currentHourString)

    def getMinuteString(self):
        currentTime = str(datetime.now())
        currentMinuteString = currentTime.split(':')[1]
        return(currentMinuteString)

    def getSecondString(self):
        currentTime = str(datetime.now())
        currentSecondString = str(int(float(currentTime.split(':')[2])))
        return(currentSecondString)

    def getDateString(self):
        currentTime = str(datetime.now())
        self.currentTimeString = currentTime.split(' ')[0]
        return(self.currentTimeString)

    def getDateTimeString(self):
        currentTime = str(datetime.now())
        year = currentTime.split('-')[0]
        month = currentTime.split('-')[1]
        day = currentTime.split('-')[2].split(' ')[0]
        time = currentTime.split(' ')[1].split('.')[0]
        time = time.split(':')[0] + '-' + time.split(':')[1] + '-' + time.split(':')[2]
        self.currentTimeString = month + '-' + day + '-' + year + ' ' + time
        return(self.currentTimeString)

    def getTimeStamp(self):
        self.currentTimeStamp = time.time()
        return(self.currentTimeStamp)

    def convert_TimeStampToDate(self, timeStamp):
        valid_conversion = False
        while(not(valid_conversion)):
            current_timeStamp = self.getTimeStamp()
            current_Date = self.getDateString()   
            timeDifference_Seconds = current_timeStamp - timeStamp
            timeDifference_Minutes = timeDifference_Seconds / 60
            timeDifference_Hours = timeDifference_Minutes / 60
            timeDifference_Days = int(timeDifference_Hours / 24)
            if timeDifference_Days > 0:
                convertedDate = self.decreaseDate(current_Date, timeDifference_Days)
            else:
                convertedDate = self.increaseDate(current_Date, timeDifference_Days)
            if '--' in convertedDate:
                timeStamp = timeStamp / 1000
            else:
                valid_conversion = True
        return(convertedDate)

    def convert_TimeStampToDateTime(self, timestamp, *args):
    # The date is determined based on which exchange's timestamp is being used
        try:
            exchange_name = args[0]['Exchange Name']
        except:
            exchange_name = 'Kraken'
        if str(timestamp)[len(str(timestamp)) - 3] == '0' and str(timestamp)[len(str(timestamp)) - 2] == '0' and str(timestamp)[len(str(timestamp)) - 1] == '0':
            timestamp = int(timestamp / 1000)
        starting_date = self.timestamp_starting_dates[exchange_name]
        days = int(timestamp / 86400)
        date_string = self.increaseDate(starting_date, days)
        date_string = self.YYYYMMDD_to_MMDDYYYY(date_string)
        days_remainder = timestamp % 86400
    # Hours are calculated and modified based on the timezone of the exchange vs. our timezone
        hours = int(days_remainder / 3600)
        hours = hours + self.timestamp_timezone_adjustments_EST[exchange_name]
        if len(str(hours)) == 1:
            hour_string = '0' + str(hours)
        else:
            hour_string = str(hours)
        hours_remainder = days_remainder % 3600
    # Minutes are calculated
        minutes = int(hours_remainder / 60)        
        if len(str(minutes)) == 1:
            minute_string = '0' + str(minutes)
        else:
            minute_string = str(minutes)
        date_time_string = date_string + ' ' + hour_string + ':' + minute_string
        return(date_time_string)

    def YYYYMMDD_to_MMDDYYYY(self, date):
        new_date = date.split('-')[1] + '-' + date.split('-')[2] + '-' + date.split('-')[0]
        return(new_date)
        
    
    def increaseDate(self, *args):
    # Default for no args is user input
        if len(args) == 0:
            date = '?'
            amount = '?'
    # Default for 1 arg is to increase the date by 1
        elif len(args) == 1:
            date = args[0]
            amount = 1
        elif len(args) == 2:
            date = args[0]
            amount = args[1]
        while date == '?':
            date = input('What date would you like to increase?')
        while amount == '?':
            amount = input('By what amount would you like to increase the date?')
        date_year = date.split('-')[0]
        date_month = date.split('-')[1]
        date_day = date.split('-')[2]
        increased_day = date_day
        increased_month = date_month
        increased_year = date_year
        month_name = self.monthNames[date_month]
        if month_name == 'Feb':
            if self.checkLeapYear(date_year):
                month_name = 'FebL'
        max_day = self.monthLengths[month_name]
        if not(self.silentMode):
            print('Starting Day: ' + date_day + '\n' + \
                  'Starting Month: ' + date_month + '\n' + \
                  'Starting Year: ' + date_year)
        increased_day = int(date_day) + amount
        while int(increased_day) > int(max_day):
            increased_day -= max_day
            increased_month = ((2 - len(str(int(increased_month) + 1))) * '0') + str(int(increased_month) + 1)
            if increased_month == '13':
                increased_month = '01'
                increased_year = str(int(increased_year) + 1)
            month_name = self.monthNames[increased_month]
            if month_name == 'Feb':
                if self.checkLeapYear(increased_year):
                    month_name = 'FebL'
            max_day = self.monthLengths[month_name]
        increased_day = ((2 - len(str(int(increased_day)))) * '0') + str(int(increased_day))
        increased_date = increased_year + '-' + increased_month + '-' + increased_day
        if not(self.silentMode):
            print('Increased Day: ', increased_day)
            print('Increased Month: ', increased_month)
            print('Increased Year: ', increased_year)
            print('\nIncreased Date: ', increased_date)
        return(increased_date)
        

    def decreaseDate(self, *args):
    # Default for no args is user input
        if len(args) == 0:
            date = '?'
            amount = '?'
    # Default for 1 arg is to increase the date by 1
        elif len(args) == 1:
            date = args[0]
            amount = 1
        elif len(args) == 2:
            date = args[0]
            amount = args[1]
        while date == '?':
            date = input('What date would you like to decrease?')
        while amount == '?':
            amount = input('By what amount would you like to decrease the date?')
        date_year = date.split('-')[0]
        date_month = date.split('-')[1]
        date_day = date.split('-')[2]
        decreased_day = int(date_day)
        decreased_month = date_month
        decreased_year = date_year
        month_name = self.monthNames[date_month]
        if month_name == 'Feb':
            if self.checkLeapYear(date_year):
                month_name = 'FebL'
        if not(self.silentMode):
            print('Starting Day: ' + date_day + '\n' + \
                  'Starting Month: ' + date_month + '\n' + \
                  'Starting Year: ' + date_year)
        amount_decreased = 0
        while amount_decreased < amount:
            decreased_day -= 1
            amount_decreased += 1
            if decreased_day <= 0:
                decreased_month = ((2 - len(str(int(decreased_month) - 1))) * '0') + str(int(decreased_month) - 1)
                if '00' in decreased_month:
                    decreased_month = '12'
                    decreased_year = str(int(decreased_year) - 1)
                month_name = self.monthNames[decreased_month]
                if month_name == 'Feb':
                    if self.checkLeapYear(decreased_year):
                        month_name = 'FebL'
                decreased_day = self.monthLengths[month_name]
        decreased_day = ((2 - len(str(int(decreased_day)))) * '0') + str(int(decreased_day))
        decreased_date = decreased_year + '-' + decreased_month + '-' + str(decreased_day)
        if not(self.silentMode):
            print('Decreased Day: ', decreased_day)
            print('Decreased Month: ', decreased_month)
            print('Decreased Year: ', decreased_year)
            print('\nDecreased Date: ', decreased_date)
        return(decreased_date)

    def checkLeapYear(self, year):
        leapYear = False
        year = int(year)
        if year % 4 == 0:
            if not(self.silentMode):
                print('LEAP! This year is  ||divisible by 4||  so it is probably a leap year:', year)
            leapYear = True
            if year % 100 == 0:
                if not(self.silentMode):
                    print("LEAP! Actually, this year is also  ||divisible by 100||  so it's probably not a leap year!")
                leapYear = False
                if year % 400 == 0:
                    if not(self.silentMode):
                        print('LEAP! Actually, this year is also  ||divisible by 400||  so it IS a leap year!')
                    leapYear = True
        return(leapYear)

