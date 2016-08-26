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
    """
    def setUp(self):
        api_key = os.environ.get('CLOUDFLARE_API_KEY')
        api_email = os.environ.get('CLOUDFLARE_API_EMAIL')
        self.lib_wrapper = CloudFlareLibWrapper(api_key, api_email)

    def tearDown(self):
        pass

    def test_create_a_zone(self):
        try:
            domain_name = 'answer-educate.download'
            zone_info = self.lib_wrapper.create_a_zone(domain_name)
            id_key = "id"
            self.assertTrue(id_key in zone_info)
            self.assertNotEqual("", zone_info[id_key].strip())
            self.assertEqual(domain_name, zone_info['name'])
            print("CREATED ZONE INFO ID:", zone_info.get(id_key), file=sys.stderr)
            print("CREATED ZONE INFO:", zone_info, file=sys.stderr)
        except CloudFlareAPIError as e:
            if "already exists" not in e.message:
                raise e

    def test_delete_a_zone(self):
        domain_name = 'answer-educate.download'
        zone_info = self.lib_wrapper.delete_a_zone_by_name(domain_name)
        if zone_info is not None:
            print("DELETED ZONE INFO:", zone_info, file=sys.stderr)
            self.assertTrue('id' in zone_info)


if __name__ == '__main__':
    unittest.main()
