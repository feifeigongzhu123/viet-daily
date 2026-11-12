"""Generate standard Vietnamese MP3s for words (and optionally examples).

Voice: Microsoft Edge neural TTS, vi-VN-HoaiMyNeural (northern Vietnamese).
Requires network access to Microsoft's speech service.

Usage:
    python scripts/generate_audio.py [--force] [--no-examples] [--workers 8]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import edge_tts

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "words.json"
AUDIO_DIR = ROOT / "audio"
WORD_DIR = AUDIO_DIR / "words"
EXAMPLE_DIR = AUDIO_DIR / "examples"
INDEX_FILE = AUDIO_DIR / "index.json"
VOICE = "vi-VN-HoaiMyNeural"


async def synthesize(text: str, target: Path, rate: str) -> None:
    last_error: Exception | None = None
    for attempt in range(1, 5):
        try:
            communicate = edge_tts.Communicate(text=text, voice=VOICE, rate=rate)
            await communicate.save(str(target))
            if target.exists() and target.stat().st_size > 1000:
                return
            raise RuntimeError("generated file is unexpectedly small")
        except Exception as exc:  # noqa: BLE001 - retry any transport/API error
            last_error = exc
            target.unlink(missing_ok=True)
            await asyncio.sleep(1.2 * attempt)
    raise RuntimeError(f"Could not synthesize {text!r}: {last_error}")


async def generate(words: list[dict], force: bool, include_examples: bool, workers: int) -> None:
    WORD_DIR.mkdir(parents=True, exist_ok=True)
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, Path, str]] = []
    for item in words:
        jobs.append((item["word"], WORD_DIR / f"{item['id']}.mp3", "-10%"))
        if include_examples:
            jobs.append((item["example"], EXAMPLE_DIR / f"{item['id']}.mp3", "-7%"))

    pending = [job for job in jobs if force or not job[1].exists()]
    print(f"{len(jobs)} audio files selected, {len(pending)} to generate, workers={workers}.")
    if not pending:
        return

    semaphore = asyncio.Semaphore(workers)
    done = 0

    async def run(text: str, target: Path, rate: str) -> None:
        nonlocal done
        async with semaphore:
            await synthesize(text, target, rate)
            done += 1
            if done % 25 == 0 or done == len(pending):
                print(f"  {done}/{len(pending)}", flush=True)

    results = await asyncio.gather(
        *(run(text, target, rate) for text, target, rate in pending),
        return_exceptions=True,
    )
    errors = [result for result in results if isinstance(result, Exception)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)


def write_index(words: list[dict]) -> None:
    paths = ["audio/words", "audio/examples"]
    files = []
    for item in words:
        word_file = f"audio/words/{item['id']}.mp3"
        example_file = f"audio/examples/{item['id']}.mp3"
        if (ROOT / word_file).exists():
            files.append(word_file)
        if (ROOT / example_file).exists():
            files.append(example_file)
    INDEX_FILE.write_text(
        json.dumps({"directories": paths, "files": files}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="regenerate existing MP3s")
    parser.add_argument("--no-examples", action="store_true", help="generate word audio only")
    parser.add_argument("--workers", type=int, default=8, help="parallel TTS requests")
    args = parser.parse_args()

    words = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    asyncio.run(generate(words, args.force, not args.no_examples, max(1, args.workers)))
    write_index(words)

    all_mp3 = list(AUDIO_DIR.rglob("*.mp3"))
    total_bytes = sum(path.stat().st_size for path in all_mp3)
    print(f"OK: {len(all_mp3)} MP3 files, {total_bytes / 1024 / 1024:.1f} MB")
    print(f"Wrote {INDEX_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
