#!/usr/bin/env python3
"""
阿里云短信通知模块
订单成功后自动发送短信到指定手机

依赖: pip3 install alibabacloud_dysmsapi20170525

配置: config.py 中设置 SMS_* 参数
"""

import json


def send_sms(phone: str, template_param: dict = None, sign_name: str = None,
             template_code: str = None, access_key: str = None,
             access_secret: str = None) -> bool:
    """
    发送短信
    :param phone: 手机号
    :param template_param: 模板变量 {"project":"xxx","price":"xxx"}
    :param sign_name: 短信签名
    :param template_code: 模板代码
    :param access_key: 阿里云 AccessKey
    :param access_secret: 阿里云 Secret
    """
    # 从 config 读取默认配置
    if any(x is None for x in [sign_name, template_code, access_key, access_secret]):
        try:
            from config import (
                SMS_SIGN_NAME, SMS_TEMPLATE_CODE,
                SMS_ACCESS_KEY, SMS_ACCESS_SECRET,
            )
            sign_name = sign_name or SMS_SIGN_NAME
            template_code = template_code or SMS_TEMPLATE_CODE
            access_key = access_key or SMS_ACCESS_KEY
            access_secret = access_secret or SMS_ACCESS_SECRET
        except ImportError:
            print("[SMS] ❌ config.py 未配置 SMS_* 参数")
            return False

    if not all([sign_name, template_code, access_key, access_secret]):
        print("[SMS] ❌ 缺少必要参数")
        return False

    try:
        from alibabacloud_dysmsapi20170525.client import Client
        from alibabacloud_dysmsapi20170525 import models as sms_models
        from alibabacloud_tea_openapi import models as open_api_models
    except ImportError:
        print("[SMS] ❌ 未安装SDK: pip install alibabacloud_dysmsapi20170525")
        return False

    config = open_api_models.Config(
        access_key_id=access_key,
        access_key_secret=access_secret,
    )
    config.endpoint = 'dysmsapi.aliyuncs.com'
    client = Client(config)

    request = sms_models.SendSmsRequest(
        phone_numbers=phone,
        sign_name=sign_name,
        template_code=template_code,
        template_param=json.dumps(template_param or {}, ensure_ascii=False),
    )

    try:
        response = client.send_sms(request)
        if response.body.code == 'OK':
            print(f"[SMS] 已发送到 {phone}")
            return True
        else:
            print(f"[SMS] ❌ {response.body.code}: {response.body.message}")
            return False
    except Exception as e:
        print(f"[SMS] ❌ {e}")
        return False


def notify_order_success(phone: str, project_name: str = "",
                         ticket_name: str = "", price: str = ""):
    """
    订单成功通知 (快捷方法)
    需要先在config.py配置SMS参数 + 阿里云短信模板
    """
    return send_sms(phone, template_param={
        "project": project_name or "演出",
        "ticket": ticket_name or "票",
        "price": str(price) or "0",
    })


if __name__ == "__main__":
    # 测试
    print("SMS模块加载正常")
    print("send_sms('13800138000', {'project':'测试'})")
