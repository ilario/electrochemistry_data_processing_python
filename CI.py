#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import required packages
import numpy as np
import pandas as pd
from tkinter.filedialog import askopenfilename
from sklearn.linear_model import LinearRegression

def get_resistance(*args):
    if len(args) == 1:
        file_path = args[0]
    else:
        file_path = askopenfilename(filetypes=[("EC-Lab Text Format", ".mpt")],title='Choose the CI file to analyse')
    
    print(file_path)
    # Loop the data lines to find the row where the data starts, which is when the number of tabulations stops increasing
    with open(file_path, 'r', encoding='latin-1') as temp_f:
        column_count_prev = 0
        first_long_row = 0
        
        lines = temp_f.readlines()
        for i, line in enumerate(lines):
            # Count the column count for the current line
            column_count = len(line.split('\t')) + 1
    
            # Set the new most column count
            first_long_row = i if column_count > column_count_prev else first_long_row
            
            column_count_prev = column_count
            
        #take the last line and check if the decimal separator is comma or period
        if ',' in lines[i]:
            decimal_separator = ','
        else:
            decimal_separator = '.'
            
    # Close file
    temp_f.close()
    skiprows_list = []
    skiprows_list.extend(range(first_long_row))
    
    df = pd.read_csv(file_path, sep='\t', decimal=decimal_separator, skiprows=lambda x: x in skiprows_list)
        
    # Plot and show our data
    potential=df['Ewe/V']
    current=df['I/mA']*1000
    time=df['time/s']
    controlCurrent=df['control/mA']
    dControlCurrent=np.diff(controlCurrent)
    currentStepsIndexes = np.nonzero(dControlCurrent)
    resistance_arr = []
    resistance_original_arr = []
    
    for j, i in enumerate(np.nditer(currentStepsIndexes)):
        resistance_original=(potential[i]-potential[i+1])/(current[i]-current[i+1])
        resistance_original_arr.append(resistance_original)
        # x should be provided vertical, reshape does this
        if resistance_original > 0:
            start = 1
        else:
            # if the first potential point is affected by some inductive affect causing a negative resistance, skip it
            start = 2

        x = np.array(time[(i+start):(i+7)]).reshape((-1, 1))
        y = np.array(potential[(i+start):(i+7)])
        
    #    print("x")
    #    print(x)
    #    print("y")
    #    print(y)
    #    print("x[1:2]")
    #    print(x[0:1])
        model = LinearRegression()
        model.fit(x, y)
        y_pred = model.predict(x[0:1])[0]
    #    print("y_pred")
    #    print(y_pred)
        resistance_arr.append((potential[i]-y_pred)/(current[i]-current[i+1]))
    
    resistance_mean = sum(resistance_arr)/len(resistance_arr)
    resistance_original_mean = sum(resistance_original_arr)/len(resistance_original_arr)
    resistance_std = np.std(resistance_arr)
    resistance_original_std = np.std(resistance_original_arr)
    
    print("Standard CI would say " + str(resistance_original_mean) + 
          " ohm with STD of " + str(resistance_original_std) + 
          " ohm. Fitting says " + str(resistance_mean) + " ohm with STD of " + 
          str(resistance_std) + " ohm.")
    return(resistance_mean)
