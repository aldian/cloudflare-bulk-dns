import CloudFlare


class CloudFlareLibWrapper(object):
    def __init__(self, api_key, api_email):
        self.api_key = api_key
        self.api_email = api_email
        self.cf = CloudFlare.CloudFlare(email=api_email, token=api_key)

    def get_zone_info(self, domain_name):
        zones = self.cf.zones.get(params={'name': domain_name, 'per_page': 1})
        if len(zones) > 0:
            return zones[0]

    def create_a_zone(self, domain_name):
        return self.cf.zones.post(data={'name': domain_name})

    def delete_a_zone_by_name(self, domain_name):
        zones = self.cf.zones.get(params={'name': domain_name, 'per_page': 1})
        if len(zones) > 0:
            zone_id = zones[0]['id']
            return self.cf.zones.delete(zone_id)
