import glob
import json
import os
import subprocess

patterns = ["env/*/"]
out_dir = "./archives"

data = {}

if os.path.exists("data.json"):
    with open("data.json", "r") as file:
        data = json.load(file)

for pattern in patterns:
    results = glob.glob(pattern)

    for result in results:
        m_time = os.path.getmtime(result)
        if result not in data or (result in data and data[result] < m_time):
            data[result] = m_time
            subprocess.call("7z a {}.zip {}".format(os.path.normpath(out_dir + "/" + result), result))

with open("data.json", "w") as file:
    json.dump(data, file)