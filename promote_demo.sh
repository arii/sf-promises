#!/bin/bash
set -e

SOURCE_JSON="data/data.candidate.json"
if [ ! -f "$SOURCE_JSON" ]; then
    if [ -f "data/data.candidate-worker-pilot.json" ]; then
        SOURCE_JSON="data/data.candidate-worker-pilot.json"
    else
        echo "[-] Error: data.candidate.json not found."
        exit 1
    fi
fi

cp "$SOURCE_JSON" docs/data.json
python3 -c "
import json
with open('docs/data.json') as f:
    d = json.load(f)
with open('docs/data.js', 'w', encoding='utf-8') as f:
    f.write('/* SF Promises - Dynamic SQLite Export */\nwindow.__DEMO_DATA__ = ')
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write(';\n')
"
echo "[+] Promoted candidate data to docs/data.json and docs/data.js successfully!"
