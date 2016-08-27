from __future__ import print_function
import os
import sys
import unittest

from CloudFlare.exceptions import CloudFlareAPIError

from cloudflare_dns import CloudFlareLibWrapper


class TestCloudFlareLibWrapper(unittest.TestCase):
    """The testing of integration with the CloudFlare API

    You need to put the correct api key and email values to
    environment variables CLOUDFLARE_API_KEY AND CLOUDFLARE_API_EMAIL

    When needed for testing, we can lookup the list of active zones from dev_notes.txt
    """
    def setUp(self):
        api_key = os.environ.get('CLOUDFLARE_API_KEY')
        api_email = os.environ.get('CLOUDFLARE_API_EMAIL')
        self.lib_wrapper = CloudFlareLibWrapper(api_key, api_email)

    def tearDown(self):
        pass

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_list_zones(self):
        domain_name = 'answer-educate.download'
        # make sure zone didn't exist before creating it
        try:
            self.lib_wrapper.delete_zone_by_name(domain_name)
        except:
            pass
        zone_info = self.lib_wrapper.create_zone(domain_name)

        zone_info_ids = set()
        idx = 1
        page = 1
        while True:
            zone_info_list = self.lib_wrapper.list_zones(page=page, per_page=20)

            print("PAGE:", page, file=sys.stderr)
            for zone_info in zone_info_list:
                zone_info_ids.add(zone_info['id'])
                print(idx, "ZONE INFO ID:", zone_info['id'], file=sys.stderr)
                print(idx, "ZONE INFO NAME:", zone_info['name'], file=sys.stderr)
                print(idx, "ZONE INFO STATUS:", zone_info['status'], file=sys.stderr)
                idx += 1

            if len(zone_info_list) < 20:
                break

            self.assertEqual(20, len(zone_info_list))

            page += 1

        self.assertTrue(zone_info['id'] in zone_info_ids)

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_get_zone_info(self):
        domain_name = 'answer-educate.download'

        # make sure zone existed before getting its info
        try:
            self.lib_wrapper.create_zone(domain_name)
        except:
            pass

        # get the zone info
        zone_info = self.lib_wrapper.get_zone_info(domain_name)
        self.assertTrue('id' in zone_info)
        print("GET ZONE INFO:", zone_info, file=sys.stderr)

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_create_zone(self):
        domain_name = 'answer-educate.download'

        # make sure zone didn't exist before creating it
        try:
            self.lib_wrapper.delete_zone_by_name(domain_name)
        except:
            pass

        # create the zone
        try:
            zone_info = self.lib_wrapper.create_zone(domain_name)
            id_key = "id"
            self.assertTrue(id_key in zone_info)
            self.assertNotEqual("", zone_info[id_key].strip())
            self.assertEqual(domain_name, zone_info['name'])
            print("CREATED ZONE INFO ID:", zone_info.get(id_key), file=sys.stderr)
            print("CREATED ZONE INFO:", zone_info, file=sys.stderr)
        except CloudFlareAPIError as e:
            if "already exists" not in e.message:
                raise e

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_delete_zone(self):
        domain_name = 'answer-educate.download'

        # make sure zone existed before deleting it
        try:
            self.lib_wrapper.create_zone(domain_name)
        except:
            pass

        # delete the zone
        zone_info = self.lib_wrapper.delete_zone_by_name(domain_name)
        if zone_info is not None:
            print("DELETED ZONE INFO:", zone_info, file=sys.stderr)
            self.assertTrue('id' in zone_info)

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_list_dns_records(self):
        domain_name = 'answer-educate.download'
        # make sure zone existed before getting its info
        try:
            self.lib_wrapper.create_zone(domain_name)
        except:
            pass
        # get the zone info
        zone_info = self.lib_wrapper.get_zone_info(domain_name)
        zone_id = zone_info['id']

        record_info = self.lib_wrapper.create_dns_record(zone_id, "TXT", "bar", "foo")

        dns_record_ids = set()
        while True:
            dns_records = self.lib_wrapper.list_dns_records(zone_id, page=1, per_page=20)
            print("DNS RECORDS LEN:", len(dns_records), file=sys.stderr)
            for dns_record in dns_records:
                dns_record_ids.add(dns_record['id'])
                print("DNS RECORD ID:", dns_record['id'], file=sys.stderr)
                print("DNS RECORD TYPE:", dns_record['type'], file=sys.stderr)
                print("DNS RECORD NAME:", dns_record['name'], file=sys.stderr)
                print("DNS RECORD CONTENT:", dns_record['content'], file=sys.stderr)

            if len(dns_records) < 20:
                break

        self.assertTrue(record_info['id'] in dns_record_ids)
        self.lib_wrapper.delete_dns_record(zone_id, record_info['id'])

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_create_dns_record(self):
        domain_name = 'answer-educate.download'
        # make sure zone existed before getting its info
        try:
            self.lib_wrapper.create_zone(domain_name)
        except:
            pass
        # get the zone info
        zone_info = self.lib_wrapper.get_zone_info(domain_name)
        zone_id = zone_info['id']

        record_info = self.lib_wrapper.create_dns_record(zone_id, "TXT", "bar", "foo")
        self.assertTrue('id' in record_info)
        self.lib_wrapper.delete_dns_record(zone_id, record_info['id'])

    @unittest.skip("Temporarily skipped to prevent zone blocking by CloudFlare")
    def test_delete_dns_record(self):
        domain_name = 'answer-educate.download'
        # make sure zone existed before getting its info
        try:
            self.lib_wrapper.create_zone(domain_name)
        except:
            pass
        # get the zone info
        zone_info = self.lib_wrapper.get_zone_info(domain_name)
        zone_id = zone_info['id']

        record_info = self.lib_wrapper.create_dns_record(zone_id, "TXT", "bar", "foo")
        deleted_record_info = self.lib_wrapper.delete_dns_record(zone_id, record_info['id'])
        self.assertEqual(record_info['id'], deleted_record_info['id'])


if __name__ == '__main__':
    unittest.main()
