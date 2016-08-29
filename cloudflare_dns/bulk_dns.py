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
    if zone_info is None:
        record_deleted_cb(succeed=False, exception=ValueError('zone_info is None'))
        return
    page = 1
    while True:
        dns_records = cf_lib_wrapper.list_dns_records(zone_info['id'], page=page, per_page=20)
        for dns_record in dns_records:
            record_info = cf_lib_wrapper.delete_dns_record(zone_info['id'], dns_record['id'])
            record_deleted_cb(succeed=True, response=record_info)
        if len(dns_records) < 20:
            break
        page += 1


def add_new_record(domain_name, record_type, record_name, record_content, record_added_cb=None, cf_lib_wrapper=None):
    zone_info = cf_lib_wrapper.get_zone_info(domain_name)
    if zone_info is None:
        record_added_cb(succeed=False, exception=ValueError('zone_info is None'))
        return
    try:
        if not record_name:
            record_name = domain_name
        record_info = cf_lib_wrapper.create_dns_record(zone_info['id'], record_type, record_name, record_content)
        record_added_cb(succeed=True, response=record_info)
    except CloudFlareAPIError as e:
        record_added_cb(succeed=False, exception=e)


def edit_record(domain_name, record_type, record_name, old_record_content, new_record_content, record_edited_cb=None, cf_lib_wrapper=None):
    zone_info = cf_lib_wrapper.get_zone_info(domain_name)
    if zone_info is None:
        record_edited_cb(succeed=False, exception=ValueError('zone_info is None'))
        return
    record_info = None
    page = 1
    while True:
        dns_records = cf_lib_wrapper.list_dns_records(zone_info['id'], page=page, per_page=20)
        for dns_record in dns_records:
            if dns_record['type'] == record_type and dns_record['name'] == "{0}.{1}".format(record_name, domain_name) \
                    and dns_record['content'] == old_record_content:
                record_info = dns_record
                break
        if (record_info is not None) or (len(dns_records) < 20):
            break
        page += 1
    if record_info is None:
        record_edited_cb(succeed=False, exception=ValueError('Existing DNS record not found'))
        return
    try:
        record_info = cf_lib_wrapper.update_dns_record(
            zone_info['id'], record_info['id'], record_type, record_name, new_record_content)
        record_edited_cb(succeed=True, response=record_info)
    except CloudFlareAPIError as e:
        record_edited_cb(succeed=False, exception=e)


def list_records(domain_name, record_listed_cb=None, cf_lib_wrapper=None):
    zone_info = cf_lib_wrapper.get_zone_info(domain_name)
    if zone_info is None:
        record_listed_cb(succeed=False, exception=ValueError('zone_info is None'))
        return
    page = 1
    while True:
        dns_records = cf_lib_wrapper.list_dns_records(zone_info['id'], page=page, per_page=20)
        for dns_record in dns_records:
            record_listed_cb(succeed=True, response=dns_record)
        if len(dns_records) < 20:
            break
        page += 1


usage_str = (
    'Usage:'
    '\ncloudflare_dns/bulk_dns.py --add-new-domain <domain_list_file>' +
    '\ncloudflare_dns/bulk_dns.py --delete-all-records <domain_list_file>' +
    '\ncloudflare_dns/bulk_dns.py --list-records <domain_list_file>' +
    '\ncloudflare_dns/bulk_dns.py --add-new-records --type <record_type> --name <record_name> --content <record_content> <domain_list_file>' +
    '\ncloudflare_dns/bulk_dns.py --edit-records --type <record_type> --name <record_name> --old-content <old_content> --new-content <new_content> <domain_list_file>'
)


def cli_add_new_domains(domains_file_name, cf_lib_wrapper):
    counter = 0
    dt = datetime.datetime.now()
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


def cli_delete_all_records(domains_file_name, cf_lib_wrapper):
    counter = 0
    dt = datetime.datetime.now()
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
                    if response is None:
                        output_text = "failed [{0}]: {1} while deleting records of {2}".format(
                            counter + 1, exception.message, zone_name)
                        writer.writerow([zone_name, '', exception.message])
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
            print("Deleted records from {0} zones.".format(counter))
    print("CSV file {0} generated.".format(csv_name))


def cli_add_new_records(domains_file_name, cf_lib_wrapper, record_type, record_name, record_content):
    counter = 0
    dt = datetime.datetime.now()
    csv_name = "cf_dns_add_new_records_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    with open(csv_name, "wb") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['zone name', 'status', 'record id'])

        def record_added_cb_wrapper(zone_name):
            def record_added_cb(succeed=None, response=None, exception=None):
                if succeed:
                    output_text = "added [{0}]: record {1} of {2}".format(counter + 1, response['id'], zone_name)
                    writer.writerow([zone_name, 'added', response['id']])
                else:
                    output_text = "failed [{0}]: while adding new record to {1}".format(
                        counter + 1, zone_name)
                    writer.writerow([zone_name, 'failed: ' + exception.message])
                print(output_text)
            return record_added_cb

        with open(domains_file_name) as f:
            print("Adding records to zones listed in {0}:".format(domains_file_name))
            for line in f:
                zone_name = line.strip()
                add_new_record(zone_name, record_type, record_name, record_content, record_added_cb=record_added_cb_wrapper(zone_name), cf_lib_wrapper=cf_lib_wrapper)
                counter += 1
            print("Added {0} records.".format(counter))
    print("CSV file {0} generated.".format(csv_name))


