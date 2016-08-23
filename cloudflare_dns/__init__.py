import CloudFlare


class CloudFlareLibWrapper(object):
    def __init__(self, api_key, api_email):
        self.api_key = api_key
        self.api_email = api_email
        self.cf = CloudFlare.CloudFlare(email=api_email, token=api_key)

    def create_a_zone(self, domain_name):
        return self.cf.zones.post(data={'name': domain_name})
