# B站会员购 - 自动化下单工具 v2.0

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install requests brotli qrcode playwright
python -m playwright install chromium

# 2. 扫码登录 + 选票种 (一键配置)
python login.py

# 3. 全自动下单
python auto_buy.py
```

## 📁 文件说明

| 文件 | 功能 | 推荐度 |
|------|------|--------|
| `auto_buy.py` | 🎯 一站式全自动下单 (prepare+确认) | ⭐⭐⭐ |
| `login.py` | 🔐 扫码登录 + 选票种向导 | ⭐⭐⭐ |
| `main.py` | 🚀 test / quick / monitor | ⭐⭐ |
| `confirm_browser.py` | 🖥️ Playwright确认下单 (单独使用) | ⭐ |
| `config.py` | ⚙️ Cookie/项目/代理配置 | - |
| `api_client.py` | 🌐 API客户端 | - |
| `order.py` | 🛒 订单管理 | - |

## 🎮 使用模式

### 模式1: 全自动 (推荐)

```bash
python auto_buy.py
```

prepare 秒锁 + 浏览器自动打开确认页 + 自动填信息 + 自动点下一步 → 跳支付页面

### 模式2: 监听开售

```bash
python main.py monitor
```

轮询项目状态 → 开售瞬间 prepare → 输出确认链接 → 浏览器打开点确认

### 模式3: 手动

```bash
python main.py quick    # prepare下单 → 输出链接
# 手动浏览器打开链接 → 点下一步
```

## ⚙️ 配置

编辑 `auto_buy.py` 顶部或 `config.py`：
建议使用login.py进行配置，不建议手动修改，并且推荐票数量为1
```python
PROJECT_ID = ""    # 项目ID
SCREEN_ID = ""     # 场次ID
SKU_ID = ""         # 票种SKU
COUNT = 1                 # 数量
PAY_MONEY = 10800         # 金额(分)

PROXY = ""                # 浏览器代理 (海外用户需要)
CONTACT_NAME = ""     # 联系人
CONTACT_TEL = ""
```

## 🌐 代理设置


```python
# login.py
LOGIN_PROXY = "http://127.0.0.1:7890"

# auto_buy.py  
PROXY = "http://127.0.0.1:7890"

# config.py (main.py用)
HTTP_PROXY = "http://127.0.0.1:7890"
```

## ⚠️ 注意事项

- Cookie 有效期约1个月，过期后重新 `python login.py`
- `login.py` 在终端显示二维码

 
