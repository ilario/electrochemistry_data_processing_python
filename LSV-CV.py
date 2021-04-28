#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
import CI_lib

def find_ci_mean_min(dir_name, file_name):
    file_path_CI_scheme_1 = re.sub(r'_\d\d_LSV_C\d\d.mpt$', '_', file_name)
    file_path_CI_scheme_1 = re.sub(r'_\d\d_CV_C\d\d.mpt$', '_', file_path_CI_scheme_1)
#    file_path_CI_scheme_2 = re.sub(r'.*_\d\d_LSV_C(\d\d).mpt$', '_C\g<1>.mpt', file_name)
    file_path_CI_scheme_2 = re.sub(r'.*_C(\d\d).mpt$', '_C\g<1>.mpt', file_name)
    file_path_CI_scheme_regex = re.escape(file_path_CI_scheme_1) + '\\d\\d_CI' + re.escape(file_path_CI_scheme_2)
    files_in_dir = os.listdir(dir_name)
    related_CI = filter(lambda x: re.search(file_path_CI_scheme_regex, x), files_in_dir)
    resistance_arr = []
    for currInt_name in related_CI:
        resistance_CI = CI_lib.get_resistance(os.path.join(dir_name, currInt_name))
        resistance_arr.append(resistance_CI)
    if resistance_arr:
        resistance_min = min(resistance_arr)
    else:
        resistance_min = 0
    return resistance_min

def analyse_file(file_path):
    # Loop the data lines to find the row where the data starts, which is when the number of tabulations stops increasing
    reference_original = 0
    reference_suggested = ''
    reference_found = False
    surface = 0
    surface_found = False
    repetitions = 0
    cycle_number_column = 0
    with open(file_path, 'r', encoding='latin-1') as temp_f:
        lines = temp_f.readlines()
        first_long_row = int(str.split(lines[1])[-1]) - 1
        for i, line in enumerate(lines[0:200]):
            # Count the column count for the current line
            #column_count = len(line.split('\t')) + 1
            # Set the new most column count
            #first_long_row = i if column_count > column_count_prev else first_long_row
            #column_count_prev = column_count
            
            #if more than one, take the last loop. The "zero" is the first data row
            if not reference_found:
                if line[0:19] == 'Reference electrode':
                    try:
                        reference_fromfile = re.search('(.+) \((.+) V\)',line[22:])
                        reference_suggested = reference_fromfile.group(1)
                        reference_original = reference_fromfile.group(2).replace(',','.')
                        reference_found = True
                    except AttributeError:
                        None
            if not surface_found:
                if line[0:22] == 'Electrode surface area':
                    surface_found = True
                    surface = float(line[25:30].replace(',','.'))
            if line[0:15] == 'Number of loops':
                repetitions = int(str.split(line)[-1]) - 1
            cycle_number_column_position = line.find("cycle number")
            if not cycle_number_column_position == -1:
                cycle_number_column = line.count("\t", 0, cycle_number_column_position)
        #take the last line and check if the decimal separator is comma or period
        if ',' in lines[i]:
            decimal_separator = ','
        else:
            decimal_separator = '.'
        if not repetitions and cycle_number_column:
            repetitions_string = str.split(lines[-1])[cycle_number_column]
            if decimal_separator == ',':
                repetitions_string = repetitions_string.replace(',','.')
            repetitions = int(float(repetitions_string)) - 1

    # Close file
    temp_f.close()
    return first_long_row, reference_suggested, reference_original, surface, decimal_separator, repetitions

def analyse_file_loop_number(file_path, loop_number):
    first_data_row = False
    last_data_row = False
    with open(file_path, 'r', encoding='latin-1') as temp_f:
        lines = temp_f.readlines()
        rows_count = len(lines)
        for i, line in enumerate(lines[0:200]):
            if line[0:4] == 'Loop':
#               tmp_first_data_row = int(str.split(line)[5])
                if str.split(line)[1] == str(loop_number):
                    first_data_row = int(str.split(line)[5]) #tmp_first_data_row
                    last_data_row = int(str.split(line)[7])            
    temp_f.close()
    return first_data_row, last_data_row, rows_count
            
