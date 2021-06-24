import json, os, argparse

solvers = ['fem','split','flip']

parser = argparse.ArgumentParser(description='Solver Type.')
parser.add_argument("--path", type=str, default="/scratch/zh1476/fluid/model-problems/", help="root folder")
parser.add_argument("--key", "-k", type=str, default="")
args = parser.parse_args()

# content = []
# for root, dirs, files in os.walk(args.path):
#     for dir in dirs:
#         if args.key == "" or dir.find(args.key) != -1:
#             if os.path.exists(os.path.join(root, dir, 'output.json')):
#                 with open(os.path.join(root, dir, 'output.json'),'r') as f:
#                     json_data = json.load(f)
#                 solver = ''
#                 for s in solvers:
#                     if dir.find(s) != -1:
#                         solver = s
#                 if solver == '':
#                     continue
#                 content.append(','.join([solver, repr(json_data["mesh_size"]), repr(json_data["err_l2"]), repr(json_data["time_solving"]), str(json_data["peak_memory"])]))
#     break

# print('\n'.join(content))

for root, dirs, _ in os.walk(args.path):
    for dir in dirs:
        if dir.find('2d') == -1:
            continue
        if args.key == "" or dir.find(args.key) != -1:
            if not os.path.exists(os.path.join(root, dir, 'output.json')):
                print(os.path.join(root, dir))
