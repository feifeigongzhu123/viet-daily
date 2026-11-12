import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
files = sorted(Path("audio").glob("*/*.mp3"))
durations = []
errors = []
for path in files:
    result = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, text=True, errors="ignore")
    match = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", result.stderr)
    if not match:
        errors.append(str(path))
        continue
    hours, minutes, seconds = match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    durations.append(duration)
    if duration < 0.5 or duration > 12:
        errors.append(f"{path}: unusual duration {duration:.2f}s")

print(f"audio files: {len(files)}, parsed: {len(durations)}")
print(f"duration min/median/max: {min(durations):.2f}s / {sorted(durations)[len(durations)//2]:.2f}s / {max(durations):.2f}s")
print(f"total audio: {sum(durations):.1f}s")
if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print("OK: all audio files readable with plausible durations")
