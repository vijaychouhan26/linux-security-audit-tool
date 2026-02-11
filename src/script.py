from collections import defaultdict

data = defaultdict(list)

with open("backend/data/lynis-report.dat") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            data[k].append(v)

print("Warnings:", data.get("warning[]", [])[:5])
print("Suggestions:", data.get("suggestion[]", [])[:5])
print("Hardening index:", data.get("hardening_index"))
