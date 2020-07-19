# Simple Monte Carlo Value-at-Risk Calculation
Python implementation of Monte Carlo Value-at-Risk calculation for a single stock with PyQt5 GUI. 
This application allows the user to select the many parameters to calculate a simple Value-at-Risk
estimate of a single stock using Geometric Brownian Motion and Monte Carlo simulation. Parameters include:

    Historical Window: The historical window of analysis from which the stock's mean (mu) and volatility (sigma) is calculated. Minimum length: 22 weekdays.
    Prediction Window: The prediction window over which GBM will be simulated. VaR will be calculated on the final day based on the confidence level provided by the user.
    Stock Ticker Selection: Allows the user to select from a list of all tradeable stocks for analysis.
    Trials: The number of GBM paths to be simulated during Monte Carlo. Usually set to 1,000 or 10,000.
    VaR Confidence: The confidence level at which to calculate VaR.

The main script in the package is "MCVaR_gui.py". The scripts main function creates a MCVaRApp object which contains 
all elements of the Monte Carlo VaR application's user interface.
    
# Installation
"MCVaR_gui.py" is dependent on the following packages:

    Package           | Function
    ---------------------------------------------
    sys               | Interact with operating system to create applications.
    PyQt5             | Create windows, buttons, and other UI elements.
    pandas_datareader | Used to load stock ticker adjust stock price data.
    pandas            | DataFrame object and methods. Also used to write DataFrames and charts to Microsoft Excel.
    numpy             | Matrix calculations.
    os                | Directory management for file retrieval.
    datetime          | Datetime objects and methods.
    scipy.stats       | Used to draw values from the normal distribution based on a random variable for epsilon.
    MCVaR_Widgets     | A collection of widgets specific for the Monte Carlo VaR Calculation application (contained in this package).
    
In addition to the packages listed above, "MCVaR_Widgets.py" is dependent on the following packages:

    Package           | Function
    ---------------------------------------------
    shutil            | IHigh-level file operations. Used to as part of web-scraping procedure to gather list of available stock tickers.
    urllib.request    | Allows Python to download files from websites. Used as part of web-scraping procedure to gather list of available stock tickers.
    contextlib        | URL Context manager. Used as part of a web-scraping procedure to gather list of available stock tickers.
    
If there is an issue with importing these libraries, simply use the "pip" or "conda" command from the Python or Anaconda shell, respectively, to properly install them.

# Usage
With the proper Python environment installed, "MCVaR_gui.py" can be run simply by double clicking the file in Windows File Explorer.

The user may set the values for the parameters listed in the introduction. Two buttons are provided. One executes the Monte Carlo VaR procedure, the other exports the
results of the trials to Microsoft Excel.

# Changelog
    Version | Date       | Notes
    ------------------------------------------------------------
    1.0.0   | 07-19-2020 | First end-to-end implementation of
                           the Monte Carlo VaR Application for
                           this project.
    -------------------------------------------------------------
# Authors
Brandon C Lyman
