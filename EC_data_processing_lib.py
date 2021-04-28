#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ilario Gelmetti
"""
# Import required packages
import os
import numpy as np #import diff,std,mean,array
import re
import CI_lib

# find_ci_mean_min(dir_name, file_name):
# return resistance_min

# analyse_file(file_path):
# return first_long_row, reference_suggested, reference_original, surface, decimal_separator, repetitions

# analyse_file_loop_number(file_path, loop_number):
# return first_data_row, last_data_row, rows_count
            
# find_outliers(data):
# return outliers_indexes

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

