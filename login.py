#!/usr/bin/env python3
"""
B站扫码登录 - Cookie + 项目配置一键搞定
==========================================
用法:
  python login.py
  
  终端显示二维码 → 手机扫码 → 自动提取Cookie
  → 输入项目链接 → 列出场次票种 → 选择配置 → 一键写入 config.py
"""

import sys
import os
import time
import re
import json
import requests
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs


# ==================== 配置 ====================

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.py")

API_QR_GENERATE = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
API_QR_POLL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
API_NAV = "https://api.bilibili.com/x/web-interface/nav"
API_PROJECT_DETAIL = "https://show.bilibili.com/api/ticket/project/getV2"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://mall.bilibili.com/",
    "Origin": "https://mall.bilibili.com",
}

# ==================== 代理 ====================
# 如果B站API被墙，设置代理
# 格式: "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"
LOGIN_PROXY = ""


# ==================== 二维码显示 ====================

def print_qr_color(url: str):
    """彩色终端二维码"""
    import qrcode
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.modules
    size = len(matrix)

    print("  " + "▄" * (size * 2 + 2))
    for row in matrix:
        line = "  █"
        for cell in row:
            line += "\033[40m  \033[0m" if cell else "\033[47m  \033[0m"
        line += "█"
        print(line)
    print("  " + "▀" * (size * 2 + 2))


# ==================== 登录流程 ====================

class BilibiliLogin:
    """B站扫码登录 + 项目配置"""

    def __init__(self, proxy: str = None):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

        # 代理
        px = proxy or LOGIN_PROXY
        if px:
            self.session.proxies = {"http": px, "https": px}
            print(f"[代理] 🌐 {px}")

        self.qrcode_key: Optional[str] = None
        self.cookies: Dict[str, str] = {}

    def generate_qrcode(self) -> str:
        """生成登录二维码"""
        print("[1/4] 请求登录二维码...", end=" ")
        resp = self.session.get(API_QR_GENERATE, timeout=10)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"获取二维码失败: {data}")
        self.qrcode_key = data["data"]["qrcode_key"]
        qr_url = data["data"]["url"]
        print("✅")
        print(f"\n{'='*50}")
        print(f"  📱 请用「哔哩哔哩APP」扫描二维码登录")
        print(f"{'='*50}\n")
        print_qr_color(qr_url)
        print(f"\n  密钥: {self.qrcode_key[:16]}...\n")
        return qr_url

    def poll_scan(self, timeout: int = 180) -> Optional[str]:
        """轮询扫码状态"""
        print("[2/4] 等待扫码...", end="", flush=True)
        start = time.time()
        last_status = ""

        while time.time() - start < timeout:
            try:
                resp = self.session.get(
                    API_QR_POLL,
                    params={"qrcode_key": self.qrcode_key},
                    timeout=5,
                )
                data = resp.json()
                if data.get("code") != 0:
                    time.sleep(1)
                    continue

                inner = data.get("data", {})
                code = inner.get("code", -1)

                if code == 86101:  # 未扫码
                    if last_status != "waiting":
                        print(f"\r[2/4] ⏳ 等待扫码...", end="", flush=True)
                        last_status = "waiting"
                    time.sleep(2)
                elif code == 86090:  # 已扫码
                    if last_status != "scanned":
                        print(f"\r[2/4] 📱 已扫码，请确认...", end="", flush=True)
                        last_status = "scanned"
                    time.sleep(1)
                elif code == 0:  # 成功
                    print(f"\r[2/4] ✅ 登录成功！          ")
                    return inner.get("url", "")
                elif code == 86038:  # 过期
                    print(f"\r[2/4] ❌ 二维码已过期")
                    return None
                else:
                    time.sleep(1)
            except requests.RequestException as e:
                print(f"\r[2/4] ⚠️  {e}")
                time.sleep(2)

        print(f"\r[2/4] ⏰ 超时")
        return None

    def extract_cookies(self, confirm_url: str) -> Dict[str, str]:
        """提取Cookie"""
        print("[3/4] 提取登录信息...", end=" ", flush=True)
        self.session.get(confirm_url, allow_redirects=True, timeout=10)

        cookies = {}
        for cookie in self.session.cookies:
            domain = cookie.domain or ""
            if "bilibili.com" in domain or domain == "":
                cookies[cookie.name] = cookie.value

        self.cookies = cookies
        print("✅")
        return cookies

    def verify_login(self) -> Optional[dict]:
        """验证登录，返回用户信息"""
        print("[验证] 检查登录状态...", end=" ", flush=True)
        try:
            resp = self.session.get(API_NAV, timeout=10)
            data = resp.json()
            if data.get("code") == 0 and data.get("data", {}).get("isLogin"):
                user = data["data"]
                print("✅")
                print(f"\n  昵称: {user.get('uname', '?')}")
                print(f"  UID:   {user.get('mid', '?')}")
                level = user.get('level_info', {}).get('current_level', '?')
                print(f"  等级:  Lv{level}  💰{user.get('money', '?')}")
                return user
            else:
                print("❌")
                return None
        except Exception as e:
            print(f"❌ {e}")
            return None

    def run(self) -> bool:
        """完整登录流程"""
        print(r"""
╔══════════════════════════════════════╗
║   🔐 B站扫码登录 - 一键配置工具 🔐   ║
╚══════════════════════════════════════╝
""")
        try:
            self.generate_qrcode()
            confirm_url = self.poll_scan(timeout=180)
            if not confirm_url:
                return False
            self.extract_cookies(confirm_url)
            user = self.verify_login()
            return user is not None
        except KeyboardInterrupt:
            print("\n\n⏹️  用户取消")
            return False
        except Exception as e:
            print(f"\n❌ {e}")
            return False


