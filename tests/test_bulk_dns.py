from cStringIO import StringIO
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
        self.cf_lib_wrapper.create_a_zone = MagicMock(return_value={'id': 'ZONE INFO ID', 'name': domain_name})
        bulk_dns.add_new_domain(
            domain_name, domain_added_cb=domain_added_cb,
            cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(1, len(responses))

    def test_cli_add_new_domains(self):
        responses = []

        def add_new_domain_mock(domain_name, domain_added_cb=None, cf_lib_wrapper=None):
            response = {'id': 'ZONE INFO ID', 'name': domain_name}
            responses.append(response)
            old_stdout = sys.stdout
            sys.stdout = my_stdout = StringIO()
            domain_added_cb(succeed=True, response=response)
            sys.stdout = old_stdout
            self.assertEqual("added [{0}]: {1}".format(len(responses), domain_name), my_stdout.getvalue().strip())

        bulk_dns.add_new_domain = add_new_domain_mock
        self.cf_lib_wrapper.create_a_zone = MagicMock(return_value={'id': 'ZONE INFO ID'})
        bulk_dns.cli(['--add-new-domains', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(30, len(responses))

if __name__ == '__main__':
    unittest.main()
