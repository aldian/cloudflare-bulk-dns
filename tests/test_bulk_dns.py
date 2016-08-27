from cStringIO import StringIO
import os
import re
import sys
import unittest
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock
from cloudflare_dns import CloudFlareLibWrapper
from cloudflare_dns import bulk_dns


class TestBulkDns(unittest.TestCase):
    def setUp(self):
        self.cf_lib_wrapper = CloudFlareLibWrapper('THE API KEY', 'THE API EMAIL')

    def tearDown(self):
        pass

    def test_add_new_domain(self):
        responses = []

        def domain_added_cb(**kwargs):
            self.assertTrue(kwargs['succeed'])
            response = kwargs['response']
            responses.append(response)
            self.assertEqual('ZONE INFO ID', response['id'])

        domain_name = 'add-purer-happen.host'
        self.cf_lib_wrapper.create_zone = MagicMock(return_value={'id': 'ZONE INFO ID', 'name': domain_name})
        bulk_dns.add_new_domain(
            domain_name, domain_added_cb=domain_added_cb,
            cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(1, len(responses))

    def test_cli_add_new_domains(self):
        responses = []

        def add_new_domain_mock(domain_name, domain_added_cb=None, cf_lib_wrapper=None):
            response = {u'status': u'pending',
                   u'original_name_servers': [u'dns2.registrar-servers.com', u'dns1.registrar-servers.com'],
                   u'original_dnshost': None, u'name': domain_name,
                   u'owner': {u'type': u'user', u'id': u'f8c7636f868f2581c13bb0388d1fc006',
                              u'email': u'mall1media@yandex.com'}, u'original_registrar': None, u'paused': False,
                   u'modified_on': u'2016-08-26T15:34:31.844063Z', u'created_on': u'2016-08-26T15:34:31.817353Z',
                   u'meta': {u'page_rule_quota': 3, u'wildcard_proxiable': False, u'step': 4,
                             u'phishing_detected': False, u'multiple_railguns_allowed': False,
                             u'custom_certificate_quota': 0},
                   u'plan': {u'externally_managed': False, u'name': u'Free Website', u'price': 0,
                             u'can_subscribe': False, u'currency': u'USD', u'frequency': u'', u'legacy_id': u'free',
                             u'legacy_discount': False, u'id': u'0feeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
                             u'is_subscribed': True},
                   u'name_servers': [u'donald.ns.cloudflare.com', u'dora.ns.cloudflare.com'], u'development_mode': 0,
                   u'type': u'full', u'id': u'683b994a838b2c6f57c45a160507f5b8',
                   u'permissions': [u'#analytics:read', u'#billing:edit', u'#billing:read', u'#cache_purge:edit',
                                    u'#dns_records:edit', u'#dns_records:read', u'#lb:edit', u'#lb:read', u'#logs:read',
                                    u'#organization:edit', u'#organization:read', u'#ssl:edit', u'#ssl:read',
                                    u'#waf:edit', u'#waf:read', u'#zone:edit', u'#zone:read', u'#zone_settings:edit',
                                    u'#zone_settings:read']}

            responses.append(response)
            old_stdout = sys.stdout
            sys.stdout = my_stdout = StringIO()
            domain_added_cb(succeed=True, response=response)
            sys.stdout = old_stdout
            self.assertEqual("added [{0}]: {1}".format(len(responses), domain_name), my_stdout.getvalue().strip())

        add_new_domain_real = bulk_dns.add_new_domain
        bulk_dns.add_new_domain = add_new_domain_mock

        self.cf_lib_wrapper.create_zone = MagicMock(return_value={'id': 'ZONE INFO ID'})
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()
        bulk_dns.cli(['--add-new-domains', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)
        sys.stdout = old_stdout
        self.assertEqual(30, len(responses))
        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        os.remove(csv_file_name)

        bulk_dns.add_new_domain = add_new_domain_real

    def test_cli_delete_all_records(self):
        bulk_dns.cli(['--delete-all-records', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)

if __name__ == '__main__':
    unittest.main()