# ==================== 项目配置向导 ====================

def select_project(cookies: Dict[str, str]) -> Optional[dict]:
    """
    交互式选择项目场次票种
    返回配置字典
    """
    print(f"\n{'='*50}")
    print(f"  🎫 项目配置向导")
    print(f"{'='*50}\n")

    # Step 1: 获取项目链接
    default_url = "https://mall.bilibili.com/neul-next/ticket-renovation/detail.html?id=1001424"
    print(f"项目链接 (支持 show/mall 格式):")
    print(f"  [{default_url}]")
    try:
        url = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    if not url:
        url = default_url

    # 提取 PROJECT_ID
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    project_id = params.get("id", [None])[0]
    if not project_id:
        # 尝试从路径提取
        m = re.search(r'[/?&]id=(\d+)', url)
        if m:
            project_id = m.group(1)
    if not project_id:
        print("❌ 无法从URL提取项目ID")
        return None
    print(f"\n  📌 PROJECT_ID = {project_id}")

    # Step 2: 请求项目详情
    print(f"\n  正在获取项目信息...", end=" ", flush=True)
    session = requests.Session()
    session.headers.update(HEADERS)
    for key, value in cookies.items():
        session.cookies.set(key, value, domain=".bilibili.com")

    csrf = cookies.get("bili_jct", "")
    params_req = {
        "id": project_id,
        "project_id": project_id,
        "t": int(time.time() * 1000),
        "csrf": csrf,
    }
    try:
        resp = session.get(API_PROJECT_DETAIL, params=params_req, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"❌\n  请求失败: {e}")
        return None

    err = data.get("errno", data.get("code", 0))
    if err != 0 and not data.get("success"):
        msg = data.get('msg', data.get('message', str(data)[:100]))
        print(f"❌\n  API错误: {msg}")
        if '系统繁忙' in str(msg) or '100011' in str(err):
            print("   💡 该项目可能是私密/定向邀请项目，API不可达")
        return None

    project = data.get("data", {})
    print("✅")
    print(f"\n  项目: {project.get('name', '?')}")
    sale_flag = project.get("sale_flag_number", "?")
    print(f"  状态: {'🟢 在售' if sale_flag == 1 else '🔴 未开售'} (flag={sale_flag})")

    # Step 3: 列出并选择场次
    screens = project.get("screen_list", [])
    if not screens:
        print("❌ 没有可用场次")
        return None

    print(f"\n{'─'*40}")
    print(f"  📅 场次列表 ({len(screens)}个):")
    print(f"{'─'*40}")
    for i, s in enumerate(screens):
        sid = s.get("id", "?")
        name = s.get("name", "?")
        flag = s.get("sale_flag_number", "?")
        stime = s.get("start_time", "?")
        flag_icon = "🟢" if flag == 1 else "🔴"
        print(f"  [{i+1}] {flag_icon} ID:{sid}")
        print(f"      {name} | {stime}")

    print(f"\n  请选择场次 (1-{len(screens)}):")
    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(screens):
            print("❌ 无效选择")
            return None
    except ValueError:
        print("❌ 请输入数字")
        return None

    screen = screens[idx]
    screen_id = str(screen.get("id", ""))
    print(f"\n  ✅ 已选择: {screen.get('name')} (SCREEN_ID={screen_id})")

    # Step 4: 列出并选择票种
    tickets = screen.get("ticket_list", [])
    if not tickets:
        # 可能需要单独请求场次详情
        print("  ⚠️  场次无票种列表，尝试单独请求...")
        screen_info_url = "https://show.bilibili.com/api/ticket/screen/info"
        params2 = {
            "project_id": project_id,
            "screen_id": screen_id,
            "t": int(time.time() * 1000),
            "csrf": csrf,
        }
        try:
            resp2 = session.get(screen_info_url, params=params2, timeout=10)
            d2 = resp2.json()
            if d2.get("errno") == 0:
                tickets = d2.get("data", {}).get("ticket_list", [])
        except Exception:
            pass

    if not tickets:
        print("❌ 没有可用票种")
        return None

    print(f"\n{'─'*40}")
    print(f"  🎟️  票种列表 ({len(tickets)}个):")
    print(f"{'─'*40}")
    for i, t in enumerate(tickets):
        tid = t.get("id", "?")
        tname = t.get("desc") or t.get("name", "?")
        price = t.get("price", 0) / 100
        stock = t.get("num", "?")
        flag = t.get("sale_flag", {}).get("display_name", "?")
        print(f"  [{i+1}] SKU:{tid}")
        print(f"      {tname} | ¥{price:.2f} | 库存:{stock} | {flag}")

    print(f"\n  请选择票种 (1-{len(tickets)}):")
    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(tickets):
            print("❌ 无效选择")
            return None
    except ValueError:
        print("❌ 请输入数字")
        return None

    ticket = tickets[idx]
    sku_id = str(ticket.get("id", ""))
    price = ticket.get("price", 0) / 100
    print(f"\n  ✅ 已选择: {ticket.get('name')} ¥{price:.2f} (SKU_ID={sku_id})")

    # Step 5: 数量
    max_num = ticket.get("num", 1)
    if isinstance(max_num, str):
        try:
            max_num = int(max_num)
        except ValueError:
            max_num = 1
    max_num = max(1, min(max_num, 10))  # 限制最多10张

    print(f"\n  购买数量 (1-{max_num}, 默认1):")
    try:
        choice = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    try:
        count = int(choice) if choice else 1
        count = max(1, min(count, max_num))
    except ValueError:
        count = 1

    print(f"\n  ✅ 购买数量: {count}")

    order_type = 1  # 默认普通订单
    sale_type = ticket.get("sale_type", 1)
    if sale_type == 3:
        order_type = 5  # 套票/特殊

    return {
        "project_id": project_id,
        "screen_id": screen_id,
        "sku_id": sku_id,
        "count": count,
        "pay_money": ticket.get("price", 0) * count,  # 分
        "order_type": order_type,
        "project_name": project.get("name", ""),
        "screen_name": screen.get("name", ""),
        "ticket_name": ticket.get("desc") or ticket.get("name", ""),
        "ticket_price": price,
    }


