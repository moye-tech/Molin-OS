# 闲鱼自动化 — 初始化阻断器清单

> 首次部署时必须逐项通过。三项全部绿色后 Cron 作业自动激活。

## 阻断器状态

| # | 阻断项 | 命令/操作 | 状态 |
|---|--------|----------|:----:|
| 1 | Python 3.12+ | `brew install python@3.12` | ✅ |
| 2 | XianYuApis 项目 | `git clone <URL> ~/xianyu_agent` | ✅ |
| 3 | 闲鱼 Cookies | 扫码登录 goofish.com → 导出 → `~/.xianyu_cookies_new.txt` | ✅ |

## 验证命令

```bash
# 1. Python版本
/opt/homebrew/bin/python3.12 --version

# 2. 项目文件完整性
ls ~/xianyu_agent/message/types.py
ls ~/xianyu_agent/static/goofish_js_version_2.js
ls ~/xianyu_agent/utils/goofish_utils.py

# 3. Cookies有效性
/opt/homebrew/bin/python3.12 -c "
import json
cookies = json.load(open('/Users/moye/.xianyu_cookies_new.txt'))
import requests
s = requests.Session()
for k,v in cookies.items(): s.cookies.set(k,v,domain='.goofish.com')
r = s.post('https://h5api.m.goofish.com/h5/mtop.taobao.idlehome.home.webpc.feed/1.0/',
  params={'jsv':'2.7.2','appKey':'34839810','t':'1778400000000','sign':'','v':'1.0','type':'originaljson','dataType':'json'},
  headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.goofish.com/'}, timeout=15)
print('✅ API连通' if r.status_code==200 else f'❌ HTTP {r.status_code}')
"
```

## Cron 作业

- **作业ID**: `1a6bd56a00cc`
- **策略**: 每30分钟（15分/45分），9:00-21:00
- **技能**: xianyu-automation + agent-sales-deal-strategist + feishu-message-formatter
- **投递**: `feishu:oc_94c87f141e118b68c2da9852bf2f3bda`
- **如果 Cookies 无效**: Cron 静默跳过，不报错

## Cookie 刷新

goofish_apis.py 自动处理：
- `_m_h5_tk` 刷新（调用 `mtop.taobao.idlemessage.pc.loginuser.get`）
- 签名生成（`generate_sign(token, timestamp, data)`）
- Cookie 域设置（`.goofish.com`）