def cli_list_records(domains_file_name, cf_lib_wrapper):
    counter = 0
    dt = datetime.datetime.now()
    csv_name = "cf_list_records_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    with open(csv_name, "wb") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['zone name', 'record id', 'type', 'name', 'content'])

        def record_listed_cb_wrapper(zone_name):
            def record_listed_cb(succeed=None, response=None, exception=None):
                if succeed:
                    output_text = "{0}: record {1}. ID {2}. NAME {3}. CONTENT {4}".format(
                        zone_name, response['type'], response['id'], response['name'], response['content'])
                    writer.writerow(
                        [zone_name, response['id'], response['type'], response['name'], response['content']])
                else:
                    output_text = "{0}: {1}".format(zone_name, exception.message)
                    writer.writerow([zone_name, exception.message])
                print(output_text)
            return record_listed_cb

        with open(domains_file_name) as f:
            print("Listing DNS records from zones listed in {0}:".format(domains_file_name))
            for line in f:
                zone_name = line.strip()
                list_records(zone_name, record_listed_cb=record_listed_cb_wrapper(zone_name), cf_lib_wrapper=cf_lib_wrapper)
                counter += 1
            print("Listed records from {0} zones.".format(counter))
    print("CSV file {0} generated.".format(csv_name))


def cli_edit_records(domains_file_name, cf_lib_wrapper, record_type, record_name, old_record_content, new_record_content):
    counter = 0
    dt = datetime.datetime.now()
    csv_name = "cf_dns_edit_records_{0:04}{1:02}{2:02}_{3:02}{4:02}{5:02}.csv".format(
        dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    with open(csv_name, "wb") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['zone name', 'status', 'record id'])

        def record_edited_cb_wrapper(zone_name):
            def record_edited_cb(succeed=None, response=None, exception=None):
                if succeed:
                    output_text = "edited [{0}]: record {1} of {2}".format(counter + 1, response['id'], zone_name)
                    writer.writerow([zone_name, 'edited', response['id']])
                else:
                    output_text = "failed [{0}]: while editing record of {1}".format(
                        counter + 1, zone_name)
                    writer.writerow([zone_name, 'failed: ' + exception.message])
                print(output_text)
            return record_edited_cb

        with open(domains_file_name) as f:
            print("Editing records to zones listed in {0}:".format(domains_file_name))
            for line in f:
                zone_name = line.strip()
                edit_record(
                    zone_name, record_type, record_name, old_record_content, new_record_content,
                    record_edited_cb=record_edited_cb_wrapper(zone_name), cf_lib_wrapper=cf_lib_wrapper)
                counter += 1
            print("Edited {0} records.".format(counter))
    print("CSV file {0} generated.".format(csv_name))


@configured
def cli(args, cf_lib_wrapper=None):
    try:
        opts, args = getopt.getopt(
            args, '', [
                'add-new-domains', 'delete-all-records', 'add-new-records', 'list-records', 'edit-records',
                'type=', 'name=', 'content=', 'old-content=', 'new-content='
            ])
    except getopt.GetoptError:
        print(usage_str)
        return

    cmd_set = {'--add-new-domains', '--delete-all-records', '--add-new-records', '--list-records', '--edit-records'}
    cmd = None
    record_type = None
    record_name = None
    record_content = None
    old_record_content = None
    new_record_content = None
    for opt, arg in opts:
        if opt in cmd_set:
            cmd = opt
        else:
            if opt == '--type':
                record_type = arg
            elif opt == '--name':
                record_name = arg
            elif opt == '--content':
                record_content = arg
            elif opt == '--old-content':
                old_record_content = arg
            elif opt == '--new-content':
                new_record_content = arg

    if cmd is None or len(args) < 1:
        print(usage_str)
        return

    domains_file_name = args[0]

    if cmd == '--add-new-domains':
        cli_add_new_domains(domains_file_name, cf_lib_wrapper)
    elif cmd == '--delete-all-records':
        cli_delete_all_records(domains_file_name, cf_lib_wrapper)
    elif cmd == '--add-new-records':
        cli_add_new_records(domains_file_name, cf_lib_wrapper, record_type, record_name, record_content)
    elif cmd == '--list-records':
        cli_list_records(domains_file_name, cf_lib_wrapper)
    elif cmd == '--edit-records':
        cli_edit_records(domains_file_name, cf_lib_wrapper, record_type, record_name, old_record_content, new_record_content)


if __name__ == "__main__":
    cli(sys.argv[1:])
