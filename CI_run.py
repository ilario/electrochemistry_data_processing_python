#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Ilario Gelmetti
"""
import CI_lib
from tkinter.filedialog import askopenfilename

file_path = askopenfilename(filetypes=[("EC-Lab Text Format", ".mpt")],title='Choose the CI file to analyse')
CI_lib.get_resistance(file_path)