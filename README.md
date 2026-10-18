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

### 合并方式

- 来源定义在 `config/adblock-sources.json`，每个来源必须成功下载并通过校验。
- 可莉源需要完整客户端 User-Agent；配置已记录实测可用值，TLS 校验保持启用。
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

本地验证与构建（Python 3.12+ 和 curl，无第三方 Python 依赖）：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build-adblock.py
```
