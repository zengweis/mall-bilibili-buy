
#B站Cookie
# 从浏览器F12 → Application → Cookies → .bilibili.com 复制
# 非特殊请通过login.py配置项目自动填入
BILIBILI_COOKIES = {
    "SESSDATA": "4813b7RWtkMy1xQ05XWENVeXJjeM0lRNjVDWDZnIIEC",
    "bili_jct": "12840b0a8495",
    "DedeUserID": "625",
    "DedeUserID__ckMd5": "a1dec66f95",
    "sid": "eesw0qby",
}

# 项目信息，非特殊请通过login.py配置项目自动填入
# 从票务页面URL获取: https://show.bilibili.com/platform/detail.html?id=XXXXX
PROJECT_ID = "1001405"

# 场次ID (从页面F12抓包 screen_list 里找)
SCREEN_ID = "1004870"

# 票种SKU ID (从页面F12抓包 ticket_list 里找)
SKU_ID = "877298"

# 购买数量
BUY_COUNT = 1

# 支付金额 (分) - 票价 * 数量无特殊请不要改
PAY_MONEY = 1000

# 订单类型 (1=普通, 3=套票, 5=众筹)
ORDER_TYPE = 1

# ==================== 代理配置 ====================
# HTTP代理，支持 http/https/socks5
# 格式: "http://127.0.0.1:7890" 或 "socks5://127.0.0.1:1080"
# 留空 = 不使用代理
HTTP_PROXY = "http://127.0.0.1:7890"

# 代理认证 (如果需要)
PROXY_USERNAME = ""
PROXY_PASSWORD = ""

# ==================== 请求配置 ====================
API_BASE = "https://show.bilibili.com/api"

# 请求头 
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": f"https://show.bilibili.com/platform/detail.html?id={PROJECT_ID}",
    "Origin": "https://show.bilibili.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

# ==================== 轮询配置 ====================
# 订单状态轮询最大次数
MAX_POLL_RETRIES = 20
# 前4次轮询的最大延迟(秒)
EARLY_POLL_MAX_DELAY = 2.0
# 4次后的最大延迟(秒)
LATE_POLL_MAX_DELAY = 6.0

# ==================== 开售监听 ====================
# 监听开售的轮询间隔(秒)
SALE_MONITOR_INTERVAL = 0.5

# ==================== 短信通知 ====================
# 阿里云短信服务 (订单成功时通知)
SMS_ACCESS_KEY = ""       # 阿里云 AccessKey ID
SMS_ACCESS_SECRET = ""    # 阿里云 AccessKey Secret
SMS_SIGN_NAME = ""        # 短信签名
SMS_TEMPLATE_CODE = ""    # 短信模板代码
SMS_PHONE = ""            # 接收手机号

# ==================== 运行模式 ====================
LOOP_MODE = True         # 无限重试
RETRY_DELAY = 0.3        # 重试间隔秒
NTP_ENABLED = True       # NTP同步
LEAD_MS = 200            # 提前触发ms

#联系人，购票人自动获取第一位，请提前测试购票人信息是否符合预期
CONTACT_NAME = ""
CONTACT_TEL = ""

# 留空=立即抢, 如需定时，格式："2026-07-24 10:00:00"

# 新版无特殊需求留空即可，程序会自动获取开售时间并定时开抢
SCHEDULE_TIME = ""
