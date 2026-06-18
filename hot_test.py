#!/usr/bin/env python3
"""
热门项目检测器
输入项目链接 → 检测 hotProject / ptoken / risk_level
"""

import re, json, requests, sys
from urllib.parse import urlparse, parse_qs

API = "https://show.bilibili.com/api/ticket/project/getV2"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Referer": "https://mall.bilibili.com/",
}


def check(url: str):
    # 提取 project_id
    m = re.search(r'/detail\.html\?id=(\d+)', url)
    if not m:
        # 也支持直接输入纯数字ID
        if url.strip().isdigit():
            pid = url.strip()
        else:
            print("❌ 无法识别，请输入完整链接或项目ID")
            return
    else:
        pid = m.group(1)

    print(f"🔍 检测项目 {pid} ...\n")

    try:
        resp = requests.get(API, params={"id": pid, "project_id": pid}, headers=HEADERS, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return

    if data.get("errno") != 0:
        print(f"❌ API错误: {data.get('msg')}")
        return

    d = data["data"]
    name = d.get("name", "?")
    hot = d.get("hotProject", False)
    screens = d.get("screen_list", [])

    print(f"📌 {name}")
    print(f"{'─'*40}")
    print(f"  hotProject : {'🔥 是 (有额外风控)' if hot else '✅ 否 (无额外风控)'}")
    print(f"  场次数    : {len(screens)}")

    for s in screens[:3]:
        sid = s.get("id")
        sname = s.get("name", "?")
        flag = s.get("sale_flag", {}).get("display_name", "?")
        tickets = s.get("ticket_list", [])
        print(f"  ├─ 场次 {sid} {sname} [{flag}]")
        for t in tickets[:3]:
            tname = t.get("desc") or "?"
            print(f"  │  🎟️ {t.get('id')} {tname} ¥{t.get('price',0)/100:.2f}")
        if len(tickets) > 3:
            print(f"  │  ... 共{len(tickets)}种票")
    if len(screens) > 3:
        print(f"  └─ ... 共{len(screens)}个场次")

    print(f"\n{'─'*40}")
    if hot:
        print("⚠️ 热门项目！需要 ptoken/ctoken 指纹验证")
        print("   请使用 auto_buy.py (已支持热门项目)")
    else:
        print("✅ 普通项目，可直接用 auto_buy.py")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        check(sys.argv[1])
    else:
        url = input("项目链接: ").strip()
        check(url)
