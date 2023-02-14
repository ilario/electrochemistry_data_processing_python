#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ilario Gelmetti
"""
# Import required packages
import os
import matplotlib.pyplot as plt
import pandas as pd
from pylab import cm
import numpy as np #import diff,std,mean,array
from json import loads as jsonloads
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import simpledialog
from tkinter import messagebox
import re
import sys
import configparser
from EC_data_processing_lib import find_ci_mean_min
from EC_data_processing_lib import analyse_file
from EC_data_processing_lib import analyse_file_loop_number
from EC_data_processing_lib import find_outliers

# Edit the font, font size, and axes width
plt.rcParams['font.size'] = 14
plt.rcParams['axes.linewidth'] = 2

config = configparser.ConfigParser()

files_paths = []
config_file = ""
if len(sys.argv) == 2:
    config_file = sys.argv[1]
else:
    # Create interface, hide main window, ask for file selection
    root = tk.Tk()
    #try to take the window to foreground
    #root.lift()
    root.focus_force()
    #root.withdraw()

    #try again, specific for windows OS
    #root.wm_attributes('-topmost', 1)
    #root.after_idle(root.attributes,'-topmost',False)
    

    if len(sys.argv) > 2:
        for argument in sys.argv[1:]:
            files_paths.append(os.path.abspath(argument))
    else:
        config_file = askopenfilename(parent=root,filetypes=[("EC scripts configuration", ".ini")],title='Choose the configuration file or skip')
        #root.wm_attributes('-topmost', 0)
automated = False
if config_file:
    automated = True
    config.read(config_file)
    files_paths = config.sections()
elif not len(files_paths):
    while True:
        selected_file = askopenfilename(filetypes=[("EC-Lab Text Format", ".mpt")],title='Choose the file to plot')
        if selected_file:
            print(selected_file)
            files_paths.append(selected_file)
        else:
            break

if not len(files_paths):
    root.withdraw()
    sys.exit()

print(files_paths)

# Generate the full colors from the 'Dark2' ColorBrewer colormap
config['DEFAULT']['color_scheme'] = config['DEFAULT'].get('color_scheme') or simpledialog.askstring('Set color scheme','Qualitative color schemes: Pastel1, Pastel2, Paired, Accent, Dark2, Set1, Set2, Set3, tab10, tab20, tab20b, tab20c', initialvalue='tab20')
colors = cm.get_cmap(config['DEFAULT']['color_scheme'])

if config['DEFAULT'].get('xmin') and config['DEFAULT'].get('xmax'):
    axis_limits_preset_x = True
else:
    axis_limits_preset_x = False
if config['DEFAULT'].get('ymin') and config['DEFAULT'].get('ymax'):
    axis_limits_preset_y = True
else:
    axis_limits_preset_y = False

if not config['DEFAULT'].get('r_correct'):
    config['DEFAULT']['r_correct'] = str(simpledialog.askfloat('Resistance correction value','1 = full resistance correction, 0 = no resistance correction', initialvalue=1))
  
if not config['DEFAULT'].get('normalize_surface'):
    config['DEFAULT']['normalize_surface'] = str(messagebox.askyesno('Normalize current over surface','Do you want to plot the current over surface?'))

if not config['DEFAULT'].get('title'):
    config['DEFAULT']['title'] = simpledialog.askstring('Figure title','Which title should the figure have? Empty is allowed.')

if not config['DEFAULT'].get('current_unit'):
    config['DEFAULT']['current_unit'] = simpledialog.askstring('Units for the current','Which units should the current have? Allowed values are A, mA, uA, nA.', initialvalue='mA')

current_unit_string_dict = {'A':'A',
                            'mA':'mA',
                            'uA':'\muA',
                            'nA':'nA'}
current_unit_string = current_unit_string_dict.get(config['DEFAULT']['current_unit'])
current_unit_factor_dict = {'A':0.001,
                            'mA':1,
                            'uA':1000,
                            'nA':1000000}
current_unit_factor = current_unit_factor_dict.get(config['DEFAULT']['current_unit'])

# Create figure and add axes object
#base_size_horiz = 3.5 #one column
base_size_horiz = 7.2 #full width
base_size_vert = 4.5 #something reasonable
if not config['DEFAULT'].get('plot_tafel'):
    config['DEFAULT']['plot_tafel'] = str(messagebox.askyesno('Tafel plot','Do you want to plot also the Tafel plot?'))
if config['DEFAULT']['plot_tafel'] == 'True':
    fig = plt.figure(figsize=(base_size_horiz, base_size_vert*2))#two full width
else:
    fig = plt.figure(figsize=(base_size_horiz, base_size_vert))

if config['DEFAULT']['plot_tafel'] == 'True':
    ax = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
else:
    ax = fig.add_axes([0, 0, 1, 1])
xmin=1000000
xmax=-1000000
ymin=1000000
ymax=-1000000
color_index = []
theres_no_CV = True
prevReferenceNew = False
plt.axhline(y=0, color='lightgray', linestyle='-')

for j,identifier in enumerate(files_paths):
    # in the future, the identifier could be different from the file_path, for example if we want to plot the same file more than once
    file_path = identifier
    file_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)
    if "_CV_" in file_name:
        theres_no_CV = False

    try:
        label_suggested = re.search('-(.+)-.+?_\d\d_LSV', file_name).group(1)
    except AttributeError:
        label_suggested = file_name
    label_suggested = label_suggested.replace('_', ' ').replace('-', ', ')
    label_suggested = re.sub(r'([a-zA-Z])(\d+)', '\g<1>$_{\g<2>}$', label_suggested)
    
    print(file_path)
    if automated:
        config[identifier]['label_string'] = config[identifier].get('label_string') or label_suggested
        if not config[identifier]['r_correct'] == '0.0':
            config[identifier]['resistance'] =  config[identifier].get('resistance') or str(find_ci_mean_min(dir_name, file_name))
    else:
        first_long_row, reference_suggested, reference_original, surface, decimal_separator, repetitions = analyse_file(file_path)
        config[identifier] = {}
        #first_data_row, last_data_row, rows_count = analyse_file_loop_number(file_path, config[identifier].get('loop_number'))
        if not config['DEFAULT'].get('reference_string'):
            config['DEFAULT']['reference_string'] = simpledialog.askstring('Set reference electrode name','Name of the wanted reference potential', initialvalue=reference_suggested)
        config[identifier]['first_long_row'] = str(first_long_row)
        config[identifier]['decimal_separator'] = str(decimal_separator)
        config[identifier]['label_string'] = simpledialog.askstring('Set legend entry','Legend entry for '+file_name, initialvalue=label_suggested)   
        label_string_nosub = config[identifier]['label_string'].replace('$_{','').replace('}$','')
        if repetitions:
            config[identifier]['loop_number'] = str(simpledialog.askinteger('Loop number to plot','Which loop should be plotted, starting from zero up to ' + str(repetitions) + ', for '+label_string_nosub+' Beware that this is cycle number MINUS ONE.', initialvalue=repetitions))
        else:
            config[identifier]['loop_number'] = '0'
        if config['DEFAULT']['normalize_surface'] == 'True':
            config[identifier]['surface'] = str(simpledialog.askfloat('Set working electrode surface area','Electrode surface area in cm2 for '+file_name, initialvalue=surface))
        config[identifier]['reference_original'] = str(simpledialog.askfloat('Set reference electrode potential','Potential of employed reference electrode for '+file_name, initialvalue=reference_original))
        if not config['DEFAULT']['r_correct'] == '0.0':
            config[identifier]['resistance'] = str(simpledialog.askfloat('Set resistance for iR correction','Resistance for iR correction of '+file_name, initialvalue=find_ci_mean_min(dir_name, file_name)))
        config[identifier]['reference_new'] = str(simpledialog.askfloat('Set wanted reference potential','Wanted potential reference for '+label_string_nosub, initialvalue=float(prevReferenceNew or -float(config[identifier]['reference_original']))))
        prevReferenceNew = config[identifier]['reference_new']
        config[identifier]['color_index'] = str(simpledialog.askinteger('Set index of color','Color index for '+label_string_nosub, initialvalue=j))
        #config[identifier]['skip_points'] = str(skip_points)
    if not config[identifier].get('resistance'):
        print("RESISTANCE NOT CORRECTED!")
    
for j,identifier in enumerate(files_paths):
    # in the future, the identifier could be different from the file_path, for example if we want to plot the same file more than once
    file_path = identifier
    first_long_row = int(config[identifier]['first_long_row'])
    loop_number = int(config[identifier].get('loop_number') or -1)
    first_data_row, last_data_row, rows_count = analyse_file_loop_number(file_path, loop_number)
    #skip_points = jsonloads(config[identifier]['skip_points']) if config[identifier].get('skip_points') else []
    skiprows_list = list(range(first_long_row))# + skip_points
    # False and True are recognized both as int and as bool!
    if not isinstance(first_data_row, bool) and not isinstance(last_data_row, bool): 
        skiprows_list = skiprows_list + list(range(first_long_row+1,first_long_row+first_data_row+1)) + list(range(first_long_row+last_data_row, rows_count))
    print(file_path)
    df = pd.read_csv(file_path, sep='\t', decimal=config[identifier]['decimal_separator'], skiprows=lambda x: x in skiprows_list, encoding = 'iso-8859-1')
    
    if not loop_number == -1 and 'cycle number' in df.columns:
        df = df[df['cycle number'] == (loop_number + 1)]
    
    # remove lines with mode 3 which is open circuit, which typically happens when the safety limit is passed or at the beginning of the measurement
    df = df[df['mode'] != 3]

    # Plot and show our data
    potential=df['Ewe/V']
    current=current_unit_factor*df['<I>/mA']

    if not config[identifier].get('outliers_indexes'):
        while True:
            idx = np.ones(len(current), dtype=bool)
            outliers_indexes_current = find_outliers(current)
            outliers_indexes_diffcurrent = find_outliers(np.diff(current))
            outliers_indexes_diffpotential = find_outliers(np.diff(potential))
            outliers_indexes = outliers_indexes_current + outliers_indexes_diffcurrent + outliers_indexes_diffpotential
            # for CV there's often just one point being removed, and this goes on forever. Stopping when there's just one point in the outliers list.
            if not outliers_indexes or len(outliers_indexes) < 2:
                break
            #convert to set for unifying duplicates
            outliers_indexes = set(outliers_indexes)
            print('Removing outliers: ' + str(outliers_indexes))
            for i in outliers_indexes:
                idx[i] = False
            # skip also a few of the tail points which could be transients due to touching the compliance and stopping the measurement
            idx[-1] = False; #idx[-5:-1] = [False]*4;
            current = current[idx]
            potential = potential[idx]

    else:        
        for i in jsonloads(config[identifier]['outliers_indexes']):
            idx[i] = False
            #del potential[i]
            #del current[i]
        current = current.iloc(idx)
        potential = potential.iloc(idx)
    potential_toReference = potential + float(config[identifier]['reference_new']) + float(config[identifier]['reference_original'])
    if config[identifier].get('resistance'):
        resistance = float(config[identifier]['resistance'])*float(config['DEFAULT']['r_correct'])
        x = potential_toReference - (resistance*current/(1000*current_unit_factor))
    else:
        x = potential_toReference
    if config['DEFAULT']['normalize_surface'] == 'True':
        y=current/float(config[identifier]['surface'])
    else:
        y=current
    if not config[identifier].get('linestyle'):
        config[identifier]['linestyle'] = 'solid'
    if config['DEFAULT']['plot_tafel'] == 'True':
        plt.subplot(2, 1, 2)
        ax2.plot(y,x, linewidth=3, color=colors(int(config[identifier]['color_index'])), label=config[identifier]['label_string'], linestyle=config[identifier]['linestyle'])#alpha=0.8)
        ax2.set_xscale('log')
        plt.subplot(2, 1, 1)
    ax.plot(x, y, linewidth=3, color=colors(int(config[identifier]['color_index'])), label=config[identifier]['label_string'], linestyle=config[identifier]['linestyle'])#alpha=0.8)
    if not axis_limits_preset_x:
        xmin = x.min() if x.min() < xmin else xmin
        xmax = x.max() if x.max() > xmax else xmax

    if not axis_limits_preset_y and (theres_no_CV or ("_CV_" in file_path)):
        ymin = y.min() if y.min() < ymin else ymin
        ymax = y.max() if y.max() > ymax else ymax
    


x_label = '$E_{WE}$ $[V]$'
# Add the x and y-axis labels
if config['DEFAULT'].get('reference_string'):
   # if isinstance(config['DEFAULT'].get('reference_string'),str):
    x_label = x_label + ' vs. ' + config['DEFAULT']['reference_string']
if float(config['DEFAULT']['r_correct']):
    x_label = x_label + ', iR corrected'
else:
    x_label = x_label + ', uncorrected'

if config['DEFAULT']['normalize_surface'] == "True":
    y_label = 'Current density $[' + current_unit_string + '/cm^2]$'
else:
    y_label = 'Current $[' + current_unit_string + ']$'

if not axis_limits_preset_x:
    config['DEFAULT']['xmin'] = str(xmin-0.02*(xmax-xmin))
    config['DEFAULT']['xmax'] = str(xmax+0.02*(xmax-xmin))
if not axis_limits_preset_y:
    config['DEFAULT']['ymin'] = str(ymin-0.05*(ymax-ymin))
    config['DEFAULT']['ymax'] = str(ymax+0.05*(ymax-ymin))

config_file_path = files_paths[0] + '.ini'
with open(config_file_path, 'w') as configfile:
    config.write(configfile)
    configfile.close()
    print("CONFIUGRATION SAVED IN " + config_file_path)
    
ax.set_xlabel(x_label, labelpad=5)
ax.set_ylabel(y_label, labelpad=5)

ax.set_xlim(float(config['DEFAULT'].get('xmin')),float(config['DEFAULT'].get('xmax')))
ax.set_ylim(float(config['DEFAULT'].get('ymin')),float(config['DEFAULT'].get('ymax')))

ax.xaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', top='on')
ax.xaxis.set_tick_params(which='minor', size=4, width=1, direction='in', top='on')
ax.yaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', right='on')
ax.yaxis.set_tick_params(which='minor', size=4, width=1, direction='in', right='on')

handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, frameon=False)
plt.title(config['DEFAULT'].get('title'))

if config['DEFAULT']['plot_tafel'] == 'True':
    ax2.set_xlabel('$Log_{10}$' + y_label, labelpad=5)
    ax2.set_ylabel(x_label, labelpad=5)
    ax2.set_xlim(float(config['DEFAULT'].get('ymin')),float(config['DEFAULT'].get('ymax')))
    ax2.set_ylim(float(config['DEFAULT'].get('xmin')),float(config['DEFAULT'].get('xmax')))
    ax2.xaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', top='on')
    ax2.xaxis.set_tick_params(which='minor', size=4, width=1, direction='in', top='on')
    ax2.yaxis.set_tick_params(which='major', size=7, width=1.5, direction='in', right='on')
    ax2.yaxis.set_tick_params(which='minor', size=4, width=1, direction='in', right='on')
    ax2.legend(handles, labels)

if config_file:
    filename = os.path.basename(os.path.splitext(config_file)[0])
    path = os.path.dirname(config_file)
else:
    filename = os.path.basename(os.path.dirname(files_paths[0]))
    path = os.path.dirname(files_paths[0])
    
plt.savefig(os.path.join(path,filename+'.png'),bbox_inches='tight', dpi=300)
try:
    plt.savefig(os.path.join(path,filename+'.pdf'),bbox_inches='tight')
except PermissionError:
    plt.savefig(os.path.join(path,filename+'-RENAME_ME.pdf'),bbox_inches='tight')
    print('THE REQUESTED FILE NAME WAS UNAVAILABLE, SAVED WITH RENAME_ME SUFFIX INSTEAD')
plt.show()
root.withdraw()
