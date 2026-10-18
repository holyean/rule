#!/usr/bin/env python3
"""Fetch validated sources, merge equivalent network rules, publish deterministically."""
import argparse
from collections import Counter
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = re.compile(r"(?=.{1,253}$)[a-z0-9_](?:[a-z0-9_.-]*[a-z0-9_])?\Z")
SKIP_TYPES = {"URL-REGEX", "AND", "OR", "NOT", "USER-AGENT", "PROCESS-NAME"}


def domain(value):
    value = value.rstrip('.').lower().encode('idna').decode('ascii')
    if not DOMAIN.fullmatch(value) or '.' not in value or '..' in value:
        raise ValueError(f"Invalid domain: {value}")
    return value


def parse(text, fmt):
    rules, skipped = [], Counter()
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(('#', ';', '//')) or line == '[Rule]':
            continue
        try:
            if fmt == 'domainset':
                kind = 'DOMAIN-SUFFIX' if line.startswith('.') else 'DOMAIN'
                value = domain(line.lstrip('.'))
            else:
                parts = [p.strip() for p in line.split(',')]
                kind = parts[0].upper()
                if kind in SKIP_TYPES:
                    skipped[kind] += 1
                    continue
                if len(parts) < 2 or any(p.upper() not in {'REJECT', 'REJECT-DROP', 'NO-RESOLVE'} for p in parts[2:]):
                    raise ValueError('Unexpected policy or options')
                value = parts[1]
                if kind in {'DOMAIN', 'DOMAIN-SUFFIX'}:
                    value = domain(value)
                elif kind == 'DOMAIN-KEYWORD':
                    value = value.lower()
                    if not value or re.search(r'[\s,#]', value):
                        raise ValueError('Invalid keyword')
                elif kind in {'IP-CIDR', 'IP-CIDR6'}:
                    net = ipaddress.ip_network(value, strict=False)
                    if net.version != (4 if kind == 'IP-CIDR' else 6):
                        raise ValueError('IP family mismatch')
                    value = str(net)
                else:
                    raise ValueError(f'Unsupported rule type {kind}')
            rules.append((kind, value))
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f'Line {number}: {line[:150]}: {exc}') from exc
    return rules, dict(sorted(skipped.items()))


def ancestors(host):
    labels = host.split('.')
    return ('.'.join(labels[i:]) for i in range(1, len(labels)))


def merge(rules):
    unique = set(rules)
    suffixes = {v for k, v in unique if k == 'DOMAIN-SUFFIX'}
    result = set()
    for kind, value in unique:
        if kind in {'DOMAIN', 'DOMAIN-SUFFIX'}:
            if (kind == 'DOMAIN' and value in suffixes) or any(p in suffixes for p in ancestors(value)):
                continue
        elif kind in {'IP-CIDR', 'IP-CIDR6'}:
            continue
        result.add((kind, value))
    for kind in ('IP-CIDR', 'IP-CIDR6'):
        nets = [ipaddress.ip_network(v) for k, v in unique if k == kind]
        result.update((kind, str(net)) for net in ipaddress.collapse_addresses(nets))
    return sorted(result)


def protected(rule, allow):
    kind, value = rule
    if kind in {'DOMAIN', 'DOMAIN-SUFFIX'}:
        if any(value == a or value.endswith('.' + a) for a in allow):
            return True
        # A broader suffix must not swallow an explicitly allowed namespace.
        return kind == 'DOMAIN-SUFFIX' and any(a.endswith('.' + value) for a in allow)
    return kind == 'DOMAIN-KEYWORD' and any(value in a for a in allow)


def fetch(url, user_agent=None):
    # System TLS verification stays enabled. Fail closed on HTTP errors and timeouts.
    command = ['curl', '--fail', '--location', '--silent', '--show-error',
                             '--retry', '3', '--retry-all-errors', '--connect-timeout', '15',
                             '--max-time', '120']
    if user_agent:
        command.extend(['--user-agent', user_agent])
    result = subprocess.run(command + [url], check=True, capture_output=True)
    return result.stdout


def check_count(label, count, minimum, previous=0):
    if count < minimum or (previous and count < previous * 0.65):
        raise ValueError(f'{label}: suspicious rule count {count}; minimum={minimum}, previous={previous}')


def build(cache=None):
    sources = json.loads((ROOT / 'config/adblock-sources.json').read_text())
    allow = sorted({domain(l.strip()) for l in (ROOT / 'config/adblock-allow-domains.txt').read_text().splitlines()
                    if l.strip() and not l.strip().startswith('#')})
    report_path = ROOT / 'surge/adblock-report.json'
    previous = json.loads(report_path.read_text()) if report_path.exists() else {}
    old_sources = {s['id']: s for s in previous.get('sources', [])}
    all_rules, source_rules, stats = [], [], []
    for source in sources:
        data = (cache / source['id']).read_bytes() if cache else fetch(source['url'], source.get('user_agent'))
        rules, skipped = parse(data.decode('utf-8-sig'), source['format'])
        count = len(set(rules))
        check_count(source['id'], count, source['min_rules'], old_sources.get(source['id'], {}).get('unique_rules', 0))
        stats.append({**source, 'sha256': hashlib.sha256(data).hexdigest(),
                      'parsed_rules': len(rules), 'unique_rules': count, 'skipped_types': skipped,
                      'new_exact_rules_in_source_order': len(set(rules) - set(all_rules))})
        all_rules.extend(rules)
        source_rules.append(set(rules))
    allowed_removed = {r for r in all_rules if protected(r, allow)}
    merged = merge(r for r in all_rules if r not in allowed_removed)
    check_count('merged', len(merged), 100000, previous.get('final_rules', 0))
    final = set(merged)
    for index, (own, stat) in enumerate(zip(source_rules, stats)):
        others = set().union(*(r for i, r in enumerate(source_rules) if i != index))
        stat['surviving_rules'] = len(own & final)
        stat['exclusive_surviving_rules'] = len((own - others) & final)
    lines = [f'{kind},{value}' + (',no-resolve' if kind.startswith('IP-CIDR') else '') for kind, value in merged]
    header = ['# NAME: Holyean Advertising', '# POLICY: REJECT',
              '# SOURCE CONFIG: config/adblock-sources.json', f'# RULES: {len(lines)}']
    output = '\n'.join(header + lines) + '\n'
    report = {'sources': stats, 'input_rules': len(all_rules), 'unique_rules': len(set(all_rules)),
              'exact_duplicates_removed': len(all_rules) - len(set(all_rules)),
              'allow_domains': allow, 'allow_rules_removed': len(allowed_removed),
              'allow_rules_removed_by_type': dict(sorted(Counter(k for k, v in allowed_removed).items())),
              'final_rules': len(merged), 'final_types': dict(sorted(Counter(k for k, v in merged).items())),
              'output_sha256': hashlib.sha256(output.encode()).hexdigest()}
    # No file is replaced until every source and the complete merge have passed validation.
    report_path.parent.mkdir(exist_ok=True)
    allow_output = '# NAME: Holyean GitHub Allowlist\n# POLICY: select your GitHub policy; place before adblock.list\n' + ''.join(f'DOMAIN-SUFFIX,{a}\n' for a in allow)
    for path, content in [(ROOT / 'surge/adblock.list', output),
                          (ROOT / 'surge/adblock-allow.list', allow_output),
                          (report_path, json.dumps(report, ensure_ascii=False, indent=2) + '\n')]:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
            f.write(content)
            temp = Path(f.name)
        temp.replace(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, help='Use previously downloaded sources for offline verification')
    args = parser.parse_args()
    build(args.cache_dir)
