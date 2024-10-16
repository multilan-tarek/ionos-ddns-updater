import os
import time
import urllib.request
from urllib.error import HTTPError, URLError
import json
from dns import resolver
import logging


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

logger = logging.getLogger("IONOS-DDNS")

def get_update_url():
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
        response = response.read().decode(response.headers.get_content_charset())
        response_json = json.loads(response)
        return response_json["updateUrl"]

    except HTTPError as error:
        if error.code == 429:
            logger.error("API returned: 429 Too many requests, retrying in 10 minutes...")
            time.sleep(600)
        else:
            logger.error("API returned: Unknown error  (%s), retrying in 60 seconds..." % error.code)
            time.sleep(60)
        return get_update_url()
    except URLError as error:
        logger.error("Error: %s" % error)

logger.info("Getting update URL...")
update_url = get_update_url()

while True:
    needs_update = False
    try:
        public_ip = urllib.request.urlopen(public_ip_url).read().decode("utf8")
        logger.info("Checking if update is needed...")
        logger.info("Public IP: %s" % public_ip)

        for hostname in hostnames:
            try:
                res = resolver.Resolver()
                res.nameservers = dns_servers
                answers = res.resolve(hostname)
                for rdata in answers:
                    ip_address = rdata.address

                    if str(ip_address) == str(public_ip):
                        logger.info("%s IP (%s) is same as public IP" % (hostname, ip_address))
                    else:
                        logger.info("%s IP (%s) is not the same as public IP" % (hostname, ip_address))
                        needs_update = True

            except resolver.NXDOMAIN:
                hostnames.remove(hostname)
                logger.error("%s: Not found" % hostname)

        if needs_update:
            logger.info("Updating IPs...")
            try:
                update_request = urllib.request.urlopen(update_url)
                logger.info("Update successful (New IP: %s)" % public_ip)
            except HTTPError as update_error:
                if update_error.code == 429:
                    logger.error("API returned: 429 Too many requests")
                else:
                    logger.error("API returned: Unknown error  (%s)" % update_error.code)
                    time.sleep(60)
            except URLError as update_error:
                logger.error("Error: %s" % update_error)

    except HTTPError as public_ip_error:
        logger.error("Public IP API: Unknown error" % public_ip_error.code)
    except URLError as public_ip_error:
        logger.error("Error: %s" % public_ip_error)

    time.sleep(check_interval)