# ==================== 写入配置 ====================

def update_config(cookies: Dict[str, str], project_cfg: dict = None):
    """写入 config.py"""
    print(f"\n{'='*50}")
    print(f"  💾 写入配置")
    print(f"{'='*50}\n")

    if not os.path.exists(CONFIG_FILE):
        print("❌ config.py 不存在")
        return False

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 更新 Cookie
    new_cookies = {
        "SESSDATA": cookies.get("SESSDATA", "你的SESSDATA"),
        "bili_jct": cookies.get("bili_jct", "你的bili_jct"),
        "DedeUserID": cookies.get("DedeUserID", "你的UID"),
        "DedeUserID__ckMd5": cookies.get("DedeUserID__ckMd5", "你的ckMd5"),
        "sid": cookies.get("sid", "你的sid"),
    }
    cookie_lines = []
    for key, value in new_cookies.items():
        cookie_lines.append(f'    "{key}": "{value}",')
    cookie_block = "BILIBILI_COOKIES = {\n" + "\n".join(cookie_lines) + "\n}"

    pattern = r"BILIBILI_COOKIES\s*=\s*\{[^}]*\}"
    if re.search(pattern, content):
        content = re.sub(pattern, cookie_block, content)
        print("  ✅ Cookie 已更新")
    else:
        print("  ⚠️  未找到 BILIBILI_COOKIES")

    # 2. 更新项目配置
    if project_cfg:
        updates = {
            "PROJECT_ID": f'PROJECT_ID = "{project_cfg["project_id"]}"',
            "SCREEN_ID": f'SCREEN_ID = "{project_cfg["screen_id"]}"',
            "SKU_ID": f'SKU_ID = "{project_cfg["sku_id"]}"',
            "BUY_COUNT": f"BUY_COUNT = {project_cfg['count']}",
            "PAY_MONEY": f"PAY_MONEY = {project_cfg.get('pay_money', 0)}",
            "ORDER_TYPE": f"ORDER_TYPE = {project_cfg.get('order_type', 1)}",
        }
        for key, new_line in updates.items():
            pattern = rf'{key}\s*=\s*".*"'
            if key in ("BUY_COUNT", "PAY_MONEY", "ORDER_TYPE"):
                pattern = rf'{key}\s*=\s*\d+'
            if re.search(pattern, content):
                content = re.sub(pattern, new_line, content)
                print(f"  ✅ {key} 已更新")
            else:
                print(f"  ⚠️  未找到 {key}")

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  📁 已保存到: {CONFIG_FILE}")
    return True


