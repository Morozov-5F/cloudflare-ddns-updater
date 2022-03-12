#!/usr/bin/env python3

import requests
import argparse

parser = argparse.ArgumentParser(description="Update DNS record in Cloudflare DNS service")
parser.add_argument('-z', '--zone_id', required=False, help="Zone ID")
parser.add_argument('-n', '--zone_name', required=False, help="Zone Name")
parser.add_argument('record_name', help="DNS record name to modify")
parser.add_argument('-e', '--email', required=True, help="Email address for authentication")
parser.add_argument('-t', '--token', required=True, help="Access token for modifying the zone")
args = parser.parse_args()

auth_email = args.email
auth_key = args.token
record_name = args.record_name

zone_id = args.zone_id
zone_name = args.zone_name

if not zone_id and not zone_name:
    print('error: Either --zone_id or --zone_name should be specified')
    exit(1)

if zone_id and zone_name:
    print('warning: Both --zone_id and --zone_name are specified, using --zone_id for requests')


headers = { 'X-Auth-Email': auth_email, 'Authorization': f'Bearer {auth_key}', 'Content-Type': 'application/json'}

if zone_name and not zone_id:
    zone_resp = requests.get(f'https://api.cloudflare.com/client/v4/zones?name={zone_name}', headers=headers)
    resp = zone_resp.json()
    if not zone_resp.ok or not resp['success']:
        print(f'error: Unable to get the zone info, status {zone_resp.status_code}, response: "{zone_resp.text}"')
        exit(1)

    if len(resp['result']) == 0:
        print(f'error: Zone with the given name does not exist')
        exit(1)

    zone_id = resp['result'][0]['id']

dns_record_resp = requests.get(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}', headers=headers)
dns_record = dns_record_resp.json()
if not dns_record_resp.ok or not dns_record['success']:
    print(f'error: Unable to get the DNS record info, status {dns_record_resp.status_code}, response: "{dns_record_resp.text}"')
    exit(1)

if len(dns_record['result']) == 0:
    print(f'error: DNS record with the given name does not exist in the specified zone')
    exit(1)

dns_record = dns_record['result'][0]
old_ip = dns_record['content']
record_type = dns_record['type']
record_id = dns_record['id']
record_ttl = dns_record['ttl']
record_proxied = dns_record['proxied']

current_ip_resp = requests.get('https://v4.ident.me')
if not current_ip_resp.ok:
    print(f'error: unable to get the current IP, server responded with "{current_ip_resp.status_code}" code, response text: {current_ip_resp.text}')
    exit(1)

current_ip = current_ip_resp.text

if current_ip == old_ip:
    print(f'Old IP ({old_ip}) is equal to Current IP ({current_ip}), skipping update')
    exit(0)

data = {
    'type': record_type,
    'ttl': record_ttl,
    'content': current_ip,
    'proxied': record_proxied,
    'name': record_name
}
update_resp = requests.put(f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}', headers=headers, json=data)
if not update_resp.ok or not update_resp.json()['success']:
    print(f'error: Unable to update the DNS record info, status {update_resp.status_code}, response: "{update_resp.text}"')
    exit(1)

print('DNS record update successfully, all done')
