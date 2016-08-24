import os
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

    def test_add_new_domains(self):
        responses = []

        def domain_added_cb(**kwargs):
            self.assertTrue(kwargs['succeed'])
            response = kwargs['response']
            responses.append(response)
            self.assertEqual('ZONE INFO ID', response['id'])

        self.cf_lib_wrapper.create_a_zone = MagicMock(return_value={'id': 'ZONE INFO ID'})
        domain_names = ['add-purer-happen.host', 'analyze-dry.win', 'juiciest-old-flap.tech']
        bulk_dns.add_new_domains(
            domain_names, domain_added_cb=domain_added_cb,
            cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(3, len(responses))

    def test_cli_add_new_domains(self):

        def add_new_domains_mock(bulk_dns):
            pass

        bulk_dns.add_new_domains = add_new_domains_mock
        self.cf_lib_wrapper.create_a_zone = MagicMock(return_value={'id': 'ZONE INFO ID'})
        bulk_dns.cli(['--add-new-domains', 'example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)

if __name__ == '__main__':
    unittest.main()
