# cloudflare-dns

As we are using the library at https://pypi.python.org/pypi/cloudflare and the library is using Python 2.7,
We will also use Python 2.7

Put your CloudFlare API key and email in environment variables named CLOUDFLARE_API_KEY and CLOUDFLARE_API_EMAIL

You can add domains by calling this CLI:
python cloudflare_dns/bulk_dns.py --add-new-domains example-domains.txt

