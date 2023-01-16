# -*- coding: utf-8 -*-

# Import required packages
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd
from pylab import cm
import tkinter as tk
from tkinter.filedialog import askopenfilenames
#from tkinter.filedialog import askdirectory

# Edit the font, font size, and axes width
#mpl.rcParams['font.family'] = 'Avenir'
plt.rcParams['font.size'] = 18
plt.rcParams['axes.linewidth'] = 2

# Generate 2 colors from the 'Dark2' ColorBrewer colormap
#colors = cm.get_cmap('Dark2', 2)

# Create interface, hide main window, ask for file selection
root = tk.Tk()
root.withdraw()

files_paths = askopenfilenames(filetypes=[("EC-Lab Text Format", ".mpt")],title='Choose the files to plot')
#dir_path = askdirectory()
#for root, dirs, files in os.walk(dir_path):
#    for file in files:
#        if file.endswith(".mpt"):
#             print(os.path.join(root, file))
for file_path in files_paths:
    print(file_path)

    # Loop the data lines to find the row where the data starts, which is when the number of tabulations stops increasing
    with open(file_path, 'r') as temp_f:
        column_count_prev = 0
        first_large_row = 0
        skiprows_list = []
        reference_found = False
        for i, line in enumerate(temp_f.readlines()):
            # Count the column count for the current line
            column_count = len(line.split('\t')) + 1
    
            # Set the new most column count
            first_large_row = i if column_count > column_count_prev else first_large_row
            
            column_count_prev = column_count
            
            # remove lines with mode 3 which is open circuit, which typically happens when the safety limit is passed
            if line[0] == '3':
                skiprows_list.append(i)
                # exclude also a couple of rows after the error
                skiprows_list.append(i+1)
                skiprows_list.append(i+2)
            if not reference_found:
                if line[0:19] == 'Reference electrode':
                    reference_found = True
                    reference = line[22:]
                    print(reference)
    # Close file
    temp_f.close()
    
    skiprows_list.extend(range(first_large_row))
    # skip also a few of the first points, as they are usually just transients
    skiprows_list.extend(range(first_large_row+1,first_large_row+10))
    
    
    # Use numpy.loadtxt to import our data
    #mode,ox_red,error,control_changes,time_s,control_V,Ewe_V,I_mA,Q_C,I_Range,Ece_V,Rcmp_Ohm,Analog_OUT_V,P_W,Ewe_Ece_V = np.loadtxt(file_path, unpack=True, delimiter='\t', skiprows=74)
    
    df = pd.read_csv(file_path, sep='\t', decimal=',', skiprows=lambda x: x in skiprows_list)
    # remove lines with mode 3 which is open circuit, which typically happens when the safety limit is passed
    #df = df_all[df_all.mode.eq(2)] do not work because mode has special meaning seems
    #df = df_all[df_all['mode']==2]
        
    # Create figure and add axes object
    #fig = plt.figure(figsize=(3.5, 3.5))
    fig = plt.figure(figsize=(7.2, 4.5))
    
    ax = fig.add_axes([0, 0, 1, 1])
    
    # Plot and show our data
    x=df['Ewe/V']
    y=df['<I>/mA']
    #ax.plot(x, y, linewidth=2, color=colors(0), label='Sample 1')
    # Create a set of line segments so that we can color them individually
    # This creates the points as a N x 1 x 2 array so that we can stack points
    # together easily to get the segments. The segments array for line collection
    # needs to be (numlines) x (points per line) x 2 (for x and y)
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # Create a continuous norm to map from data points to colors
    norm = plt.Normalize(0, len(x))
    lc = LineCollection(segments, cmap='rainbow', norm=norm)
    # Set the values used for colormapping
    lc.set_array(np.array(range(len(x))))
    lc.set_linewidth(2)
    line = ax.add_collection(lc)
    ax.set_xlim(x.min()-0.02*(x.max()-x.min()), x.max()+0.02*(x.max()-x.min()))
    ax.set_ylim(y.min()-0.05*(y.max()-y.min()), y.max()+0.05*(y.max()-y.min()))
    
    
    #ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(100))
    #ax.xaxis.set_minor_locator(mpl.ticker.MultipleLocator(50))
    #ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(0.5))
    #ax.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(0.25))
    ax.xaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', top='on')
    ax.xaxis.set_tick_params(which='minor', size=4, width=1, direction='in', top='on')
    ax.yaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', right='on')
    ax.yaxis.set_tick_params(which='minor', size=4, width=1, direction='in', right='on')
    
    # Add the x and y-axis labels
    if reference_found:
        ax.set_xlabel('Ewe/V vs. ' + reference, labelpad=10)
    else:
        ax.set_xlabel('Ewe/V', labelpad=10)   
    ax.set_ylabel('Current/mA', labelpad=10)
    plt.savefig(file_path+'.pdf',bbox_inches='tight')
    
    plt.show()
    
