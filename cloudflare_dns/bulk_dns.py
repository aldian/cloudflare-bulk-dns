from __future__ import print_function
import os
import sys
import datetime
import csv
from functools import wraps
from CloudFlare.exceptions import CloudFlareAPIError
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from cloudflare_dns import CloudFlareLibWrapper


def configured(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if kwargs.get('cf_lib_wrapper') is None:
            api_key = os.environ.get('CLOUDFLARE_API_KEY')
            if not api_key:
                raise ValueError('The environment variable CLOUDFLARE_API_KEY is not set')

            api_email = os.environ.get('CLOUDFLARE_API_EMAIL')
            if not api_email:
                raise ValueError('The environment variable CLOUDFLARE_API_EMAIL is not set')

            kwargs['cf_lib_wrapper'] = CloudFlareLibWrapper(api_key, api_email)
        return f(*args, **kwargs)
    return decorated_function


def add_new_domain(domain_name, domain_added_cb=None, cf_lib_wrapper=None):
    try:
        zone_info = cf_lib_wrapper.create_zone(domain_name)
        if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
            domain_added_cb(succeed=True, response=zone_info)
    except CloudFlareAPIError as e:
        if "already exists" not in e.message:
            raise e
        if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
            domain_added_cb(succeed=False, response={'name': domain_name}, exception=e)


@configured
def cli(args, cf_lib_wrapper=None):
    counter = 0
    dt = datetime.datetime.now()

    cmd = args[0]
    if cmd == '--add-new-domains':
        with open("cf_dns_add_new_domains_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second), "wb") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['name', 'status', 'id', 'type', 'created_on'])

            def domain_added_cb(succeed=None, response=None, exception=None):
                if succeed:
                    output_text = "added [{0}]: {1}".format(counter + 1, response['name'])
                    writer.writerow([response['name'], response['status'], response['id'], response['type'], response['created_on']])
                else:
                    output_text = "failed [{0}]: {1}".format(counter + 1, exception.message)
                    writer.writerow([response['name'], 'failed'])
                print(output_text)

            domains_file_name = args[1]
            with open(domains_file_name) as f:
                print("Adding domains listed in {0}:".format(domains_file_name))
                for line in f:
                    add_new_domain(line.strip(), domain_added_cb=domain_added_cb, cf_lib_wrapper=cf_lib_wrapper)
                    counter += 1
                print("Added {0} new domains.".format(counter))

if __name__ == "__main__":
    cli(sys.argv[1:])
