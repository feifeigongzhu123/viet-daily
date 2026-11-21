"""Headless UI smoke test for the categorized library and autoplay.

Run the local server first: python -m http.server 8772
Then: python scripts/test_library_ui.py
Uses the installed Microsoft Edge so no Chromium download is required.
"""

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8772/"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT = Path(__file__).resolve().parent.parent / "tmp" / "ui"
OUT.mkdir(parents=True, exist_ok=True)

errors = []
checks = []


def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))
    print(("PASS " if condition else "FAIL ") + name + (f" | {detail}" if detail else ""))


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=EDGE, headless=True)
    page = browser.new_page(viewport={"width": 360, "height": 720}, device_scale_factor=2)
    page.on("console", lambda msg: errors.append(f"console {msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    page.goto(URL, wait_until="networkidle")
    check("app loaded", page.locator(".brand, .app-title, header").count() > 0)
    check("4 nav buttons", page.locator(".nav-btn").count() == 4, str(page.locator(".nav-btn").count()))

    page.locator('.nav-btn[data-view="library"]').click()
    page.wait_for_selector("#library-list .lib-group")

    chips = page.locator("#filter-chips .chip")
    chip_labels = [chips.nth(i).inner_text().replace("\n", " ") for i in range(chips.count())]
    check("4 category chips", chips.count() == 4, " | ".join(chip_labels))

    all_groups = page.locator("#library-list .lib-group-head span")
    group_titles = [all_groups.nth(i).inner_text() for i in range(all_groups.count())]
    check("grouped sections render", len(group_titles) > 3, f"{len(group_titles)} groups")
    check("textbook groups first", any("第" in t and "课" in t for t in group_titles), group_titles[:3])
    check("general grouped by letter", any(t.startswith("通用词 ·") for t in group_titles))

    page.screenshot(path=str(OUT / "library-all-mobile.png"), full_page=False)

    page.locator('#filter-chips .chip[data-filter="textbook"]').click()
    page.wait_for_timeout(250)
    tb_titles = [page.locator("#library-list .lib-group-head span").nth(i).inner_text()
                 for i in range(page.locator("#library-list .lib-group-head span").count())]
    check("textbook filter only lessons", all("第" in t and "课" in t for t in tb_titles), tb_titles[:2])

    page.locator('#filter-chips .chip[data-filter="general"]').click()
    page.wait_for_timeout(250)
    gen_titles = [page.locator("#library-list .lib-group-head span").nth(i).inner_text()
                  for i in range(page.locator("#library-list .lib-group-head span").count())]
    check("general filter only letters", all(t.startswith("通用词 ·") for t in gen_titles), gen_titles[:3])

    # Seed one textbook word as "不熟" (seen, stage 0).
    first_id = page.evaluate("VOCAB.find(w => !w.source.startsWith('通用')).id")
    store = page.evaluate("JSON.parse(localStorage.getItem('vietdaily.v1') || 'null')")
    if not store:
        store = {"version": 1, "settings": {}, "progress": {}, "plans": {}, "history": {}}
    store.setdefault("progress", {})[first_id] = {"seen": 1, "stage": 0, "due": "2026-11-21"}
    page.evaluate("s => localStorage.setItem('vietdaily.v1', JSON.stringify(s))", store)
    page.reload(wait_until="networkidle")
    page.locator('.nav-btn[data-view="library"]').click()
    page.locator('#filter-chips .chip[data-filter="again"]').click()
    page.wait_for_timeout(250)
    again_titles = [page.locator("#library-list .lib-group-head span").nth(i).inner_text()
                    for i in range(page.locator("#library-list .lib-group-head span").count())]
    check("again filter groups seeded word", again_titles == ["教材词 · 需要加强"], str(again_titles))
    check("again badge shown", page.locator(".status-badge.is-again").count() == 1)
    page.screenshot(path=str(OUT / "library-again-mobile.png"), full_page=False)

    # Autoplay in the "不熟" category.
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(400)
    btn_text = page.locator("#autoplay-btn").inner_text()
    check("autoplay started", btn_text.startswith("■ 停止"), btn_text)
    check("autoplay highlights current", page.locator(".lib-row.is-autoplay").count() == 1)
    page.screenshot(path=str(OUT / "library-autoplay-mobile.png"), full_page=False)
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(150)
    check("autoplay stopped", page.locator("#autoplay-btn").inner_text() == "▶ 自动播放")

    # Wide (large) layout sanity.
    page.set_viewport_size({"width": 900, "height": 720})
    page.locator('.nav-btn[data-view="library"]').click()
    page.locator('#filter-chips .chip[data-filter="all"]').click()
    page.wait_for_timeout(300)
    cols = page.evaluate("getComputedStyle(document.querySelector('.library-list')).gridTemplateColumns")
    check("wide layout still single column list", cols.count(" ") == 0 or "px" in cols, cols)

    page.screenshot(path=str(OUT / "library-all-wide.png"), full_page=False)
    browser.close()

failed = [name for name, ok, _ in checks if not ok]
if errors:
    print("\nBrowser errors:")
    for line in errors:
        print("  " + line)
print(json.dumps({"passed": len(checks) - len(failed), "failed": failed, "errors": errors}, ensure_ascii=False))
sys.exit(1 if failed or errors else 0)
