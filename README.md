# Holyean Rule

Personal, public rule outputs for Surge. This repository contains no proxy
credentials, server addresses, account data, or private configuration.

## CN Direct

`surge/cn-direct.list` consolidates the QuixoticHeart mainland-China domain
set with the non-overlapping SukkaW domestic-domain and CIDR supplements.

Use it in Surge before `GEOIP,CN` and before the final proxy rule:

```ini
RULE-SET,https://raw.githubusercontent.com/holyean/rule/main/surge/cn-direct.list,DIRECT,no-resolve
GEOIP,CN,DIRECT,no-resolve
```

## Global Proxy

`surge/global-proxy.list` consolidates the QuixoticHeart global-proxy list,
blackmatrix7's app and user-agent coverage, and non-overlapping SukkaW global
supplements. It removes duplicated records and excludes the SukkaW test-only
hostname.

Use it after specific service rules and before `cn-direct.list`:

```ini
RULE-SET,https://raw.githubusercontent.com/holyean/rule/main/surge/global-proxy.list,美国线路,extended-matching,no-resolve
RULE-SET,https://raw.githubusercontent.com/holyean/rule/main/surge/cn-direct.list,DIRECT,no-resolve
GEOIP,CN,DIRECT,no-resolve
```

The workflow updates both generated libraries every Monday at 11:17 China
Standard Time and only commits when the resulting output changes.

## Sources

- https://github.com/QuixoticHeart/rule-set
- https://github.com/blackmatrix7/ios_rule_script
- https://ruleset.skk.moe

## Advertising / 广告拦截

`surge/adblock.list` 按本仓库现有规则库的方式生成，每周一北京时间
11:47（UTC 03:47）自动重新拉取、合并、去重并提交变化，也可在
Actions → Update Advertising Rules → Run workflow 手动更新。GitHub 的定时任务可能延迟；
公共仓库长期没有活动时 GitHub 也可能停用定时任务，届时需要重新启用工作流。

订阅地址：

```text
https://raw.githubusercontent.com/holyean/rule/main/surge/adblock.list
```

在 Surge `[Rule]` 中放在服务分流、Global Proxy、CN Direct 和 FINAL 之前。
个人需要放行的规则放在这两行之前：

```ini
RULE-SET,https://raw.githubusercontent.com/holyean/rule/main/surge/adblock-allow.list,美国线路
RULE-SET,https://raw.githubusercontent.com/holyean/rule/main/surge/adblock.list,REJECT
```

GitHub 排除域名由 `config/adblock-allow-domains.txt` 维护，覆盖 github.com、
githubusercontent.com、githubassets.com、github.io、GitHub 开发环境和容器镜像等域名。
每次构建都剔除命中这些域名及其子域的规则。配套的 `adblock-allow.list` 在客户端优先放行
这些域名，避免宽泛关键词规则再次命中 GitHub 子域。示例沿用本仓库的“美国线路”
代理策略；请按自己的访问方式将第一行策略改成代理策略或 DIRECT。
GitHub Pages 等用户托管内容同样按个人偏好整体放行。

### 国内应用业务误拦截修复

`config/adblock-functional-allow-rules.txt` 独立维护业务例外，每次合并全部来源时均应用，
避免周更把误拦截重新带回来。现有 `adblock.list` 订阅地址保持有效，无需增加客户端规则组。
这些域名不会混入指定“美国线路”的 GitHub 放行表。

- 精确放行汽水/抖音使用的 Polaris 业务接口、设备安全接口与 Gecko 功能资源。
- 保护汽水音乐 `qishui.com` 和极核 `zeehoev.com` 的第一方服务域名。
- 不整体放行字节跳动或 `snssdk.com`；`log.snssdk.com`、`applog.snssdk.com`、
  `gecko-pangle-lf.snssdk.com` 等广告/统计规则继续保留。
- `DOMAIN` 例外只保护该主机，`DOMAIN-SUFFIX` 例外才覆盖其子域。
  与例外冲突的宽泛域名或关键词拦截会从合并表剔除，报告记录剔除数量。

`config/global-proxy-exclude-rules.txt` 则排除国际表对整个 `snssdk.com` 的泛化分类，
使该共享 SDK 按现有国内分流表处理；TikTok 专用域名及海外 SDK 域名保持原分类。

极核壁纸发布若出现 `Request body exceeds buffering limit`，原因是客户端脚本要求
缓存过大的请求体，属于脚本配置问题。域名放行不能修复它；API 请求的头部捕获应避免
读取图片请求体，网页面板的表单处理可以单独保留。此仓库不会通过关闭整体广告拦截来
掩盖这类错误，也不存储设备账号或请求内容。

### 合并方式

- 来源定义在 `config/adblock-sources.json`，每个来源必须成功下载并通过校验。
- 可莉源使用客户端 User-Agent 和 iOS TLS 请求指纹；TLS 证书校验保持启用。
- 统一大小写和空白，剥离上游 REJECT/REJECT-DROP 策略；本仓库由订阅时选择策略。
- 保留 DOMAIN、DOMAIN-SUFFIX、DOMAIN-KEYWORD、IPv4/IPv6 CIDR。
- 精确域名仍是精确匹配，后缀域名覆盖自身及子域；去重严格按点分隔的域名边界进行。
- 去除完全重复规则，以及已被父级 DOMAIN-SUFFIX 覆盖的子域规则；合并等价 CIDR。
- 不把浏览器元素过滤、重写或 MITM 功能塞进网络规则。blackmatrix7 的 URL-REGEX、
  AND 等规则不并入这份列表，跳过数量在报告中单独列出。
- 不因一次 DNS 解析失败删除域名；本次合并不代表逐条人工确认广告性质。
- 下载失败、格式错误、低于来源数量下限，或较上次减少超过 35% 时构建失败，
  不提交、不覆盖上一版正常结果。没有内容变化时不创建更新提交。

### 来源及分析

| 来源 | 选用文件 / 特点 |
| --- | --- |
| [可莉](https://github.com/luestr/ProxyResource) | 用户指定的 [Advertising.lsr](https://rule.kelee.one/Loon/Advertising.lsr)，完整客户端 UA 获取 |
| [blackmatrix7](https://github.com/blackmatrix7/ios_rule_script) | Advertising_All.list；Advertising.list 本身不含完整域名库，不能单独当作完整版 |
| [Loyalsoldier](https://github.com/Loyalsoldier/surge-rules) | release/ruleset/reject.txt，补充广告域名 |
| [秋风 AWAvenue](https://github.com/TG-Twilight/AWAvenue-Ads-Rule) | Surge DOMAIN-SET，按其点前缀区分后缀和精确域名 |
| [217heidai](https://github.com/217heidai/adblockfilters) | adblockclash.list，剥离上游策略后合入，补充多来源 DNS 广告域名 |

`surge/adblock-report.json` 随每次构建更新，包含来源 URL、SHA-256、原始规则数量、
精确去重数量、合并后的类型数量、GitHub 排除数量及输出 SHA-256。
`new_exact_rules_in_source_order` 是按配置顺序新增的精确规则数，受排序影响；
`exclusive_surviving_rules` 是仅该来源提供且最终保留的规则数，不等于广告拦截效果。
可莉和 blackmatrix7 的域名覆盖高度重叠，但保留两者以持续满足指定来源要求。

来源作者和许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本地验证与构建（Python 3.12+、curl 及 requirements-adblock.txt）：

```sh
python3 -m pip install -r requirements-adblock.txt
python3 -m unittest discover -s tests -v
python3 scripts/build-adblock.py
```
