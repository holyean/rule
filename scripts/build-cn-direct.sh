#!/usr/bin/env bash
set -Eeuo pipefail

readonly QUIX_URL='https://raw.githubusercontent.com/QuixoticHeart/rule-set/ruleset/surge/cn.list'
readonly SKK_DOMAIN_URL='https://ruleset.skk.moe/List/non_ip/domestic.conf'
readonly SKK_IP_URL='https://ruleset.skk.moe/List/ip/domestic.conf'
readonly OUTPUT='surge/cn-direct.list'

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

fetch() {
  curl --fail --location --silent --show-error --retry 3 --retry-all-errors \
    --connect-timeout 15 --max-time 120 "$1" -o "$2"
}

fetch "$QUIX_URL" "$workdir/quix-cn.list"
fetch "$SKK_DOMAIN_URL" "$workdir/skk-domestic.list"
fetch "$SKK_IP_URL" "$workdir/skk-domestic-ip.list"

{
  awk -F, '$1 == "DOMAIN-SUFFIX" && $2 != "" { print $1 "," $2 }' "$workdir/quix-cn.list"
  awk -F, '
    $1 == "DOMAIN" || $1 == "DOMAIN-SUFFIX" || $1 == "DOMAIN-WILDCARD" || $1 == "USER-AGENT" {
      if ($2 != "" && $2 != "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe") print $1 "," $2
    }
  ' "$workdir/skk-domestic.list"
  awk -F, '$1 == "IP-CIDR" && $2 != "" { print $1 "," $2 }' "$workdir/skk-domestic-ip.list"
} | LC_ALL=C sort -u > "$workdir/rules.list"

{
  printf '%s\n' '# NAME: Holyean CN Direct'
  printf '%s\n' '# POLICY: DIRECT'
  printf '%s\n' '# DESCRIPTION: Consolidated mainland-China direct rules for Surge.'
  printf '%s\n' '# SOURCES: QuixoticHeart/rule-set cn; SukkaW domestic domain and CIDR supplements.'
  printf '%s\n' "# RULES: $(wc -l < "$workdir/rules.list" | tr -d ' ')"
  cat "$workdir/rules.list"
} > "$workdir/cn-direct.list"

mkdir -p "$(dirname "$OUTPUT")"
mv "$workdir/cn-direct.list" "$OUTPUT"
