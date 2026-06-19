import sys, time, json, concurrent.futures
from datetime import datetime
from config import (BILIBILI_COOKIES, PROJECT_ID, SCREEN_ID, SKU_ID, BUY_COUNT, PAY_MONEY, ORDER_TYPE, HTTP_PROXY, SMS_PHONE, LOOP_MODE, RETRY_DELAY, NTP_ENABLED, LEAD_MS, CONTACT_NAME, CONTACT_TEL, SCHEDULE_TIME)

CSRF = BILIBILI_COOKIES.get("bili_jct","")
API_BASE = "https://show.bilibili.com/api/ticket"
MALL_API = "https://mall.bilibili.com/mall-search-items/items_detail/info"

# 移动端UA
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148"
WEB_LOCATION = "mall.ticket-detail"

def _log(tag, msg):
    now = datetime.now().strftime("%H:%M:%S.")
    ms = str(int(time.time()*1000))[-3:]
    print(f"[{now}{ms}] [{tag:>7}] {msg}")

def gen_web_ticket(session):
    """防机器人令牌 (可选, 失败不影响)"""
    try:
        r = session.post('https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket', json={
            'key_id':'ec02','hexsign':'test'
        }, timeout=3)
        if r.json().get('code')==0:
            return r.json().get('data',{}).get('ticket','')
    except: pass
    return ""

def exhibit_watch(session, pid):
    """查看实时购买动态"""
    try:
        r = session.get(f'{API_BASE}/order/exhibit?itemId={pid}', timeout=5)
        buyers = r.json().get('data',{}).get('list',[])
        if buyers:
            latest = buyers[0]
            _log("WATCH", f"{latest.get('username','?')} {latest.get('timeTxt','?')}买了")
    except: pass

