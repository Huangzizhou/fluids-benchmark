import os, re, json
import numpy as np
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Solver Type.')
    parser.add_argument("job", type=str, default="", help="job")
    args = parser.parse_args()
    
    data = []
    for root, _, files in os.walk("./logs"):
        for file in files:
            if file.find(".out") == -1:
                continue
            if os.path.exists(os.path.join(root, file[:-4]+".json")):
                continue
            found_time = False
            found_mem = False
            memory = 0
            time = 0
            with open(os.path.join(root, file), 'r') as f:
                lines = f.readlines()
                num = 0
                destination = ''
                for idx in range(len(lines)):
                    if destination == '' and lines[idx][:22] == "Cleanup script file is":
                        destination = lines[idx][23:]
                        words = destination.split('/')
                        del words[-1]
                        words[-1] = words[-1][:-4]
                        destination = '/'.join(words)
                    elif lines[idx][:24] == "  Total wall-clock time:":
                        time = float(re.findall(r"\d+\.?\d*",lines[idx])[0])
                        cur_data = file + "   ,   " + repr(time)
                        found_time = True
                    elif found_time and lines[idx][:5] == "Total":
                        memory = float(re.findall(r"\d+\.?\d*", lines[idx])[3])*1024
                        cur_data += "," + repr(memory)
                        found_mem = True
                        found_time = False
                        num += 1
                        data.append(cur_data + ", " + destination)
            if found_mem and num == 1:
                json_data = { "peak_memory": memory,  "time_solving": time}
                with open(os.path.join(root, file[:-4]+".json"),'w') as f:
                    f.write(json.dumps(json_data, indent=4))
                os.system('cp '+os.path.join(root, file[:-4]+".json")+' '+os.path.join(destination, 'output.json'))

    print("\n".join(data))