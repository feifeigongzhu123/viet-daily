import json
from pathlib import Path

import esprima

ROOT = Path(__file__).resolve().parents[1]
words = json.loads((ROOT / "data/words.json").read_text(encoding="utf-8"))
phonetics = json.loads((ROOT / "data/phonetics.json").read_text(encoding="utf-8"))
json.loads((ROOT / "manifest.webmanifest").read_text(encoding="utf-8"))
index = json.loads((ROOT / "audio/index.json").read_text(encoding="utf-8"))

for name in ["app.js", "sw.js"]:
    source = (ROOT / name).read_text(encoding="utf-8")
    esprima.parseScript(source)
    print(f"{name}: syntax OK ({len(source):,} chars)")

missing = []
for item in words:
    word_path = ROOT / "audio" / "words" / f"{item['id']}.mp3"
    if not word_path.exists() or word_path.stat().st_size < 1000:
        missing.append(str(word_path))
    if f"audio/words/{item['id']}.mp3" not in index["files"]:
        missing.append(f"index missing words/{item['id']}")

    example_path = ROOT / "audio" / "examples" / f"{item['id']}.mp3"
    if example_path.exists():
        if example_path.stat().st_size < 1000:
            missing.append(str(example_path))
        if f"audio/examples/{item['id']}.mp3" not in index["files"]:
            missing.append(f"index missing examples/{item['id']}")

for entry in index["files"]:
    if not (ROOT / entry).exists():
        missing.append(f"index points to missing file: {entry}")

for section in ("vowels", "consonants", "tones"):
    for item in phonetics.get(section, []):
        phonetic_path = ROOT / "audio" / "phonetics" / f"{item['id']}.mp3"
        if not phonetic_path.exists() or phonetic_path.stat().st_size < 1000:
            missing.append(str(phonetic_path))
        if f"audio/phonetics/{item['id']}.mp3" not in index["files"]:
            missing.append(f"index missing phonetics/{item['id']}")

print(f"words: {len(words)}, audio indexed: {len(index['files'])}, missing: {len(missing)}")
if missing:
    print("\n".join(missing[:30]))
    raise SystemExit(1)