def auto_buy():
    print(r"""
╔══════════════════════════════════════╗
║   🎫 B站ticket buy   🎫  ║
╚══════════════════════════════════════╝""")
    print(f"[配置] 项目={PROJECT_ID} 场次={SCREEN_ID} 票种={SKU_ID} x{BUY_COUNT}")
    print(f"      联系人={CONTACT_NAME} {CONTACT_TEL[:3]}****")
    t0 = time.time()

    import requests as _r
    http = _r.Session()
    http.headers.update({
        "User-Agent": UA,
        "Referer": f"https://mall.bilibili.com/neul-next/ticket-renovation/detail.html?id={PROJECT_ID}",
        "Origin": "https://mall.bilibili.com",
        "Content-Type": "application/json",
        "Connection": "keep-alive",
    })
    for k,v in BILIBILI_COOKIES.items(): http.cookies.set(k,v,domain=".bilibili.com")
    if HTTP_PROXY: http.proxies = {"http":HTTP_PROXY,"https":HTTP_PROXY}
    _log("HTTP","Session 就绪")

    # 新版防机器人令牌 (可选)
    ticket = gen_web_ticket(http)
    if ticket: _log("TICKET", f"GenWebTicket={ticket[:20]}...")

    # 看看谁在买
    exhibit_watch(http, PROJECT_ID)

    # 检测开售
    _log("CHECK","检测票种...")
    try:
        from timer import ntp_time, countdown
        # 先用旧API
        pre = http.get(f"{API_BASE}/project/getV2?id={PROJECT_ID}&project_id={PROJECT_ID}",timeout=8)
        pd = pre.json().get("data",{})
        # 如果旧API返回空/100011，尝试新API
        if not pd or pre.json().get("code")==100011:
            _log("CHECK","旧API不可用，尝试新API...")
            r2 = http.post(MALL_API, json={"itemsId":int(PROJECT_ID),"itemsDetailPageType":3}, timeout=8)
            mall_data = r2.json().get("data",{})
            if mall_data:
                bi = mall_data.get("basicInfoFloorVO",{})
                mp = mall_data.get("mergeAtmospherePriceFloorVO",{}).get("mergePriceInfoVO",{})
                _log("CHECK",f"新API: {bi.get('itemsName','?')} ¥{mp.get('leftVO',{}).get('leftTopVO',{}).get('mainPriceVOs',[{}])[0].get('priceIntegerPart','?')}-{mp.get('leftVO',{}).get('leftTopVO',{}).get('mainPriceVOs',[{}])[-1].get('priceIntegerPart','?')}")
                _log("CHECK"," 新API无SKU字段，请手动填SCREEN_ID/SKU_ID")
        ts=0; tn=""
        for s in pd.get("screen_list",[]):
            if str(s.get("id"))==SCREEN_ID:
                for t in s.get("ticket_list",[]):
                    if str(t.get("id"))==SKU_ID:
                        ts=t.get("saleStart",0); tn=t.get("desc",""); break; break
        _log("CHECK",f"{tn} saleFlag={t.get('sale_flag_number',-1)} start={ts}")
        if ts and ts>time.time():
            _log("CHECK",f"未开售! {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
            while time.time()<ts-5:
                countdown(ts)
                if int(time.time())%60<1 and NTP_ENABLED:
                    try: ntp=ntp_time(fast=True);_log("NTP",f"偏差{(ntp-time.time())*1000:+.0f}ms")
                    except: pass
                exhibit_watch(http, PROJECT_ID)  # 顺便看看谁在买
                time.sleep(57)
            _log("CHECK","开售!")
    except Exception as e:
        _log("CHECK",str(e))

    # 并发 prepare
    _log("PREPARE","5并发下单...")
    t1=time.time()
    best_token = None
    all_results = []
    def do_prepare():
        nonlocal best_token
        r=http.post(f"{API_BASE}/order/prepare",json={
            "project_id":PROJECT_ID,"screen_id":SCREEN_ID,"sku_id":SKU_ID,
            "count":BUY_COUNT,"order_type":ORDER_TYPE,"pay_money":PAY_MONEY,
            "token":ticket,"newRisk":True,
            "csrf":CSRF,"csrf_token":CSRF,"t":int(time.time()*1000),
        },timeout=5)
        d=r.json()
        all_results.append(d)
        if d.get("errno")==0:
            tk=d["data"]["token"]
            if not best_token: best_token=tk
        return d.get("errno")
    
    with concurrent.futures.ThreadPoolExecutor(5) as ex:
        results = list(ex.map(lambda _: do_prepare(), range(5)))
    ok = sum(1 for r in results if r==0)
    _log("PREPARE",f"{ok}/5成功 {((time.time()-t1)*1000):.0f}ms")
    if best_token: _log("PREPARE",f"token={best_token[:30]}...")
    # 输出prepare响应
    for i, d in enumerate(all_results):
        e = d.get('errno',-1); m = d.get('msg','')
        t = d.get('data',{}).get('token','')[:25] if d.get('data') else ''
        print(f"      [{i+1}] errno={e} {m[:30]} {t}")
    if not best_token: _log("PREPARE","全部失败"); return False

    # 购票人
    _log("BUYER","获取购票人...")
    try:
        br = http.get(f"{API_BASE}/buyer/list?csrf={CSRF}&project_id={PROJECT_ID}",timeout=5)
        buyer_data = br.json().get("data",{}).get("list",[])
    except:
        buyer_data = []

    buyer_info = json.dumps([{
        "id":b.get("id",0),"uid":b.get("uid",0),
        "account_channel":b.get("account_channel",""),
        "personal_id":b.get("personal_id",""),
        "name":b.get("name",""),
        "id_card_front":b.get("id_card_front",""),
        "id_card_back":b.get("id_card_back",""),
        "is_default":b.get("is_default",0),
        "tel":b.get("tel",""),
        "error_code":b.get("error_code",""),
        "id_type":b.get("id_type",1),
        "verify_status":b.get("verify_status",1),
        "accountId":b.get("accountId",0),
    } for b in buyer_data[:1]]) if buyer_data else "[]"

    deliver_info = json.dumps({"name":CONTACT_NAME,"tel":CONTACT_TEL,"addr_id":0,"addr":""})

    _log("CREATE",f"提交...")
    last_resp = None
    for attempt in range(60):
        timestamp = int(time.time()*1000)
        create_body = {
            "count":BUY_COUNT,"screen_id":int(SCREEN_ID),"project_id":int(PROJECT_ID),
            "sku_id":int(SKU_ID),"order_type":ORDER_TYPE,"pay_money":PAY_MONEY,
            "buyer_info":buyer_info,"buyer":CONTACT_NAME,"tel":CONTACT_TEL,
            "deliver_info":deliver_info,"again":1 if attempt>0 else 0,
            "token":best_token,"timestamp":timestamp,
            "csrf":CSRF,"csrf_token":CSRF,"t":timestamp,
        }
        r = http.post(f"{API_BASE}/order/createV2?project_id={PROJECT_ID}", json=create_body, timeout=5)
        d = r.json()
        errno = d.get("errno",-1); msg = d.get("msg","")
        last_resp = d
        if errno == 0:
            _log("CREATE",f"🎉 orderId={d.get('data',{}).get('orderId','')}")
            if SMS_PHONE:
                try:
                    from sms import notify_order_success; notify_order_success(SMS_PHONE)
                    _log("SMS","ok")
                except: pass
            return True
        status = "🔄" if errno in (900001,1) else "❌"
        _log("CREATE",f"[{attempt+1:02d}/60] {status} errno={errno} {msg[:50]}")
        if errno in (100048,100079): return True
        if errno == 100051: break
        if errno == 100034:
            np = d.get("data",{}).get("pay_money",0)
            if np: create_body["pay_money"]=np
        if errno == 100009: return False
        time.sleep(0.3 if errno==1 else 0.15)

    # 最后响应
    if last_resp:
        _log("CREATE",f"最终: errno={last_resp.get('errno')} {last_resp.get('msg','')[:50]}")
        data = last_resp.get('data',{})
        if data:
            _log("CREATE",f"data: orderId={data.get('orderId','?')} pay_money={data.get('pay_money','?')}")
    return False


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--time","-t",help="手动指定开售时间")
    p.add_argument("--once",action="store_true",help="仅执行一次")
    args=p.parse_args()

    schedule = args.time or SCHEDULE_TIME
    if schedule:
        target=datetime.strptime(schedule,"%Y-%m-%d %H:%M:%S").timestamp()
        from timer import ntp_time,countdown,wait_until_ntp
        if NTP_ENABLED:
            now=ntp_time();print(f"NTP偏差:{(now-time.time())*1000:+.0f}ms")
            remaining=target-now
        else:remaining=target-time.time()
        if remaining>0:
            countdown(target)
            if NTP_ENABLED:wait_until_ntp(target,lead_ms=LEAD_MS)

    if LOOP_MODE and not args.once:
        a=0;ok=0;nok=0
        print(f"\n无限重试(间隔{RETRY_DELAY}s) Ctrl+C停止")
        while True:
            a+=1
            print(f"\n{'='*50}\n   第{a}次 (OK:{ok} FAIL:{nok})\n{'='*50}")
            try:
                if auto_buy():ok+=1;print("\n🎉 抢到了!");break
                else:nok+=1
            except KeyboardInterrupt:print(f"\n停止(共{a}次 OK:{ok})");break
            except Exception as e:nok+=1;print(f"异常:{e}")
            print(f"重试{RETRY_DELAY}s...");time.sleep(RETRY_DELAY)
    else:
        auto_buy()
