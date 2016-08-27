import CloudFlare


class CloudFlareLibWrapper(object):
    def __init__(self, api_key, api_email):
        self.api_key = api_key
        self.api_email = api_email
        self.cf = CloudFlare.CloudFlare(email=api_email, token=api_key)

    def list_zones(self, page=1, per_page=20, status=None):
        params = {'page': page, 'per_page': per_page}
        if status is not None:
            params['status'] = status
        return self.cf.zones.get(params=params)

    def get_zone_info(self, domain_name):
        zones = self.cf.zones.get(params={'name': domain_name, 'per_page': 1})
        if len(zones) > 0:
            return zones[0]

    def create_zone(self, domain_name):
        return self.cf.zones.post(data={'name': domain_name})

    def delete_zone_by_name(self, domain_name):
        zones = self.cf.zones.get(params={'name': domain_name, 'per_page': 1})
        if len(zones) > 0:
            zone_id = zones[0]['id']
            return self.cf.zones.delete(zone_id)

    def list_dns_records(self, zone_id, page=1, per_page=20):
        params = {'page': page, 'per_page': per_page}
        return self.cf.zones.dns_records.get(
            zone_id, params=params)

    def create_dns_record(self, zone_id, record_type, record_name, content):
        """Creating a DNS record

        :param zone_id: The zone identifier
        :param record_type: The record type
        :param record_name: the record name
        :param content: the record content
        :return: a dictionary, for example:
        {
            "id": "372e67954025e0ba6aaa6d586b9e0b59",
            "type": "A",
            "name": "example.com",
            "content": "1.2.3.4",
            "proxiable": true,
            "proxied": false,
            "ttl": 120,
            "locked": false,
            "zone_id": "023e105f4ecef8ad9ca31a8372d0c353",
            "zone_name": "example.com",
            "created_on": "2014-01-01T05:20:00.12345Z",
            "modified_on": "2014-01-01T05:20:00.12345Z",
            "data": {}
        }
        """
        return self.cf.zones.dns_records.post(
            zone_id, data={'name': record_name, 'type': record_type, 'content': content})

    def delete_dns_record(self, zone_id, record_id):
        return self.cf.zones.dns_records.delete(
            zone_id, record_id)
