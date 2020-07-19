# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 14:32:10 2020

@author: Brandon C Lyman
"""

import os
import pandas as pd
import shutil
import datetime as dt
from datetime import timedelta
import urllib.request as request
from contextlib import closing
from PyQt5.QtWidgets import (QGridLayout, QGroupBox, QLabel, QDateEdit, 
                             QLineEdit,QCompleter, QComboBox)
from PyQt5 import QtCore

ROOT = os.path.dirname(os.path.realpath(__file__)) + '/'

class ExtendedComboBox(QComboBox):
    """An enhanced version of PyQt5's QComboBox widget that allows for search
    and filtering of the greater list. Implemented by armonge on StackOverflow,
    adapted for PyQt5 by Tamas Haver on StackOverflow.
    
    The Stackoverflow post can be found here:
        
    https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input
    
    """
    def __init__(self, parent=None):
        super(ExtendedComboBox, self).__init__(parent)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QtCore.QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())
        
        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.setCompleter(self.completer)

        # connect signals
        self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    def on_completer_activated(self, text):
        """On selection of an item from the completer, select the corresponding
        item from combobox.
        """
        if text:
            index = self.findText(text)
            self.setCurrentIndex(index)
            self.activated[str].emit(self.itemText(index))

    def setModel(self, model):
        """On model change, update the models of the filter and completer as 
        well.
        """
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer.setModel(self.pFilterModel)
 
    def setModelColumn(self, column):
        """On model column change, update the model column of the filter and 
        completer as well.
        """
        self.completer.setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column) 

class HistWindowSelect(QGroupBox):
    """An extension of the QGroupBox widget. It allows the user to select a
    start date and end date for the historical window in the Monte Carlo VaR
    calculation application.
    
    The end date of the historical window is set to 22 days from the start date
    as a minimum. This restriction is implemented through the QDateEdit's set
    minimum date function.
    """
    end_signal = QtCore.pyqtSignal(dt.datetime)
    
    def __init__(self,parent = None):
        super(HistWindowSelect,self).__init__(parent)
        
        self.setTitle('Historical Window Select')
        grid = QGridLayout()
        
        lbl_start = QLabel('Start Date: ')
        lbl_end = QLabel('End Date: ')
        
        self.deStart = QDateEdit()
        self.deStart.setCalendarPopup(True)
        self.deStart.setMinimumDateTime(dt.datetime(2015,1,1))
        self.deStart.setMaximumDateTime(self.getWeekdaysBack(dt.datetime.now(),22))
        self.deStart.dateChanged.connect(self.onStartDateChange)
        self.deEnd = QDateEdit()
        self.deEnd.setCalendarPopup(True)
        self.deEnd.setMaximumDateTime(dt.datetime.now())
        self.deEnd.dateChanged.connect(self.onEndDateChange)
        self.setEndDateMinimum()
        lbl_disc = QLabel('Note: A minimum historical window length <br>of 22 business days has been imposed.')
        
        grid.addWidget(lbl_start,0,0)
        grid.addWidget(lbl_end,1,0)
        grid.addWidget(self.deStart,0,1)
        grid.addWidget(self.deEnd,1,1)
        grid.addWidget(lbl_disc,2,1)
        
        self.setLayout(grid)
        
    def onStartDateChange(self):
        """Checks if new start date is a weekend. If so, it adds the 
        appropriate number of days to bring the start date to the following 
        Monday. After, it updates the minimum value of the end date, which must
        be 22 business days after the start date.
        """
        deStart = dt.datetime.combine(self.deStart.date().toPyDate(),
                                      dt.datetime.min.time())
        if deStart.weekday() == 5:
            deStart = deStart + timedelta(days = 2)
        elif deStart.weekday() == 6:
            deStart = deStart + timedelta(days = 1)
        
        self.deStart.setDate(deStart)
        self.setEndDateMinimum()
        
    def setEndDateMinimum(self):
        """Updates the minimum value of the end date, which must
        be 22 business days after the start date.
        """
        deStart = dt.datetime.combine(self.deStart.date().toPyDate(),
                                      dt.datetime.min.time())
        end_min = self.getWeekdaysOut(deStart,22)
        self.deEnd.setMinimumDateTime(end_min)
        if self.deEnd.date() < end_min:
            self.deEnd.setDate(end_min)
            self.test_signal.emit(end_min)
        
    def onEndDateChange(self):
        """Checks if new end date is a weekend. If so, it adds the 
        appropriate number of days to bring the end date to the following 
        Monday. After, it emits a signal containing the new end date to be
        picked up by a slot in the PredWindowSelect widget.
        """
        deEnd = dt.datetime.combine(self.deEnd.date().toPyDate(),
                                    dt.datetime.min.time())
        if deEnd.weekday() == 5:
            deEnd = deEnd + timedelta(days = 2)
        elif deEnd.weekday() == 6:
            deEnd = deEnd + timedelta(days = 1)
          
        self.deEnd.setDate(deEnd)
        self.end_signal.emit(deEnd)
        
    def getWeekdaysOut(self,start_date,days_out):
        """Finds the date that is x weekdays later than the start date (where
        x = days_out).
        
        Args:
            
            start_date (datetime.datetime) - Start date from which to count 
            weekdays out.
            
            days_out (int) - Number of days out.
            
        Returns:
            
            curr_date (datetime.datetime) - the date that is days_out weekdays
            later than start_date.
        
        Raises Error:
            
            None
        
        """
        if start_date.weekday() == 5:
                start_date += timedelta(days = 2)
        if start_date.weekday() == 6:
            start_date += timedelta(days = 1)
    
        for i in range(days_out):
            if i == 0:
                curr_date = start_date
            next_date = curr_date + timedelta(days = 1)
            if next_date.weekday() == 5:
                next_date = curr_date + timedelta(days = 3)
            curr_date = next_date
        
        return(curr_date)
    
    def getWeekdaysBack(self,start_date,days_back):
        """Finds the date that is x weekdays earlier than the start date (where
        x = days_back).
        
        Args:
            
            start_date (datetime.datetime) - Start date from which to count 
            weekdays out.
            
            days_back (int) - Number of days back.
            
        Returns:
            
            curr_date (datetime.datetime) - the date that is days_back weekdays
            earlier than start_date.
        
        Raises Error:
            
            None
        
        """
        if start_date.weekday() == 5:
            start_date -= timedelta(days = 1)
        if start_date.weekday() == 6:
            start_date -= timedelta(days = 2)
            
        for i in range(days_back):
            if i == 0:
                curr_date = start_date
            next_date = curr_date - timedelta(days = 1)
            if next_date.weekday() == 6:
                next_date = curr_date - timedelta(days = 3)
            curr_date = next_date
        
        return(curr_date)
    
    def getDateWindow(self):
        """Getter function for the date window selected by the user.
        """
        start_date = dt.datetime.combine(self.deStart.date().toPyDate(),
                                         dt.datetime.min.time())
        end_date = dt.datetime.combine(self.deEnd.date().toPyDate(),
                                       dt.datetime.min.time())
        return start_date,end_date
    
class MCParamSelect(QGroupBox):
    """An extension of the QGroupBox widget that allows the user to select the 
    parameters of the Monte Carlo simulation (the VaR percentage and the
    number of trials.)
    """
    def __init__(self, parent = None):
        super(MCParamSelect,self).__init__(parent)
        
        self.setTitle('MC Parameter Selection')
        grid = QGridLayout()
        
        lbl_tc = QLabel('Trial Count: ')
        lbl_vc = QLabel('VaR Confidence Level: ')
        
        self.leTrials = QLineEdit('100')
        self.leVaRCon = QLineEdit('0.95')
        
        grid.addWidget(lbl_tc,0,0)
        grid.addWidget(self.leTrials,0,1)
        grid.addWidget(lbl_vc,0,2)
        grid.addWidget(self.leVaRCon,0,3)
        
        self.setLayout(grid)
        
    def getMCParams(self):
        """Getter function for the Monte Carlo parameters set by the user.
        """
        return int(self.leTrials.text()),float(self.leVaRCon.text())

class PredWindowSelect(QGroupBox):
    """An extension of the QGroupBox widget. It allows the user to select a
    start date and end date for the prediction window in the Monte Carlo VaR
    calculation application.
    
    The start date of the prediction window is set to the end date of the 
    historical window. The end date of the prediction window is five days later
    than the start date of the prediction window as a minimum. These 
    restrictions are implemented through the QDateEdit widget's maximum and 
    minimum date functions.
    """
    def __init__(self,parent = None):
        super(PredWindowSelect,self).__init__(parent)
        
        self.setTitle('Prediction Window Select')
        grid = QGridLayout()
        
        lbl_start = QLabel('Start Date: ')
        lbl_end = QLabel('End Date: ')
        
        self.deStart = QDateEdit()
        self.deStart.setEnabled(False)
        self.deStart.setCalendarPopup(True)
        self.deStart.dateChanged.connect(self.setEndDateMinimum)
        self.deEnd = QDateEdit()
        self.deEnd.setCalendarPopup(True)
        self.deEnd.dateChanged.connect(self.onEndDateChange)
        self.setEndDateMinimum()
        lbl_disc = QLabel('Note: A minimum prediction window length <br>of 5 business days has been imposed.')
        
        grid.addWidget(lbl_start,0,0)
        grid.addWidget(lbl_end,1,0)
        grid.addWidget(self.deStart,0,1)
        grid.addWidget(self.deEnd,1,1)
        grid.addWidget(lbl_disc,2,1)

        self.setLayout(grid)
        
    @QtCore.pyqtSlot(dt.datetime)
    def setStart(self,date):
        """Slotted function to set the start date based on end date of the 
        historical window.
        """
        self.deStart.setDate(date)
      
    def onEndDateChange(self):
        """Checks if new end date is a weekend. If so, it adds the 
        appropriate number of days to bring the end date to the following 
        Monday.
        """
        deEnd = dt.datetime.combine(self.deEnd.date().toPyDate(),
                                    dt.datetime.min.time())
        if deEnd.weekday() == 5:
            deEnd = deEnd + timedelta(days = 2)
        elif deEnd.weekday() == 6:
            deEnd = deEnd + timedelta(days = 1)
        
        self.deEnd.setDate(deEnd)
    
    def setEndDateMinimum(self):
        """Updates the minimum value of the end date, which must
        be 5 business days after the start date.
        """
        deStart = dt.datetime.combine(self.deStart.date().toPyDate(),
                                      dt.datetime.min.time())
        end_min = self.getWeekdaysOut(deStart,5)
        self.deEnd.setMinimumDateTime(end_min)
        if self.deEnd.date() < end_min:
            self.deEnd.setDate(end_min)
            
    def getWeekdaysOut(self,start_date,days_out):
        """Finds the date that is x weekdays later than the start date (where
        x = days_out).
        
        Args:
            
            start_date (datetime.datetime) - Start date from which to count 
            weekdays out.
            
            days_out (int) - Number of days out.
            
        Returns:
            
            curr_date (datetime.datetime) - the date that is days_out weekdays
            later than start_date.
        
        Raises Error:
            
            None
        
        """
        if start_date.weekday() == 5:
            start_date += timedelta(days = 2)
        if start_date.weekday() == 6:
            start_date += timedelta(days = 1)
    
        for i in range(days_out):
            if i == 0:
                curr_date = start_date
            next_date = curr_date + timedelta(days = 1)
            if next_date.weekday() == 5:
                next_date = curr_date + timedelta(days = 3)
            curr_date = next_date
        
        return(curr_date)
    
    def getDateWindow(self):
        """Getter function for the date window selected by the user.
        """
        start_date = dt.datetime.combine(self.deStart.date().toPyDate(),
                                         dt.datetime.min.time())
        end_date = dt.datetime.combine(self.deEnd.date().toPyDate(),
                                       dt.datetime.min.time())
        return start_date,end_date
    
    def getNumDays(self):
        """Getter function for the number of weekdays between the start and
        end dates."""
        start_date = dt.datetime.combine(self.deStart.date().toPyDate(),
                                         dt.datetime.min.time())
        end_date = dt.datetime.combine(self.deEnd.date().toPyDate(),
                                       dt.datetime.min.time())
        
        if start_date.weekday() == 5:
            start_date += timedelta(days = 2)
        if start_date.weekday() == 6:
            start_date += timedelta(days = 1)
            
        days = 0
        curr_date = start_date
        while curr_date != end_date:
            curr_date += timedelta(days = 1)
            if curr_date.weekday() == 5:
                continue
            elif curr_date.weekday() == 6:
                continue
            else:
                days +=1
            
        return days        
        
class TickerSelect(QGroupBox):
    """An extension of the QGroupBox widget that allows the user to select a 
    stock ticker from the available universe of stock tickers.
    """
    def __init__(self, parent = None):
        super(TickerSelect,self).__init__(parent)
        
        self.setTitle('Ticker Selection')
        grid = QGridLayout()
        
        # Define stock universe
        name_list,sym_list = self.ListAllStocks(shorten_name = True)
        
        lbl_ts = QLabel('Ticker: ')
        self.ecbSecurity = ExtendedComboBox()
        self.ecbSecurity.addItems(name_list)
        
        grid.addWidget(lbl_ts,0,0)
        grid.addWidget(self.ecbSecurity,0,1)
        
        self.setLayout(grid)
    
    def getTickerSelection(self):
        """Getter function for the stock ticker selected by the user.
        """
        full_name = str(self.ecbSecurity.currentText())
        return full_name.split(' - ')[0]
    
    def ListAllStocks(self,shorten_name = False):
        """List all tradeable stocks.
        
        Leverages nasdaqtrader.com's symbol directory API to download two text
        files in real time. Combined, the two lists represent all tradeable 
        stock tickers. Returns a list of string representing all of these 
        tickers.
        
        Args:
            
            None
            
        Returns:
            
            name_list (List) - A list of strings containing all tradeable stock 
            tickers and names separated by a hyphen.
            
            sym_list (List) - A list of strings containing all tradeable stock 
            tickers.
        
        Raises Error:
            
            None
        
        """
        def shortenStockName(stock_name,maxlength = 57):
            """Helper function to keep extra long stock names at a reasonable
            length
            """
            if len(stock_name) > maxlength:
                return stock_name[:maxlength] + '...'
            else:
                return stock_name
            
        url = 'ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt'
        with closing(request.urlopen(url)) as r:
            with open(ROOT + 'ticker_data/nasdaqlisted.txt', 'wb') as f:
                shutil.copyfileobj(r, f)
        url = 'ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt'
        with closing(request.urlopen(url)) as r:
            with open(ROOT + 'ticker_data/otherlisted.txt', 'wb') as f:
                shutil.copyfileobj(r, f)
                
        nasdaq = pd.read_csv(ROOT + 'ticker_data/nasdaqlisted.txt', sep = '|',
                             skipfooter = 1,engine = 'python')
        other = pd.read_csv(ROOT + 'ticker_data/otherlisted.txt', sep = '|',
                            skipfooter = 1,engine = 'python')

        name_list = (nasdaq['Symbol'] + ' - ' + nasdaq['Security Name']).tolist()
        name_list += (other['ACT Symbol'] + ' - ' + other['Security Name']).tolist()
        if shorten_name:
            name_list = [shortenStockName(x) for x in name_list]
        name_list = sorted(name_list)

        sym_list = nasdaq['Symbol'].tolist()
        sym_list += other['ACT Symbol'].tolist()
        sym_list = sorted(sym_list)
        return name_list,sym_list