# cloudflare-dns

As we are using the library at https://pypi.python.org/pypi/cloudflare and the library is using Python 2.7,
We will also use Python 2.7

Put your CloudFlare API key and email in environment variables.
```bash
export CLOUDFLARE_API_KEY=<your key>
export CLOUDFLARE_API_EMAIL=<your email>
```

There are 5 basic usages of this command line app:

```bash
cloudflare_dns/bulk_dns.py --add-new-domain <domain_list_file>
cloudflare_dns/bulk_dns.py --delete-all-records <domain_list_file>
cloudflare_dns/bulk_dns.py --list-records <domain_list_file>
cloudflare_dns/bulk_dns.py --add-new-records --type <record_type> [--name <record_name>] --content <record_content> <domain_list_file>
cloudflare_dns/bulk_dns.py --edit-records --type <record_type> [--name <record_name>] [--old-content <old_content>] --new-content <new_content> <domain_list_file>
```

There are common cases that the record content should refer to its zone name. For example, when you are creating an alias to an A record.
In that case, you can add and edit records like these:

```bash
cloudflare_dns/bulk_dns.py --add-new-records --type CNAME --name www --content {{zone}} my_domains.txt 
cloudflare_dns/bulk_dns.py --edit-records --type CNAME --name www --new-content hello.{{zone}} my_domains.txt
```
