#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data.json 内联进 index.html(file:// 打不开时的兜底数据源)。

为什么需要: index.html 靠 JS 渲染,数据原本只来自 fetch('data.json')。
浏览器禁止在 file:// 下 fetch 本地文件(origin=null → CORS 拦截),所以双击
打开 / 从本地索引用 file:// 点进来会白屏报「Failed to fetch」。

用法:
    python3 sync_trip_data.py            # 把 data.json 同步进 index.html
    python3 sync_trip_data.py --check    # 只检查两边是否一致(不一致退出码 1)

改行程只改 data.json,改完跑一次本脚本(或跑 --check 看是否漏同步)。
"""
import json
import re
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data.json")
HTML = os.path.join(BASE, "index.html")
START = "<!-- DATA:START -->"
END = "<!-- DATA:END -->"


def build_block() -> str:
    """生成内联数据块。json 里的 '</' 转义成 '<\\/', 避免提前闭合 <script>。"""
    with open(DATA, encoding="utf-8") as f:
        raw = f.read()
    json.loads(raw)  # 先校验 JSON 合法
    payload = json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return (
        f"{START}\n"
        f"<!-- 由 sync_trip_data.py 从 data.json 生成,勿手改这段;改了跑一次脚本即可 -->\n"
        f'<script id="trip-data" type="application/json">{payload}</script>\n'
        f"{END}"
    )


def main() -> int:
    check = "--check" in sys.argv
    with open(HTML, encoding="utf-8") as f:
        html = f.read()

    block = build_block()
    if START in html and END in html:
        new_html = re.sub(
            re.escape(START) + r".*?" + re.escape(END), lambda _m: block, html, flags=re.S
        )
    else:
        # 首次插入: 放在 leaflet.js 引入之前
        anchor = re.search(r"<script src=\"https://cdn\.jsdelivr\.net/npm/leaflet[^\n]*></script>", html)
        if not anchor:
            print("找不到插入锚点(leaflet.js script 标签),中止", file=sys.stderr)
            return 2
        new_html = html[: anchor.start()] + block + "\n" + html[anchor.start():]

    if check:
        if new_html == html:
            print("✅ 一致: index.html 内联数据 与 data.json 同步")
            return 0
        print("❌ 不一致: data.json 改过但 index.html 内联数据没同步 → 跑 python3 sync_trip_data.py")
        return 1

    if new_html == html:
        print("✅ 已是最新,无需改动")
        return 0
    with open(HTML, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"✅ 已同步: data.json → index.html 内联数据块 ({len(block)} 字节)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
