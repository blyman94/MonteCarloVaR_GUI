# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 15:33:27 2020

@author: Brandon C Lyman
"""
import sys
import os
import pandas_datareader.data as web
import pandas as pd
import numpy as np
import datetime as dt
from scipy.stats import norm
from MCVaR_Widgets import (PredWindowSelect,HistWindowSelect,TickerSelect,
                           MCParamSelect)
from PyQt5.QtWidgets import (QApplication, QDesktopWidget, QWidget, 
                             QGridLayout, QPushButton, QMessageBox)
from PyQt5 import QtGui

ROOT = os.path.dirname(os.path.realpath(__file__)) + '/'
FONT = 'Sans Serif'
FONTSIZE = 18

class MCVaRApp(QWidget):
    """Monte Carlo Value-at-Risk calculation with GUI"""
    def __init__(self):

        super().__init__()

        self.title = "Monte Carlo Value-at-Risk"
        self.setFont(QtGui.QFont(FONT,FONTSIZE)) 
        self.width = 400
        self.height = 400
        
        # Initialize Windouw UI
        self.gridMain = QGridLayout()
        self.initUI()
        self.setLayout(self.gridMain)
        
        # Display window on desktop
        self.center()
        self.show()
        
    def center(self):
        """Centers the main window on the desktop."""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def initUI(self):
        """Initialize User Interface
        """    
        self.setWindowTitle(self.title)
        self.setGeometry(0,0,self.width,self.height)
              
        # UI Elements
        self.hws = HistWindowSelect()
        self.pws = PredWindowSelect()
        self.hws.end_signal.connect(self.pws.setStart)
        self.hws.onEndDateChange()
        self.tickerSelect = TickerSelect()
        self.mcParamSelect = MCParamSelect()
        self.btnRun = QPushButton('Run Monte Carlo VaR')
        self.btnRun.clicked.connect(self.onClickRun)
        self.btnExport = QPushButton('Export VaR Results')
        self.btnExport.clicked.connect(self.onClickExport)
        self.btnExport.setEnabled(False)
        
        # Grid Arrangement
        self.gridMain.addWidget(self.hws)
        self.gridMain.addWidget(self.pws)
        self.gridMain.addWidget(self.tickerSelect)
        self.gridMain.addWidget(self.mcParamSelect)
        self.gridMain.addWidget(self.btnRun)
        self.gridMain.addWidget(self.btnExport)
        
    def onClickRun(self):
        """Calculates value at risk for parameters given in the GUI.
        
        Calculates the sample mean (mu) and volatilty (sig) over a given 
        historical time period for the selected stock ticker. Uses Geometric 
        Brownian Motion GBM to predict stock price over a given prediction 
        window. Uses Monte Carlo simulation on GBM to generate a given number
        of trials. Uses VaR Confidence level (ex. 95%) and results of the 
        trials to produce a Value-at-Risk measurement for the stock ticker.
        
        """
        # User input from GUI
        self.ticker = self.tickerSelect.getTickerSelection()
        self.hstart,self.hend = self.hws.getDateWindow()
        self.trials, self.var_con = self.mcParamSelect.getMCParams()
        self.pstart,self.pend = self.pws.getDateWindow()
        self.days = self.pws.getNumDays()
        
        data = web.DataReader(self.ticker,'yahoo',
                              self.hstart, self.hend).reset_index()[['Adj Close']]
        returns = np.log(1-data.pct_change())
        
        p0 = data.iloc[-1].values
        mu = returns.mean().values
        sig = returns.std().values
        
        paths = []
        for i in range(self.trials):
            path = []
            for j in range(1,self.days + 2):
                e = norm.ppf(np.random.rand())
                if j == 1:
                    curr_price = p0
                else:
                    curr_price = curr_price + (mu*curr_price + sig*curr_price*e)
                path.append(curr_price)
            path = np.array(path)
            paths.append(path)
        self.path_array = np.hstack(paths)
        
        t_returns = self.path_array[self.days,:]
        
        self.var = np.max([p0-np.percentile(t_returns,(1-self.var_con)*100),0])
        self.btnExport.setEnabled(True)
        self.varCalcMessage()
    
    def varCalcMessage(self):
        "Displays the given parameters and calculated VaR in a popup window."
        with open(ROOT + 'messageText.txt', 'r') as f:
                varText = f.read() % (self.ticker,
                                      dt.datetime.strftime(self.hstart,'%d-%b-%Y'),
                                      dt.datetime.strftime(self.hend,'%d-%b-%Y'),
                                      dt.datetime.strftime(self.pstart,'%d-%b-%Y'),
                                      dt.datetime.strftime(self.pend,'%d-%b-%Y'),
                                      self.trials,int(self.var_con*100),
                                      self.var)
        
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(varText)
        msgBox.setWindowTitle("Monte Carlo VaR Calculation Status")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
     
        self.returnValue = msgBox.exec()
    
    def onClickExport(self):
        """If VaR has been calculated through the onClickRun function, exports
        the Monte Carlo trials, calculated VaR, and a line chart depicting the 
        path of each trial to Microsoft Excel.
        
        If there are more than 100 trials, the Excel chart would be unreadable.
        Therefore, one can only export if the trial number is less than 100.
        
        """
        if self.trials <= 100:
            # Excel Output
            delta = self.pend - self.pstart
            index = [self.pstart + dt.timedelta(days=x) for x in range(delta.days + 1)]
            for i in [5,6]:
                for date in index:
                    if date.weekday() == i:
                        index.remove(date)
            index = [dt.datetime.strftime(x,'%d-%b-%Y') for x in index]
            
            path_df = pd.DataFrame(self.path_array,index = index,columns = ['Trial ' + str(x + 1) for x in range(0,self.path_array.shape[1])])
            writer = pd.ExcelWriter('MCVaR_Ouput.xlsx', engine='xlsxwriter')
            path_df.to_excel(writer, sheet_name='trials')
            
            var_df = pd.DataFrame([['Value-at-Risk: '],[self.var]])
            var_df.to_excel(writer,sheet_name='trials',startcol=0,
                            startrow=self.days + 3, header=None,
                            index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['trials']
            chart = workbook.add_chart({'type': 'line'})
            for col in range(path_df.shape[1]):
                chart.add_series({
                    'name': 'Trial' + str(col+1),
                    'categories': ['trials',1,0,self.days + 1,0],
                    'values': ['trials',1,col+1,self.days + 1,col+1]})
            chart.set_x_axis({'position_axis': 'on_tick'})
            chart.set_legend({'none': True})
            chart.set_size({'x_scale': 2, 'y_scale': 2})
            chart.set_title({'name': 'Monte Carlo Value-at-Risk ' + self.ticker})
            
            worksheet.insert_chart(self.days + 6,0, chart)
            
            writer.save()
            
            self.exportMessage = 'Monte Carlo Results successfully exported to Excel!'
        else:
            self.exportMessage = 'Too many trials for export. Function supports a maximum of 100 trials.'
        
        self.exportMessageBox()
        
    def exportMessageBox(self):
        """A message box to alert the user if the VaR analysis was properly 
        exported to Excel, or if an issue has occured preventing the export."""
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText(self.exportMessage)
        msgBox.setWindowTitle("Monte Carlo VaR Calculation Status")
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
     
        self.returnValue = msgBox.exec()  
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = MCVaRApp()
    sys.exit(app.exec())