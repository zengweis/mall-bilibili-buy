# B站会员购 - 自动化下单工具

##  快速开始

```bash
# 1. 安装依赖
requests>=2.28.0
urllib3>=1.26.0
qrcode>=7.4
brotli>=1.0
playwright>=1.40
alibabacloud_dysmsapi20170525>=3.0.0
其中alibabacloud_dysmsapi20170525>=3.0.0为阿里云短信sdk，如果没有企业资质短信接口不用加

# 2. 扫码登录 + 选票种 (一键配置)
python3 login.py

# 3. 全自动下单
python3 auto_buy.py
```

## 文件说明

| `auto_buy.py` | 自动下单
| `login.py` |  扫码登录 + 配置
| `config.py` |  Cookie/项目/代理配置 
| `api_client.py` |  API客户端 (Cookie/CSRF/签名/代理) 


##  配置

编辑 `auto_buy.py` 顶部或 `config.py`：
建议使用login.py进行配置，不建议手动修改，并且推荐购买实名票时数量为1
```python
PROJECT_ID = ""    # 项目ID
SCREEN_ID = ""     # 场次ID
SKU_ID = ""         # 票种SKU
COUNT = 1                 # 数量
PAY_MONEY = 10800         # 金额(分)

PROXY = ""                # 浏览器代理 
CONTACT_NAME = ""     # 联系人
CONTACT_TEL = ""
```

##  代理设置


```
# config.py 
HTTP_PROXY = "http://127.0.0.1:7890"
```

##  注意事项

- Cookie 有效期约1个月，过期后重新 `python login.py`
- `login.py` 在终端显示二维码

 本代码仅供个人学习，有意向交流请mail：zeng@tsunako.fun我会答复
 使用本项目请自行承担法律责任，禁止商业化使用