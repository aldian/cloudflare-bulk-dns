from __future__ import print_function
from cStringIO import StringIO
import os
import re
import sys
import csv
import unittest
from test.test_support import EnvironmentVarGuard

from CloudFlare.exceptions import CloudFlareAPIError

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

    def test_environment_api_key_not_set_error(self):
        def real_func():
            self.fail()
        env = EnvironmentVarGuard()
        env.unset('CLOUDFLARE_API_KEY')
        with env:
            try:
                bulk_dns.configured(real_func)()
                self.fail()
            except ValueError as e:
                self.assertTrue('CLOUDFLARE_API_KEY' in e.message)
            except:
                self.fail()

    def test_environment_email_key_not_set_error(self):
        def real_func():
            self.fail()
        env = EnvironmentVarGuard()
        env.set('CLOUDFLARE_API_KEY', 'hello key')
        env.unset('CLOUDFLARE_API_EMAIL')
        with env:
            try:
                bulk_dns.configured(real_func)()
                self.fail()
            except ValueError as e:
                self.assertTrue('CLOUDFLARE_API_EMAIL ' in e.message)
            except:
                self.fail()

    def test_environment_completely_set_and_real_func_called(self):
        def real_func(cf_lib_wrapper=None):
            self.assertIsNotNone(cf_lib_wrapper)
            self.assertEqual('hello key', cf_lib_wrapper.api_key)
            self.assertEqual('hello email', cf_lib_wrapper.api_email)

        env = EnvironmentVarGuard()
        env.set('CLOUDFLARE_API_KEY', 'hello key')
        env.set('CLOUDFLARE_API_EMAIL', 'hello email')
        with env:
            bulk_dns.configured(real_func)()

    def test_cli_getopt_invalid_option(self):
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli(['--abc'], cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout

        self.assertEqual(bulk_dns.usage_str, my_stdout.getvalue().strip())

    def test_cli_getopt_no_option(self):
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli([], cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout

        self.assertEqual(bulk_dns.usage_str, my_stdout.getvalue().strip())

    def test_cli_getopt_no_argument(self):
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli(['--add-new-domains'], cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout

        self.assertEqual(bulk_dns.usage_str, my_stdout.getvalue().strip())

    def test_add_new_domain_succeed(self):
        domain_name = 'add-purer-happen.host'
        responses = []

        def domain_added_cb(**kwargs):
            self.assertTrue(kwargs['succeed'])
            response = kwargs['response']
            self.assertEqual('ZONE INFO ID', response['id'])
            self.assertEqual(domain_name, response['name'])
            responses.append(response)

        self.cf_lib_wrapper.create_zone = MagicMock(return_value={'id': 'ZONE INFO ID', 'name': domain_name})
        bulk_dns.add_new_domain(
            domain_name, domain_added_cb=domain_added_cb,
            cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(1, len(responses))

    def test_add_new_domain_failed_already_exists(self):
        domain_name = 'add-purer-happen.host'
        responses = []

        def domain_added_cb(**kwargs):
            self.assertFalse(kwargs['succeed'])
            response = kwargs['response']
            self.assertEqual(domain_name, response['name'])
            responses.append(response)
            exception = kwargs['exception']
            self.assertTrue(isinstance(exception, CloudFlareAPIError))

        self.cf_lib_wrapper.create_zone = MagicMock(side_effect=CloudFlareAPIError(code=-1, message='already exists'))
        bulk_dns.add_new_domain(domain_name, domain_added_cb=domain_added_cb, cf_lib_wrapper=self.cf_lib_wrapper)
        self.assertEqual(1, len(responses))

    def test_add_new_domain_failed_other(self):
        domain_name = 'add-purer-happen.host'

        self.cf_lib_wrapper.create_zone = MagicMock(side_effect=CloudFlareAPIError(code=-1, message='other'))
        try:
            bulk_dns.add_new_domain(domain_name, cf_lib_wrapper=self.cf_lib_wrapper)
            self.fail("Add new domain should fail and never reach this line")
        except CloudFlareAPIError as e:
            pass

    def test_cli_add_new_domains_succeed(self):
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
        bulk_dns.add_new_domain = add_new_domain_real

        self.assertEqual(30, len(responses))
        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        with open(csv_file_name, "rb") as csv_file:
            reader = csv.reader(csv_file)
            row_number = 0
            for row in reader:
                if row_number == 0:
                    self.assertEqual('name', row[0])
                    self.assertEqual('status', row[1])
                    self.assertEqual('id', row[2])
                    self.assertEqual('type', row[3])
                    self.assertEqual('created_on', row[4])
                else:
                    self.assertEqual(row[0], responses[row_number - 1]['name'])
                    self.assertEqual(row[1], responses[row_number - 1]['status'])
                    self.assertEqual(row[2], responses[row_number - 1]['id'])
                    self.assertEqual(row[3], responses[row_number - 1]['type'])
                    self.assertEqual(row[4], responses[row_number - 1]['created_on'])
                row_number += 1
        os.remove(csv_file_name)

    def test_cli_add_new_domains_failed(self):
        responses = []

        def add_new_domain_mock(domain_name, domain_added_cb=None, cf_lib_wrapper=None):
            try:
                zone_info = cf_lib_wrapper.create_zone(domain_name)
                if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
                    domain_added_cb(succeed=True, response=zone_info)
            except CloudFlareAPIError as e:
                if "already exists" not in e.message:
                    raise e
                if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
                    response = {'name': domain_name}
                    responses.append(response)
                    domain_added_cb(succeed=False, response=response, exception=e)

        add_new_domain_real = bulk_dns.add_new_domain
        bulk_dns.add_new_domain = add_new_domain_mock
        self.cf_lib_wrapper.create_zone = MagicMock(side_effect=CloudFlareAPIError(code=-1, message='already exists'))
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()
        bulk_dns.cli(['--add-new-domains', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)
        sys.stdout = old_stdout
        bulk_dns.add_new_domain = add_new_domain_real
        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        with open(csv_file_name, "rb") as csv_file:
            reader = csv.reader(csv_file)
            row_number = 0
            for row in reader:
                if row_number == 0:
                    self.assertEqual('name', row[0])
                    self.assertEqual('status', row[1])
                    self.assertEqual('id', row[2])
                    self.assertEqual('type', row[3])
                    self.assertEqual('created_on', row[4])
                else:
                    self.assertEqual(row[0], responses[row_number - 1]['name'])
                    self.assertEqual(row[1], 'failed')
                row_number += 1
        os.remove(csv_file_name)

    def test_delete_all_records_succeed(self):
        domain_name = 'add-purer-happen.host'
        records =[
            {'id': 'DNS RECORD ID 1'},
            {'id': 'DNS RECORD ID 2'},
            {'id': 'DNS RECORD ID 3'},
            {'id': 'DNS RECORD ID 4'},
            {'id': 'DNS RECORD ID 5'},
            {'id': 'DNS RECORD ID 6'},
            {'id': 'DNS RECORD ID 7'},
            {'id': 'DNS RECORD ID 8'},
            {'id': 'DNS RECORD ID 9'},
            {'id': 'DNS RECORD ID 10'},
            {'id': 'DNS RECORD ID 11'},
            {'id': 'DNS RECORD ID 12'},
            {'id': 'DNS RECORD ID 13'},
            {'id': 'DNS RECORD ID 14'},
            {'id': 'DNS RECORD ID 15'},
            {'id': 'DNS RECORD ID 16'},
            {'id': 'DNS RECORD ID 17'},
            {'id': 'DNS RECORD ID 18'},
            {'id': 'DNS RECORD ID 19'},
            {'id': 'DNS RECORD ID 20'},
            {'id': 'DNS RECORD ID 21'},
        ]
        records_page_1 = records[:20]
        records_page_2 = records[20:40]
        responses = []

        def record_deleted_cb(**kwargs):
            self.assertTrue(kwargs['succeed'])
            response = kwargs['response']
            responses.append(response)
            self.assertEqual('DNS RECORD ID {0}'.format(len(responses)), response['id'])

        self.cf_lib_wrapper.get_zone_info = MagicMock(return_value={'id': 'ZONE ID'})
        self.cf_lib_wrapper.list_dns_records = MagicMock(
            side_effect=[records_page_1, records_page_2])
        self.cf_lib_wrapper.delete_dns_record = MagicMock(
            side_effect=records)

        bulk_dns.delete_all_records(
            domain_name, record_deleted_cb=record_deleted_cb,
            cf_lib_wrapper=self.cf_lib_wrapper)

        self.assertEqual(21, len(responses))

    def test_cli_delete_all_records_succeed(self):
        def delete_all_records_mock(domain_name, record_deleted_cb=None, cf_lib_wrapper=None):
            record_deleted_cb(succeed=True, response={'id': 'DNS RECORD ID'})

        delete_all_records_original = bulk_dns.delete_all_records
        bulk_dns.delete_all_records = MagicMock(side_effect=delete_all_records_mock)

        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli(['--delete-all-records', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout
        bulk_dns.delete_all_records = delete_all_records_original

        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        with open(csv_file_name, "rb") as csv_file:
            reader = csv.reader(csv_file)
            row_number = 0
            for row in reader:
                if row_number == 0:
                    self.assertEqual('zone name', row[0])
                    self.assertEqual('record id', row[1])
                    self.assertEqual('status', row[2])
                else:
                    self.assertEqual(row[1], 'DNS RECORD ID')
                    self.assertEqual(row[2], 'deleted')
                row_number += 1
            self.assertEqual(31, row_number)
        os.remove(csv_file_name)

    def test_cli_delete_all_records_failed(self):
        def delete_all_records_mock(domain_name, record_deleted_cb=None, cf_lib_wrapper=None):
            record_deleted_cb(succeed=False, response={'id': 'DNS RECORD ID'})

        delete_all_records_original = bulk_dns.delete_all_records
        bulk_dns.delete_all_records = MagicMock(side_effect=delete_all_records_mock)

        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli(['--delete-all-records', '../example-domains.txt'], cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout
        bulk_dns.delete_all_records = delete_all_records_original

        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        with open(csv_file_name, "rb") as csv_file:
            reader = csv.reader(csv_file)
            row_number = 0
            for row in reader:
                if row_number == 0:
                    self.assertEqual('zone name', row[0])
                    self.assertEqual('record id', row[1])
                    self.assertEqual('status', row[2])
                else:
                    self.assertEqual(row[1], 'DNS RECORD ID')
                    self.assertEqual(row[2], 'failed')
                row_number += 1
            self.assertEqual(31, row_number)
        os.remove(csv_file_name)

    def test_add_new_records_succeed(self):
        pass

    def test_cli_add_new_records_succeed(self):
        def add_new_records_mock(domain_name, record_added_cb=None, cf_lib_wrapper=None):
            record_added_cb(succeed=True, response={'id': 'DNS RECORD ID'})

        add_new_records_original = bulk_dns.add_new_records
        bulk_dns.add_new_records = MagicMock(side_effect=add_new_records_mock)
        old_stdout = sys.stdout
        sys.stdout = my_stdout = StringIO()

        bulk_dns.cli(
            ['--add-new-records', '--type', 'TXT', '--name', 'foo', '--content', 'bar', '../example-domains.txt'],
            cf_lib_wrapper=self.cf_lib_wrapper)

        sys.stdout = old_stdout
        bulk_dns.add_new_records = add_new_records_original

        match = re.search(r"CSV\s+file\s+(\S+)\s+generated", my_stdout.getvalue().strip())
        csv_file_name = match.group(1)
        self.assertTrue(os.path.isfile(csv_file_name))
        with open(csv_file_name, "rb") as csv_file:
            reader = csv.reader(csv_file)
            row_number = 0
            for row in reader:
                if row_number == 0:
                    self.assertEqual('zone name', row[0])
                    self.assertEqual('record id', row[1])
                    self.assertEqual('status', row[2])
                else:
                    self.assertEqual(row[1], 'DNS RECORD ID')
                    self.assertEqual(row[2], 'added')
                row_number += 1
            self.assertEqual(31, row_number)
        os.remove(csv_file_name)

if __name__ == '__main__':
    unittest.main()
