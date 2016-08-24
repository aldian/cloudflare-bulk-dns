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
        self.cf_lib_wrapper.create_a_zone = MagicMock(return_value={'id': 'ZONE INFO ID'})
        domain_names = ['add-purer-happen.host', 'analyze-dry.win', 'juiciest-old-flap.tech']
        bulk_dns.add_new_domains(domain_names, domain_added_cb=None, cf_lib_wrapper=self.cf_lib_wrapper)

    def test_cli_add_new_domains(self):
        pass

if __name__ == '__main__':
    unittest.main()
