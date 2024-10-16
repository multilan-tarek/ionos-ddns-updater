import os
import time
import urllib.request
import sys
from urllib.error import HTTPError, URLError
import json
from dns import resolver


def get_env(key_, default):
    value = os.environ.get(key_)
    if value is None:
        return default
    return value


check_interval = int(get_env("CHECK_INTERVAL", 180))
hostnames = get_env("HOSTNAMES", "").replace(" ", "").split(",")
prefix = get_env("PREFIX", "")
key = get_env("KEY", "")
description = get_env("DESCRIPTION", "DDNS Update")
api_url = get_env("API_URL", "https://api.hosting.ionos.com/dns/v1/dyndns")
public_ip_url = get_env("PUBLIC_IP_URL", "https://ident.me")
dns_servers = ['1.1.1.1', '8.8.8.8']


def get_update_url():
    sys.stdout.write("Getting Update URL... ")

    json_body = json.dumps({
        "domains": hostnames,
        "description": description
    })
    json_body_bytes = json_body.encode("utf-8")

    request = urllib.request.Request(api_url)
    request.add_header("Content-Type", "application/json; charset=utf-8")
    request.add_header("accept", "application/json")
    request.add_header("X-API-Key", "%s.%s" % (prefix, key))
    try:
        response = urllib.request.urlopen(request, json_body_bytes)
        response = response.read().decode("utf-8")
        response_json = json.loads(response)
        sys.stdout.write("Done\n")
        return response_json["updateUrl"]

    except HTTPError as error:
        sys.stdout.write("Failed\n")
        if error.code == 429:
            sys.stderr.write("API returned: 429 Too many requests, retrying in 10 minutes...\n")
            time.sleep(600)
        else:
            sys.stderr.write(f"API returned: Unknown error  ({error.code}), retrying in 60 seconds...\n")
            time.sleep(60)
        return get_update_url()

    except URLError as error:
        sys.stdout.write("Failed\n")
        sys.stderr.write(f"Error: {error}\n")


update_url = get_update_url()

while True:
    try:
        sys.stdout.write("Getting Public IP... ")
        public_ip = urllib.request.urlopen(public_ip_url).read().decode("utf-8")
        sys.stdout.write("Done\n")
        sys.stdout.write(f"Public IP: {public_ip}\n")
        sys.stdout.write("Checking Hostname IPs... ")

        nx_hostnames = []
        update_hostnames = []
        for hostname in hostnames:
            try:
                res = resolver.Resolver()
                res.nameservers = dns_servers
                answers = res.resolve(hostname)
                for rdata in answers:
                    ip_address = rdata.address

                    if str(ip_address) != str(public_ip):
                        update_hostnames.append(hostname)

            except resolver.NXDOMAIN:
                hostnames.remove(hostname)
                nx_hostnames.append(hostname)

        sys.stdout.write("Done\n")

        if nx_hostnames:
            sys.stderr.write("Following Hostnames returned NXDOMAIN:\n")
            for hostname in nx_hostnames:
                sys.stderr.write(f"- {hostname}\n")
            sys.stdout.write("\n")

        if update_hostnames:
            sys.stderr.write("Following Hostnames need to be updated:\n")
            for hostname in update_hostnames:
                sys.stderr.write(f"- {hostname}\n")

            sys.stdout.write("Updating Hostnames... \n")
            try:
                update_request = urllib.request.urlopen(update_url)

            except HTTPError as update_error:
                sys.stdout.write("Failed\n")
                if update_error.code == 429:
                    sys.stderr.write("API returned: 429 Too many requests\n")
                else:
                    sys.stderr.write(f"API returned: Unknown error  ({update_error.code})\n")
                    time.sleep(60)

            except URLError as update_error:
                sys.stdout.write("Failed\n")
                sys.stderr.write(f"Error: {update_error}\n")

        else:
            sys.stdout.write("All Hostname IPs are up to date\n")

    except HTTPError as public_ip_error:
        sys.stderr.write(f"Public IP API: Unknown error {public_ip_error.code}\n")
    except URLError as public_ip_error:
        sys.stderr.write(f"Error: {public_ip_error}\n")

    time.sleep(check_interval)
