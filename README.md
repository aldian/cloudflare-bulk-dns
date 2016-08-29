# cloudflare-dns

As we are using the library at https://pypi.python.org/pypi/cloudflare and the library is using Python 2.7,
We will also use Python 2.7

Put your CloudFlare API key and email in environment variables named CLOUDFLARE_API_KEY and CLOUDFLARE_API_EMAIL

In the mean time, there are 5 usages of this command line app:

```bash
cloudflare_dns/bulk_dns.py --add-new-domain <domain_list_file>
cloudflare_dns/bulk_dns.py --delete-all-records <domain_list_file>
cloudflare_dns/bulk_dns.py --list-records <domain_list_file>
cloudflare_dns/bulk_dns.py --add-new-records --type <record_type> --name <record_name> --content <record_content> <domain_list_file>
cloudflare_dns/bulk_dns.py --edit-records --type <record_type> --name <record_name> --old-content <old_content> --new-content <new_content> <domain_list_file>
```
