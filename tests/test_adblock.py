import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('adblock', Path(__file__).resolve().parents[1] / 'scripts/build-adblock.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class AdblockTests(unittest.TestCase):
    def test_domainset_preserves_exact_and_suffix_meanings(self):
        rules, _ = m.parse('.Ads.Example.com\nexact.example.com\n', 'domainset')
        self.assertEqual(rules, [('DOMAIN-SUFFIX', 'ads.example.com'), ('DOMAIN', 'exact.example.com')])

    def test_domain_coverage_uses_label_boundaries(self):
        rules = [('DOMAIN-SUFFIX', 'ads.example.com'), ('DOMAIN-SUFFIX', 'sub.ads.example.com'),
                 ('DOMAIN', 'ads.example.com'), ('DOMAIN', 'a.ads.example.com'),
                 ('DOMAIN', 'badads.example.com'), ('DOMAIN', 'example.com')]
        self.assertEqual(set(m.merge(rules)), {rules[0], rules[4], rules[5]})

    def test_exact_domain_does_not_cover_subdomain(self):
        rules = [('DOMAIN', 'example.com'), ('DOMAIN', 'sub.example.com')]
        self.assertEqual(m.merge(rules), rules)

    def test_cidr_merge_preserves_address_set(self):
        rules = [('IP-CIDR', '192.0.2.0/25'), ('IP-CIDR', '192.0.2.128/25'),
                 ('IP-CIDR', '192.0.2.8/32'), ('IP-CIDR6', '2001:db8::/32')]
        self.assertEqual(m.merge(rules), [('IP-CIDR', '192.0.2.0/24'), rules[3]])

    def test_upstream_reject_actions_are_removed(self):
        rules, _ = m.parse('[Rule]\nDOMAIN-SUFFIX,ads.example.com,REJECT-DROP\nIP-CIDR,192.0.2.3/24,no-resolve', 'rules')
        self.assertEqual(rules, [('DOMAIN-SUFFIX', 'ads.example.com'), ('IP-CIDR', '192.0.2.0/24')])

    def test_fail_closed_on_errors_or_allow_rules(self):
        for text in ['<html>Access denied</html>', 'DOMAIN,example.com,DIRECT', 'DOMAIN-SUFFIX,com', 'DOMAIN,ads..example.com']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                m.parse(text, 'rules')

    def test_count_guards(self):
        for count, minimum, previous in [(0, 1, 0), (60, 1, 100)]:
            with self.assertRaises(ValueError):
                m.check_count('test', count, minimum, previous)

    def test_non_network_filters_are_reported(self):
        rules, skipped = m.parse('URL-REGEX,^https://example.com/ads\nAND,((DOMAIN,a.example.com),(USER-AGENT,Foo))', 'rules')
        self.assertEqual(rules, [])
        self.assertEqual(skipped, {'AND': 1, 'URL-REGEX': 1})

    def test_github_allowlist_with_domain_boundaries(self):
        allow = ['github.com', 'githubusercontent.com', 'github.io']
        for rule in [('DOMAIN', 'raw.githubusercontent.com'), ('DOMAIN-SUFFIX', 'github.com'),
                     ('DOMAIN-SUFFIX', 'ads.github.io'), ('DOMAIN-KEYWORD', 'github')]:
            self.assertTrue(m.protected(rule, allow))
        for rule in [('DOMAIN', 'github.com.ads.example.com'), ('DOMAIN', 'fakegithub.com'),
                     ('DOMAIN-KEYWORD', 'advert')]:
            self.assertFalse(m.protected(rule, allow))

    def test_tls_client_uses_configured_agent(self):
        response = SimpleNamespace(content=b'DOMAIN,ads.example.com', raise_for_status=lambda: None)
        client = SimpleNamespace(get=lambda *a, **kw: response)
        with patch.dict('sys.modules', {'curl_cffi': client}):
            self.assertEqual(m.fetch('https://example.com', 'Loon/984', impersonate='safari_ios'), response.content)

    def test_tls_failure_falls_back_to_system_curl(self):
        def fail(*args, **kwargs):
            raise OSError('HTTP 403')
        client = SimpleNamespace(get=fail, exceptions=SimpleNamespace(RequestException=OSError))
        result = SimpleNamespace(returncode=0, stdout=b'rules')
        with patch.dict('sys.modules', {'curl_cffi': client}), patch.object(m.subprocess, 'run', return_value=result):
            self.assertEqual(m.fetch('https://example.com', 'Loon/984', impersonate='safari_ios'), b'rules')


if __name__ == '__main__':
    unittest.main()
