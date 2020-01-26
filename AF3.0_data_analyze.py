"""

AF3.0 data analyze script

Author: Vikram Seshadri
06/12/2019

This script is used to collect data such as volume consumed and total samples to determine if there was an incomplete run.
main functions of this script:
    1. Creates a new csv file to store collective data from the RAW fieldnames.
    2. Volume from each cycle is calculated.
    3. Samples are counted to determine successful runs.
    4. Total volume is calculated after each cycle.

"""

import pandas as pd
import re
import numpy
import glob
import csv

total_volume = 0
sample_cnt = 0
volume_ml = 0
flag = 0
dataString = ""

filename_pattern = r"(C:\\Users\\Owner\\Desktop\\AF3.0\\RAW\\)(AF )(Volume ([0-9]+)mL )(RunTime ([0-3]+)min )(Cycle([0-9]+))(.csv)"
filedir = r"C:\Users\Owner\Desktop\AF3.0\RAW"
filedir2 = r"C:\Users\Owner\Desktop\AF3.0\AF3.0"
files = glob.glob(filedir+r'\*.csv')

numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    parts[1::2] = map(int, parts[1::2])
    return parts

for j in sorted(files,key=numericalSort):
    df = pd.read_csv(j)
    n = re.match(filename_pattern,j)

    if n is not None:

        if flag == 0:
            filename = str(n.group(5)) + "Combined.csv"
            f = open(filedir2 + ' ' + filename, 'w+')
            writer = csv.DictWriter(f, fieldnames=["Cycle","Samples","Volume consumed (mL)","Remarks","Total Volume (mL)"])
            writer.writeheader()
            f.close()
            f = open(filedir2 + ' ' + filename, 'ab')
            flag = 1

        sample_cnt = max(df["Sample"])
        volume_ml = abs(float(max(df["Volume(mL)"])) - float(min(df["Volume(mL)"])))
        total_volume += volume_ml

        if sample_cnt < 1800:
            print ("Cycle: " + str(n.group(8) + ", Number of Samples: " + str(sample_cnt) + ", Volume (mL): " + str(volume_ml)) + ", Run Incomplete" )
            dataString = str(n.group(8)) + ',' + str(sample_cnt) + ',' + str(volume_ml) + ', Run Incomplete,'+str(total_volume)
        else:
            print ("Cycle: " + str(n.group(8) + ", Number of Samples: " + str(sample_cnt) + ", Volume (mL): " + str(volume_ml)))
            dataString = str(n.group(8)) + ',' + str(sample_cnt) + ',' + str(volume_ml) + ',-,'+str(total_volume)

        b = (dataString + '\n').encode('utf-8')

        f.write(b)
        dataString = ""

f.close()
