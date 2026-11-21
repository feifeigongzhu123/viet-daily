"""Headless UI smoke test for categorized library, display-order autoplay, and selection resume.

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


def dom_row_ids(page, selector="#library-list .lib-row"):
    return page.eval_on_selector_all(selector, "rows => rows.map(r => r.dataset.id)")


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
    check("5 category chips", chips.count() == 5, " | ".join(chip_labels))
    check("learned chip starts at zero", any(t.startswith("已学会 0") for t in chip_labels), " | ".join(chip_labels))

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

    # Seed: one "again", three "learned" (two textbook, one general).
    textbook_ids = page.evaluate("VOCAB.filter(w => !w.source.startsWith('通用')).slice(0, 4).map(w => w.id)")
    general_id = page.evaluate("VOCAB.find(w => w.source.startsWith('通用')).id")
    store = page.evaluate("JSON.parse(localStorage.getItem('vietdaily.v1') || 'null')")
    if not store:
        store = {"version": 1, "settings": {}, "progress": {}, "plans": {}, "history": {}}
    store.setdefault("progress", {})
    store["progress"][textbook_ids[0]] = {"seen": 1, "stage": 0, "due": "2026-11-21"}
    for word_id in textbook_ids[1:3] + [general_id]:
        store["progress"][word_id] = {"seen": 1, "stage": 1, "due": "2026-12-01"}
    page.evaluate("s => localStorage.setItem('vietdaily.v1', JSON.stringify(s))", store)
    page.reload(wait_until="networkidle")
    page.locator('.nav-btn[data-view="library"]').click()
    page.wait_for_selector("#library-list .lib-group")

    again_labels = [page.locator("#filter-chips .chip").nth(i).inner_text().replace("\n", " ")
                    for i in range(page.locator("#filter-chips .chip").count())]
    check("again and learned counts", any(t.startswith("不熟 1") for t in again_labels)
          and any(t.startswith("已学会 3") for t in again_labels), " | ".join(again_labels))

    page.locator('#filter-chips .chip[data-filter="again"]').click()
    page.wait_for_timeout(250)
    again_titles = [page.locator("#library-list .lib-group-head span").nth(i).inner_text()
                    for i in range(page.locator("#library-list .lib-group-head span").count())]
    check("again filter groups seeded word", again_titles == ["教材词 · 需要加强"], str(again_titles))
    check("again badge shown", page.locator(".status-badge.is-again").count() == 1)
    page.screenshot(path=str(OUT / "library-again-mobile.png"), full_page=False)

    page.locator('.nav-btn[data-view="library"]').click()
    page.locator('#filter-chips .chip[data-filter="learned"]').click()
    page.wait_for_timeout(250)
    learned_titles = [page.locator("#library-list .lib-group-head span").nth(i).inner_text()
                      for i in range(page.locator("#library-list .lib-group-head span").count())]
    check("learned filter grouped by source", len(learned_titles) == 2
          and learned_titles[0].startswith("已学会 · 第 ")
          and learned_titles[1].startswith("已学会 · 通用词 · "), str(learned_titles))
    check("learned rows count", page.locator("#library-list .lib-row").count() == 3,
          str(page.locator("#library-list .lib-row").count()))
    page.screenshot(path=str(OUT / "library-learned-mobile.png"), full_page=False)

    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(350)
    check("learned autoplay starts", page.locator("#autoplay-btn").inner_text().startswith("■ 停止 1/3"),
          page.locator("#autoplay-btn").inner_text())
    check("learned autoplay highlights first row", page.locator(".lib-row.is-autoplay").count() == 1)
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(150)

    # Autoplay must follow DOM/display order, not the raw vocabulary order.
    page.locator('#filter-chips .chip[data-filter="textbook"]').click()
    page.wait_for_timeout(250)
    order = dom_row_ids(page)
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(250)
    current = page.locator(".lib-row.is-autoplay").get_attribute("data-id")
    check("autoplay starts at first displayed row", current == order[0], f"{current} vs {order[0]}")
    try:
        page.wait_for_function(
            "first => { const row = document.querySelector('.lib-row.is-autoplay'); return row && row.dataset.id !== first; }",
            arg=order[0],
            timeout=6000,
        )
        next_id = page.locator(".lib-row.is-autoplay").get_attribute("data-id")
        check("autoplay moves to next displayed row", next_id == order[1], f"{next_id} vs {order[1]}")
    except Exception as error:
        check("autoplay moves to next displayed row", False, f"timeout: {error}")

    # Choosing a word's speaker should continue from that row downward.
    target_row = page.locator("#library-list .lib-row").nth(4)
    target_id = target_row.get_attribute("data-id")
    target_row.locator(".audio-round").click()
    page.wait_for_timeout(350)
    selected = page.locator(".lib-row.is-autoplay")
    check("selection highlights chosen row", selected.count() == 1 and selected.get_attribute("data-id") == target_id,
          target_id)
    check("selection starts at its position", page.locator("#autoplay-btn").inner_text().startswith("■ 停止 5/"),
          page.locator("#autoplay-btn").inner_text())
    try:
        page.wait_for_function(
            "chosen => { const row = document.querySelector('.lib-row.is-autoplay'); return row && row.dataset.id !== chosen; }",
            arg=target_id,
            timeout=6000,
        )
        next_id = page.locator(".lib-row.is-autoplay").get_attribute("data-id")
        check("selection continues to next displayed row", next_id == order[5], f"{next_id} vs {order[5]}")
    except Exception as error:
        check("selection continues to next displayed row", False, f"timeout: {error}")
    page.screenshot(path=str(OUT / "library-autoplay-mobile.png"), full_page=False)

    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(150)
    check("autoplay stopped", page.locator("#autoplay-btn").inner_text() == "▶ 自动播放")

    # Opening a word records its position; autoplay starts there after closing the sheet.
    page.locator('#filter-chips .chip[data-filter="textbook"]').click()
    page.wait_for_timeout(200)
    order = dom_row_ids(page)
    page.locator("#library-list .lib-row").nth(2).locator(".lib-main").click()
    page.wait_for_selector("#sheet:not([hidden])")
    page.locator("#sheet .sheet-close").click()
    page.wait_for_timeout(250)
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(300)
    opened_current = page.locator(".lib-row.is-autoplay")
    check("opened word sets autoplay start", opened_current.count() == 1
          and opened_current.get_attribute("data-id") == order[2]
          and page.locator("#autoplay-btn").inner_text().startswith("■ 停止 3/"),
          f"{opened_current.get_attribute('data-id') if opened_current.count() else 'none'} / {order[2]}")
    page.locator("#autoplay-btn").click()
    page.wait_for_timeout(150)

    # Wide layout sanity.
    page.set_viewport_size({"width": 900, "height": 720})
    page.locator('.nav-btn[data-view="library"]').click()
    page.locator('#filter-chips .chip[data-filter="all"]').click()
    page.wait_for_timeout(300)
    check("wide layout list visible", page.locator("#library-list .lib-row").count() > 0)
    page.screenshot(path=str(OUT / "library-all-wide.png"), full_page=False)
    browser.close()

failed = [name for name, ok, _ in checks if not ok]
if errors:
    print("\nBrowser errors:")
    for line in errors:
        print("  " + line)
print(json.dumps({"passed": len(checks) - len(failed), "failed": failed, "errors": errors}, ensure_ascii=False))
sys.exit(1 if failed or errors else 0)
