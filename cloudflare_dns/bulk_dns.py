from __future__ import print_function
import os
import sys
import datetime
from functools import wraps
import csv
import getopt
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


def delete_all_records(domain_name, record_deleted_cb=None, cf_lib_wrapper=None):
    zone_info = cf_lib_wrapper.get_zone_info(domain_name)
    page = 1
    while True:
        dns_records = cf_lib_wrapper.list_dns_records(zone_info['id'], page=page, per_page=20)
        for dns_record in dns_records:
            record_info = cf_lib_wrapper.delete_dns_record(zone_info['id'], dns_record['id'])
            record_deleted_cb(succeed=True, response=record_info)
        if len(dns_records) < 20:
            break


@configured
def cli(args, cf_lib_wrapper=None):
    usage = ('usage:'
             '\ncloudflare_dns/bulk_dns.py --add-new-domain <domain_list_file>' +
             '\ncloudflare_dns/bulk_dns.py --delete-all-records <domain_list_file>' +
             '\ncloudflare_dns/bulk_dns.py --add-new-records --type <record_type> --name <record_name> --content <record_content> <domain_list_file>')

    try:
        opts, args = getopt.getopt(args,
                                   '',
                                   [
                                       'add-new-domains', 'delete-all-records', 'add-new-records',
                                       'type=', 'name=', 'content='
                                   ])
    except getopt.GetoptError:
        exit(usage)

    cmd = None
    i = 0
    for opt, arg in opts:
        if i == 0:
            if opt in ('--add-new-domains', '--delete-all-records', '--add-new-records'):
                cmd = opt
            else:
                exit(usage)
        else:
            pass
        i += 1

    if cmd is None or len(args) < 1:
        exit(usage)

    domains_file_name = args[0]

    counter = 0
    dt = datetime.datetime.now()

    if cmd == '--add-new-domains':
        csv_name = "cf_dns_add_new_domains_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
                dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        with open(csv_name, "wb") as csv_file:
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

            with open(domains_file_name) as f:
                print("Adding domains listed in {0}:".format(domains_file_name))
                for line in f:
                    add_new_domain(line.strip(), domain_added_cb=domain_added_cb, cf_lib_wrapper=cf_lib_wrapper)
                    counter += 1
                print("Added {0} new domains.".format(counter))
            print("CSV file {0} generated.".format(csv_name))
    elif cmd == '--delete-all-records':
        csv_name = "cf_dns_delete_all_records_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        with open(csv_name, "wb") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['zone name', 'record id', 'status'])

            def record_deleted_cb_wrapper(zone_name):
                def record_deleted_cb(succeed=None, response=None, exception=None):
                    if succeed:
                        output_text = "deleted [{0}]: record {1} of {2}".format(counter + 1, response['id'], zone_name)
                        writer.writerow([zone_name, response['id'], 'deleted'])
                    else:
                        output_text = "failed [{0}]: while deleting record {1} of {2}".format(
                            counter + 1, response['id'], zone_name)
                        writer.writerow([zone_name, response['id'], 'failed'])
                    print(output_text)
                return record_deleted_cb

            with open(domains_file_name) as f:
                print("Deleting records from zones listed in {0}:".format(domains_file_name))
                for line in f:
                    zone_name = line.strip()
                    delete_all_records(zone_name, record_deleted_cb=record_deleted_cb_wrapper(zone_name), cf_lib_wrapper=cf_lib_wrapper)
                    counter += 1
                print("Deleted {0} records.".format(counter))
        print("CSV file {0} generated.".format(csv_name))

if __name__ == "__main__":
    cli(sys.argv[1:])
