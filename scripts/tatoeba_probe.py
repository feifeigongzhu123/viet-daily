import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import zhconv

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
GENERAL = [item for item in DATA if item["id"].startswith("gen-")]
random.seed(7)
sample = random.sample(GENERAL, 40)
URL = "https://tatoeba.org/en/api_v0/search"


def find_example(word: str):
    params = {
        "from": "vie",
        "to": "cmn",
        "query": word,
        "orphans": "no",
        "unowned": "no",
        "sort": "relevance",
    }
    try:
        response = requests.get(URL, params=params, timeout=25)
        if response.status_code != 200:
            return word, None, f"HTTP {response.status_code}"
        data = response.json()
    except Exception as error:
        return word, None, str(error)

    lowered = word.lower()
    candidates = []
    for result in data.get("results", []):
        text = (result.get("text") or "").strip()
        if not text or lowered not in text.lower():
            continue
        if len(text) > 110 or len(text) < 6:
            continue
        translation = None
        for group in result.get("translations", []):
            for item in group:
                if item.get("lang") == "cmn":
                    translation = item.get("text")
                    for transcription in item.get("transcriptions", []):
                        if transcription.get("script") == "Hans":
                            translation = transcription.get("text")
                            break
                    break
            if translation:
                break
        if translation:
            translation = zhconv.convert(translation, "zh-cn").strip()
            if 3 <= len(translation) <= 90:
                candidates.append((len(text), text, translation, result.get("id")))
    if not candidates:
        return word, None, "no pair"
    candidates.sort(key=lambda item: item[0])
    return word, candidates[0], None


started = time.time()
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(find_example, item["word"]): item for item in sample}
    hits = 0
    for future in as_completed(futures):
        word, example, error = future.result()
        if example:
            hits += 1
            print(f"OK  {word:20} {example[1]} || {example[2]}")
        else:
            print(f"MISS {word:20} {error}")
print(f"coverage {hits}/{len(sample)} in {time.time()-started:.1f}s")
