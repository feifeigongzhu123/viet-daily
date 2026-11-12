"""Check that each syllable's Vietnamese tone mark matches the IPA contour."""
import json
from pathlib import Path

TONES = {
    "huyen": ("˨˩", "àằầèềìòồờùừỳ"),
    "sac": ("˧˥", "áắấéếíóốớúứý"),
    "hoi": ("˧˩˧", "ảẳẩẻểỉỏổởủửỷ"),
    "nga": ("˧ˀ˥", "ãẵẫẽễĩõỗỡũữỹ"),
    "nang": ("˧ˀ˩", "ạặậẹệịọộợụựỵ"),
}
EXPECTED = {name: pair[0] for name, pair in TONES.items()}
MARKS = {character: name for name, (_, chars) in TONES.items() for character in chars}

words = json.loads(Path("data/words.json").read_text(encoding="utf-8"))
errors = []
checked = 0
for item in words:
    if item.get("source", "").startswith("通用"):
        continue
    checked += 1
    syllables = item["word"].split()
    ipa = item["ipa"].split()
    if len(syllables) != len(ipa):
        errors.append(f"{item['id']}: syllable count {len(syllables)} != IPA count {len(ipa)}")
        continue
    for syllable, transcription in zip(syllables, ipa):
        tone = next((name for char, name in MARKS.items() if char in syllable), "ngang")
        expected = EXPECTED.get(tone, "˧")
        if not transcription.endswith(expected):
            errors.append(
                f"{item['id']}: {syllable!r} is {tone} ({expected}) but IPA is {transcription!r}"
            )

if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"OK: tone marks match IPA for all {checked} hand-checked textbook entries")
