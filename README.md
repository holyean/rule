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

The workflow updates the generated file every Monday at 11:17 China Standard
Time and only commits when the resulting rules change.

## Sources

- https://github.com/QuixoticHeart/rule-set
- https://ruleset.skk.moe
