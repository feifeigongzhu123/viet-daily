import bz2
import json
import re
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
lines = bz2.open(ROOT / "data/tatoeba/vie_sentences.tsv.bz2", "rt", encoding="utf-8").read().splitlines()
sentences = []
for line in lines:
    parts = line.split("\t", 2)
    if len(parts) == 3:
        sentences.append((parts[0], parts[2].strip()))

words = ["hướng", "công việc", "giường", "bộ", "dê", "thay đổi", "lực", "văn phòng", "bốn", "lần"]


def candidates(word):
    pattern = re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)
    result = []
    for sentence_id, text in sentences:
        if not (12 <= len(text) <= 90):
            continue
        if not text[-1] in ".?!":
            continue
        if pattern.search(text):
            result.append((len(text), sentence_id, text))
    result.sort()
    return result[:3]


selected = []
for word in words:
    found = candidates(word)
    print("=" * 60)
    print(word, "candidates", len(found))
    for item in found:
        print(item)
    if found:
        selected.append(found[0][2])

response = requests.post(
    "https://edge.microsoft.com/translate/translatetext",
    params={"from": "vi", "to": "zh-Hans", "isEnterpriseClient": "false"},
    json=selected,
    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    timeout=60,
)
print("=" * 60)
if response.ok:
    translations = response.json()
    for source, item in zip(selected, translations):
        print(source, "=>", item["translations"][0]["text"])
else:
    print(response.status_code, response.text[:300])
