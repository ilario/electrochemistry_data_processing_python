#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ilario Gelmetti
"""
# Import required packages
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import EC_data_processing_lib as ec

def get_resistance(file_path):
    print(file_path)
    first_long_row, reference_suggested, reference_original, surface, decimal_separator, repetitions = ec.analyse_file(file_path)
    skiprows_list = list(range(first_long_row))
    df = pd.read_csv(file_path, sep='\t', decimal=decimal_separator, skiprows=lambda x: x in skiprows_list, encoding = 'iso-8859-1´)

    # Plot and show our data
    potential=df['Ewe/V']
    current=df['I/mA']/1000
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
    #    xa= np.array(time[int(i):(i+7)])
    #    ya= np.array(potential[int(i):(i+7)])
    #    print(xa)
    #    print(ya)
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
        resistance = (potential[i]-y_pred)/(current[i]-current[i+1])
#        print("Fitted CI: " + str(resistance))
        resistance_arr.append(resistance)
    
#    print(resistance_arr)
#    print(resistance_original_arr)
    #resistance_mean = sum(resistance_arr)/len(resistance_arr)
    resistance_1quartile = np.percentile(resistance_arr,25)
    resistance_original_mean = sum(resistance_original_arr)/len(resistance_original_arr)
    #resistance_std = np.std(resistance_arr)
    resistance_original_std = np.std(resistance_original_arr)
    #overall_mean = (resistance_original_mean/resistance_original_std**2 + resistance_mean/resistance_std**2)/(1/resistance_std**2 + 1/resistance_original_std**2)
    overall_mean = (resistance_original_mean + resistance_1quartile)/2
    print("--------------")
    #print("Standard CI would say " + str(resistance_original_mean) + 
    #      " ohm with STD of " + str(resistance_original_std) + 
    #      " ohm. Fitting says " + str(resistance_mean) + " ohm with STD of " + 
    #      str(resistance_std) + " ohm. Returning the weighted average of the two: " + str(overall_mean) + " ohm.")
    print("Standard CI would say " + str(resistance_original_mean) + 
          " ohm with STD of " + str(resistance_original_std) + 
          " ohm. Fitting says " + str(resistance_1quartile) +
          " ohm. Returning the average of the two: " + str(overall_mean) + " ohm.")
    return(overall_mean)
