#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Import required packages
import os
import matplotlib.pyplot as plt
import pandas as pd
from pylab import cm
import tkinter as tk
from tkinter.filedialog import askopenfilenames
from tkinter import simpledialog
import re
import sys
import configparser
import CI

# Edit the font, font size, and axes width
plt.rcParams['font.size'] = 18
plt.rcParams['axes.linewidth'] = 2

config = configparser.ConfigParser()

if len(sys.argv) > 1:
    #with open(sys.argv[1], 'r') as batch_f:
    config_file = sys.argv[1]
else:
    config_file = askopenfilenames(filetypes=[("EC scripts configuration", ".ini")],title='Choose the configuration file or skip')

if config_file:
    config.read(config_file)
    files_paths = config.sections()
    reference_string = config['DEFAULT']['reference_string']
    color_scheme = config['DEFAULT']['color_scheme']

# Create interface, hide main window, ask for file selection
root = tk.Tk()
root.withdraw()

if not 'files_paths' in locals():
    files_paths = askopenfilenames(filetypes=[("EC-Lab Text Format", ".mpt")],title='Choose the files to plot')
if not len(files_paths):
    sys.exit()

# Generate the full colors from the 'Dark2' ColorBrewer colormap
color_scheme = simpledialog.askstring('Set color scheme','Qualitative color schemes: Pastel1, Pastel2, Paired, Accent, Dark2, Set1, Set2, Set3, tab10, tab20, tab20b, tab20c', initialvalue='tab20')
colors = cm.get_cmap(color_scheme)

# Create figure and add axes object
#fig = plt.figure(figsize=(3.5, 3.5))#one column
fig = plt.figure(figsize=(7.2, 4.5))#full width

ax = fig.add_axes([0, 0, 1, 1])
xmin=1000
xmax=-1000
ymin=1000
ymax=-1000
color_index = -1
reference_string = ''
reference_new = 'unset'

for j,file_path in enumerate(files_paths):
    print(file_path)
    resistance = CI.get_resistance(file_path)
    # Loop the data lines to find the row where the data starts, which is when the number of tabulations stops increasing
    with open(file_path, 'r', encoding='latin-1') as temp_f:
        column_count_prev = 0
        first_data_row = 0
        first_long_row = 0
        reference_found = False
        surface_found = False
        lines = temp_f.readlines()
        for i, line in enumerate(lines):
            # Count the column count for the current line
            column_count = len(line.split('\t')) + 1
    
            # Set the new most column count
            first_long_row = i if column_count > column_count_prev else first_long_row
            
            column_count_prev = column_count
            
            # remove lines with mode 3 which is open circuit, which typically happens when the safety limit is passed
            if line[0] == '3':
                first_data_row = i
            if not reference_found:
                if line[0:19] == 'Reference electrode':
                    reference_found = True
                    try:
                        reference_fromfile = re.search('(.+) \((.+) V\)',line[22:])
                        reference_suggested = reference_fromfile.group(1)
                        reference_original = reference_fromfile.group(2).replace(',','.')
                    except AttributeError:
                        reference_string = ''
                        reference_original = 0

            if not surface_found:
                if line[0:22] == 'Electrode surface area':
                    surface_found = True
                    surface = float(line[25:30].replace(',','.'))
            
        #take the last line and check if the decimal separator is comma or period
        if ',' in lines[i]:
            decimal_separator = ','
        else:
            decimal_separator = '.'
            
    # Close file
    temp_f.close()
    
    file_name = os.path.basename(file_path)
    try:
        label_suggested = re.search('-(.+)-.+?_\d\d_LSV', file_name).group(1)
    except AttributeError:
        label_suggested = file_name

    label_suggested = label_suggested.replace('_', ' ').replace('-', ', ')
    label_suggested = re.sub(r'([a-zA-Z])(\d+)', '\g<1>$_{\g<2>}$', label_suggested)

    label_string = simpledialog.askstring('Set legend entry','Legend entry for '+file_name, initialvalue=label_suggested)
    label_string_nosub = label_string.replace('$_{','').replace('}$','')

    surface = simpledialog.askfloat('Set working electrode surface area','Electrode surface area in cm2 for '+label_string_nosub, initialvalue=surface)
    
    reference_original = simpledialog.askfloat('Set reference electrode potential','Potential of employed reference electrode for '+file_name, initialvalue=reference_original)

    resistance = simpledialog.askfloat('Set resistance for iR correction','Resistance for iR correction of '+file_name, initialvalue=0)
    
    if not reference_string: # or reference_new == float("NaN"):
        reference_string = simpledialog.askstring('Set reference electrode name','Name of the wanted reference potential for '+label_string_nosub, initialvalue=reference_suggested)

    reference_new = simpledialog.askfloat('Set wanted reference potential','Wanted potential reference for '+label_string_nosub, initialvalue=reference_new if isinstance(reference_new, float) else reference_original)

    color_index = simpledialog.askinteger('Set index of color','Color index for '+label_string_nosub, initialvalue=color_index+1)

for j,file_path in enumerate(files_paths):
    skiprows_list = []
    skiprows_list.extend(range(first_long_row))
    # skip also a few of the first points, as they are usually just transients
    skiprows_list.extend(range(first_long_row+1,first_data_row+10))

    df = pd.read_csv(file_path, sep='\t', decimal=decimal_separator, skiprows=lambda x: x in skiprows_list)
        
    # Plot and show our data
    potential=df['Ewe/V']
    current=df['<I>/mA']
    x=(potential + reference_original - reference_new) - (resistance*current/1000)
    y=current/surface

    ax.plot(x, y, linewidth=3, color=colors(color_index), label=label_string)#alpha=0.8)
    xmin = x.min() if x.min() < xmin else xmin
    xmax = x.max() if x.max() > xmax else xmax
    ymin = y.min() if y.min() < ymin else ymin
    ymax = y.max() if y.max() > ymax else ymax
    
ax.xaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', top='on')
ax.xaxis.set_tick_params(which='minor', size=4, width=1, direction='in', top='on')
ax.yaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', right='on')
ax.yaxis.set_tick_params(which='minor', size=4, width=1, direction='in', right='on')

# Add the x and y-axis labels
if reference_string:
    ax.set_xlabel('E$_{WE}$ [V] vs. ' + reference_string, labelpad=10)
else:
    ax.set_xlabel('E$_{WE}$ [V]', labelpad=10)   
ax.set_ylabel('Current [mA/cm$^2$]', labelpad=10)

ax.set_xlim(xmin-0.02*(xmax-xmin), xmax+0.02*(xmax-xmin))
ax.set_ylim(ymin-0.05*(ymax-ymin), ymax+0.05*(ymax-ymin))

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels)

filename = os.path.basename(os.path.dirname(files_paths[0]))+'-LSV'
plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'.png'),bbox_inches='tight', dpi=300)
try:
    plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'.pdf'),bbox_inches='tight')
except PermissionError:
    plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'-RENAME_ME.pdf'),bbox_inches='tight')
    print('THE REQUESTED FILE NAME WAS UNAVAILABLE, SAVED WITH RENAME_ME SUFFIX INSTEAD')
plt.show()

