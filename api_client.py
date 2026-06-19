# API客户端处理Cookie、CSRF、请求签名、代理
import time
import hashlib
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from config import (
    API_BASE, HEADERS, BILIBILI_COOKIES,
    PROJECT_ID, SCREEN_ID, SKU_ID, BUY_COUNT,
    HTTP_PROXY, PROXY_USERNAME, PROXY_PASSWORD,
)
from fingerprint import BrowserFingerprint


def build_proxies(proxy_url: str = None, username: str = None, password: str = None) -> Optional[Dict[str, str]]:
    """
    构建 requests 代理字典
    支持 http / https / socks5
    """
    url = proxy_url or HTTP_PROXY
    if not url:
        return None

    # 添加认证信息到URL
    if username or PROXY_USERNAME:
        u = username or PROXY_USERNAME
        p = password or PROXY_PASSWORD
        parsed = urlparse(url)
        auth = f"{u}:{p}@" if p else f"{u}@"
        url = f"{parsed.scheme}://{auth}{parsed.hostname}"
        if parsed.port:
            url += f":{parsed.port}"

    return {
        "http": url,
        "https": url,
    }


class BilibiliTicketAPI:
    """B站票务API客户端"""

    def __init__(
        self,
        cookies: dict = None,
        fingerprint: BrowserFingerprint = None,
        proxy: str = None,
    ):
        """
        初始化客户端
        :param cookies: B站Cookie字典
        :param fingerprint: 浏览器指纹实例
        :param proxy: 代理URL, 如 "http://127.0.0.1:7890"
        """
        self.session = requests.Session()
        self.fingerprint = fingerprint or BrowserFingerprint()

        # 设置代理
        self.proxies = build_proxies(proxy)
        if self.proxies:
            self.session.proxies.update(self.proxies)
            print(f"[代理] 🌐 {list(self.proxies.values())[0]}")

        # 设置Cookie
        self.cookies = cookies or BILIBILI_COOKIES
        for key, value in self.cookies.items():
            self.session.cookies.set(key, value, domain=".bilibili.com")

        # 获取CSRF token (就是bili_jct)
        self.csrf = self.cookies.get("bili_jct", "")

        # 合并请求头
        self.headers = {**HEADERS, **self.fingerprint.get_headers()}
        self.session.headers.update(self.headers)

        # 统计
        self.request_count = 0
        self.last_request_time = 0

    def _sign_params(self, params: dict) -> dict:
        """添加通用签名参数"""
        params["t"] = int(time.time() * 1000)
        params["csrf"] = self.csrf
        params["csrf_token"] = self.csrf
        return params

    def _request(
        self,
        method: str,
        url: str,
        params: dict = None,
        data: dict = None,
        json_data: dict = None,
    ) -> Dict[str, Any]:
        """统一请求方法"""
        # 频率控制：最少间隔100ms
        elapsed = time.time() - self.last_request_time
        if elapsed < 0.1:
            time.sleep(0.1 - elapsed)

        full_url = f"{API_BASE}{url}"
        self.request_count += 1
        self.last_request_time = time.time()

        try:
            if method.upper() == "GET":
                resp = self.session.get(
                    full_url, params=params, timeout=10
                )
            else:  # POST
                if json_data:
                    resp = self.session.post(
                        full_url, json=json_data, timeout=10
                    )
                else:
                    resp = self.session.post(
                        full_url, data=data, timeout=10
                    )

            result = resp.json()
            return result

        except requests.RequestException as e:
            return {"code": -1, "errno": -1, "msg": str(e), "error": str(e)}
        except ValueError:
            return {"code": -1, "errno": -1, "msg": "JSON解析失败"}

    # ==================== 项目信息 ====================

    def get_project_detail(self, project_id: str = None) -> dict:
        """
        获取项目详情(含场次/票种列表)
        GET /api/ticket/project/get
        """
        pid = project_id or PROJECT_ID
        params = self._sign_params({"id": pid, "project_id": pid})
        return self._request("GET", "/ticket/project/get", params=params)

    def get_screen_info(self, screen_id: str = None) -> dict:
        """
        获取场次信息(含票种+座位图)
        GET /api/ticket/screen/info
        """
        sid = screen_id or SCREEN_ID
        params = self._sign_params({
            "project_id": PROJECT_ID,
            "screen_id": sid,
        })
        return self._request("GET", "/ticket/screen/info", params=params)

    # ==================== 验证相关 ====================

    def get_question(self, sku_id: str, component_id: str, token: str = "") -> dict:
        """
        获取验证问题/SKU信息
        GET /api/ticket/question/view
        返回: {errno, data: {is_use_question, question, ...}}
        """
        params = {
            "sku_id": sku_id,
            "component_id": component_id,
            "token": token,
            "t": int(time.time() * 1000),
        }
        return self._request("GET", "/ticket/question/view", params=params)

    def answer_question(self, answer_data: dict) -> dict:
        """
        提交验证答案
        POST /api/ticket/question/answer
        """
        return self._request("POST", "/ticket/question/answer", data=answer_data)

    def close_question(self) -> dict:
        """
        关闭验证弹窗
        POST /api/ticket/question/close
        """
        data = self._sign_params({})
        return self._request("POST", "/ticket/question/close", data=data)

    # ==================== 下单核心 ====================

    def prepare_order(self, order_data: dict) -> dict:
        """
        创建/准备订单 ⭐ 核心API
        POST /api/ticket/order/prepare (JSON格式!)
        """
        data = self._sign_params(order_data)
        return self._request("POST", "/ticket/order/prepare", json_data=data)

    def get_order_status(self, token: str) -> dict:
        """
        查询订单状态
        通过 token 轮询订单创建结果
        """
        params = {
            "token": token,
            "t": int(time.time() * 1000),
        }
        return self._request("GET", "/ticket/order/status", params=params)

    # ==================== 代理测试 ====================

    def test_proxy(self) -> bool:
        """测试代理连通性"""
        try:
            resp = self.session.get(
                "https://httpbin.org/ip",
                timeout=8,
            )
            data = resp.json()
            ip = data.get("origin", "unknown")
            print(f"[代理测试]  出口IP: {ip}")
            return True
        except Exception as e:
            print(f"[代理测试]  失败: {e}")
            return False

    # ==================== Cookie检查 ====================

    def check_login(self) -> bool:
        """检查登录状态"""
        resp = self.get_project_detail()
        if resp.get("errno") == 0 or resp.get("code") == 0:
            return True
        msg = str(resp.get("msg", ""))
        if "登录" in msg or "login" in msg.lower():
            return False
        return resp.get("errno") != -1

    def __repr__(self) -> str:
        px = "ON" if self.proxies else "OFF"
        return (
            f"BilibiliTicketAPI(\n"
            f"  uid={self.cookies.get('DedeUserID', '?')},\n"
            f"  csrf={self.csrf[:8]}...,\n"
            f"  proxy={px},\n"
            f"  requests={self.request_count},\n"
            f"  project={PROJECT_ID}\n"
            f")"
        )


if __name__ == "__main__":
    api = BilibiliTicketAPI()
    print(api)
    if api.proxies:
        api.test_proxy()
    print(f"登录状态: {api.check_login()}")