# ==================== 快捷函数 ====================

def quick_setup(cookies: Dict[str, str], project_url: str = None):
    """
    快速配置：直接用Cookie+URL获取项目信息并返回配置
    不需要交互输入
    """
    if not project_url:
        return None

    parsed = urlparse(project_url)
    params = parse_qs(parsed.query)
    project_id = params.get("id", [None])[0]
    if not project_id:
        m = re.search(r'/detail\.html\?id=(\d+)', project_url)
        if m:
            project_id = m.group(1)
    if not project_id:
        return None

    session = requests.Session()
    session.headers.update(HEADERS)
    for key, value in cookies.items():
        session.cookies.set(key, value, domain=".bilibili.com")

    csrf = cookies.get("bili_jct", "")
    req_params = {
        "id": project_id, "project_id": project_id,
        "t": int(time.time() * 1000), "csrf": csrf,
    }

    try:
        resp = session.get(API_PROJECT_DETAIL, params=req_params, timeout=10)
        data = resp.json()
    except Exception:
        return None

    if data.get("errno") != 0:
        return None

    project = data.get("data", {})
    screens = project.get("screen_list", [])

    result = {
        "project_id": project_id,
        "project_name": project.get("name", ""),
        "screens": [],
    }

    for s in screens:
        screen_info = {
            "id": str(s.get("id", "")),
            "name": s.get("name", ""),
            "start_time": s.get("start_time", ""),
            "sale_flag": s.get("sale_flag_number", 0),
            "tickets": [],
        }
        for t in s.get("ticket_list", []):
            screen_info["tickets"].append({
                "id": str(t.get("id", "")),
                "name": t.get("desc") or t.get("name", ""),
                "price": t.get("price", 0) / 100,
                "num": t.get("num", 0),
                "sale_type": t.get("sale_type", 0),
            })
        result["screens"].append(screen_info)

    return result


# ==================== 主入口 ====================

def main():
    print(r"""
╔══════════════════════════════════════╗
║   🔐 B站票务 - 配置向导 v2.0       ║
╚══════════════════════════════════════╝
""")

    cookies = {}
    need_login = True

    print(f"扫码登录? [Y/n]: ", end="", flush=True)
    try: choice = input().strip().lower()
    except: choice = "y"

    if choice in ("n", "no"):
        if os.path.exists(CONFIG_FILE):
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", CONFIG_FILE)
            cfg = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cfg)
            cookies = cfg.BILIBILI_COOKIES
            need_login = False
            print(f"使用已有Cookie (UID={cookies.get('DedeUserID','?')})\n")
        else:
            print("config.py 不存在"); sys.exit(1)

    if need_login:
        login = BilibiliLogin()
        if not login.run() or not login.cookies:
            print("\n登录失败"); sys.exit(1)
        cookies = login.cookies

    print(f"\n  配置项目? [Y/n]: ", end="", flush=True)
    try: choice = input().strip().lower()
    except: choice = "y"

    if choice in ("", "y", "yes"):
        cfg = select_project(cookies)
        if cfg:
            if update_config(cookies, cfg):
                print(f"\n  项目: {cfg['project_name']}")
                print(f"  票种: {cfg['ticket_name']} x{cfg['count']}")
                print(f"  config.py 已更新! 运行: python auto_buy.py")
                return
    else:
        update_config(cookies)

    print("\n完成喵~")

if __name__ == "__main__":
    main()
