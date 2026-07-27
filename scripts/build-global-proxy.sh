#!/usr/bin/env bash
set -Eeuo pipefail

readonly QUIX_URL='https://raw.githubusercontent.com/QuixoticHeart/rule-set/ruleset/surge/proxy.list'
readonly BLACKMATRIX_URL='https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Surge/Global/Global.list'
readonly SKK_URL='https://ruleset.skk.moe/List/non_ip/global.conf'
readonly OUTPUT='surge/global-proxy.list'

workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT

fetch() {
  curl --fail --location --silent --show-error --retry 3 --retry-all-errors \
    --connect-timeout 15 --max-time 120 "$1" -o "$2"
}

fetch "$QUIX_URL" "$workdir/quix.list"
fetch "$BLACKMATRIX_URL" "$workdir/blackmatrix.list"
fetch "$SKK_URL" "$workdir/skk.list"

{
  for source in "$workdir/quix.list" "$workdir/blackmatrix.list" "$workdir/skk.list"; do
    awk -F, '
      $1 == "DOMAIN" || $1 == "DOMAIN-SUFFIX" || $1 == "DOMAIN-KEYWORD" ||
      $1 == "IP-CIDR" || $1 == "IP-CIDR6" || $1 == "PROCESS-NAME" ||
      $1 == "USER-AGENT" {
        if ($2 != "" && $2 != "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe") print $1 "," $2
      }
    ' "$source"
  done
} | LC_ALL=C sort -u > "$workdir/rules.list"

{
  printf '%s\n' '# NAME: Holyean Global Proxy'
  printf '%s\n' '# POLICY: Proxy policy selected by the client'
  printf '%s\n' '# DESCRIPTION: Consolidated global-proxy rules for Surge.'
  printf '%s\n' '# SOURCES: QuixoticHeart/rule-set proxy; blackmatrix7/ios_rule_script Global; SukkaW global supplements.'
  printf '%s\n' "# RULES: $(wc -l < "$workdir/rules.list" | tr -d ' ')"
  cat "$workdir/rules.list"
} > "$workdir/global-proxy.list"

mkdir -p "$(dirname "$OUTPUT")"
mv "$workdir/global-proxy.list" "$OUTPUT"
