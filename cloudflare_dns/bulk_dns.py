import os
import sys
from functools import wraps
from CloudFlare.exceptions import CloudFlareAPIError
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


@configured
def add_new_domains(domain_names, domain_added_cb=None, cf_lib_wrapper=None):
    for domain_name in domain_names:
        try:
            zone_info = cf_lib_wrapper.create_a_zone(domain_name)
            if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
                domain_added_cb(succeed=True, response=zone_info)
        except CloudFlareAPIError as e:
            if "already exists" not in e.message:
                raise e
            if domain_added_cb is not None and hasattr(domain_added_cb, '__call__'):
                domain_added_cb(succeed=False, exception=e)


@configured
def cli(args, cf_lib_wrapper=None):
    pass

if __name__ == "__main__":
    cli(sys.argv[1:])
