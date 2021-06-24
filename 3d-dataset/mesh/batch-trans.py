import os, subprocess

input_folder = '/home/zizhou/3d/tetwild_out_1'

for root, _, files in os.walk(input_folder):
    for file in files:
        if file.find('.mesh') == -1:
            continue
        subprocess.Popen(['python', 'trans.py', file])