#copied from https://towardsdatascience.com/5-ways-to-detect-outliers-that-every-data-scientist-should-know-python-code-70a54335a623
def find_outliers(data):
    #define a list to accumlate outliers
    outliers_indexes = []
    
    # Set upper and lower limit to X standard deviation
    # this should be done locally, as the mean will vary locally...
    data_std = np.std(data)
    data_mean = np.mean(data)
    cut_off = data_std * 40#3 would be the common value here
    
    lower_limit = data_mean - cut_off 
    upper_limit = data_mean + cut_off
    # Generate outliers
    for i, outlier_candidate in enumerate(data):
        if outlier_candidate > upper_limit or outlier_candidate < lower_limit:
            outliers_indexes.append(i)
    return outliers_indexes

# Edit the font, font size, and axes width
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 2

config = configparser.ConfigParser()

files_paths = []
config_file = ""
if len(sys.argv) == 2:
    config_file = sys.argv[1]
    automated = True
else:
    automated = False
    # Create interface, hide main window, ask for file selection
    root = tk.Tk()
    root.withdraw()
    if len(sys.argv) > 2:
        for argument in sys.argv[1:]:
            files_paths.append(os.path.abspath(argument))
    else:
        config_file = askopenfilename(filetypes=[("EC scripts configuration", ".ini")],title='Choose the configuration file or skip')

if config_file:
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
xmin=1000
xmax=-1000
ymin=1000
ymax=-1000
color_index = []
theres_no_CV = True
prevReferenceNew = False
plt.axhline(y=0, color='lightgray', linestyle='-')

for j,identifier in enumerate(files_paths):
    file_path = str.split(identifier)[0]
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
    file_path = str.split(identifier)[0]
    first_long_row = int(config[identifier]['first_long_row'])
    loop_number = int(config[identifier].get('loop_number') or -1)
    first_data_row, last_data_row, rows_count = analyse_file_loop_number(file_path, loop_number)
    #skip_points = jsonloads(config[identifier]['skip_points']) if config[identifier].get('skip_points') else []
    skiprows_list = list(range(first_long_row))# + skip_points
    # False and True are recognized both as int and as bool!
    if not isinstance(first_data_row, bool) and not isinstance(last_data_row, bool): 
        skiprows_list = skiprows_list + list(range(first_long_row+1,first_long_row+first_data_row+1)) + list(range(first_long_row+last_data_row, rows_count))
    print(file_path)
    df = pd.read_csv(file_path, sep='\t', decimal=config[identifier]['decimal_separator'], skiprows=lambda x: x in skiprows_list)
    
    if not loop_number == -1 and 'cycle number' in df.columns:
        df = df[df['cycle number'] == (loop_number + 1)]
    
    # remove lines with mode 3 which is open circuit, which typically happens when the safety limit is passed or at the beginning of the measurement
    df = df[df['mode'] != 3]

    # Plot and show our data
    potential=df['Ewe/V']
    current=df['<I>/mA']

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
        x = potential_toReference - (resistance*current/1000)
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

    if theres_no_CV or ("_CV_" in file_path):
        if not axis_limits_preset_x:
            xmin = x.min() if x.min() < xmin else xmin
            xmax = x.max() if x.max() > xmax else xmax
        if not axis_limits_preset_y:
            ymin = y.min() if y.min() < ymin else ymin
            ymax = y.max() if y.max() > ymax else ymax
    


x_label = '$E_{WE}$ [V]'
# Add the x and y-axis labels
if config['DEFAULT'].get('reference_string'):
   # if isinstance(config['DEFAULT'].get('reference_string'),str):
    x_label = x_label + ' vs. ' + config['DEFAULT']['reference_string']
if float(config['DEFAULT']['r_correct']):
    x_label = x_label + ' iR corrected'
else:
    x_label = x_label + ' uncorrected'

if config['DEFAULT']['normalize_surface'] == "True":
    y_label = 'Current density [mA/cm$^2$]'
else:
    y_label = 'Current [mA]'

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
ax.legend(handles, labels)


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
    filename = os.path.basename(os.path.splitext(config_file)[0])+'-LSV'
else:
    filename = os.path.basename(os.path.dirname(files_paths[0]))+'-LSV'
    
plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'.png'),bbox_inches='tight', dpi=300)
try:
    plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'.pdf'),bbox_inches='tight')
except PermissionError:
    plt.savefig(os.path.join(os.path.dirname(files_paths[0]),filename+'-RENAME_ME.pdf'),bbox_inches='tight')
    print('THE REQUESTED FILE NAME WAS UNAVAILABLE, SAVED WITH RENAME_ME SUFFIX INSTEAD')
plt.show()


