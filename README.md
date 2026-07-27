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
