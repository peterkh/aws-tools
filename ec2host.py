#! /usr/bin/env python
import argparse
import boto.ec2 as ec2
import ConfigParser
import os
from os.path import expanduser

default_region_env = os.environ.get('AWS_DEFAULT_REGION')

config = ConfigParser.SafeConfigParser()
if default_region_env:
    config.set('DEFAULT', 'region', default_region_env)
else:
    config.set('DEFAULT', 'region', 'ap-southeast-2')
config.set('DEFAULT', 'role_tag', 'role')
config.read("%s/.awstools.conf" % (expanduser("~")))

conf_parser = argparse.ArgumentParser()
conf_parser.add_argument("-r", "--region", dest="region", default=config.get('DEFAULT', 'region'), help="EC2 region instances are located in")
conf_parser.add_argument("-t", "--tag", dest="tag", default=config.get('DEFAULT', 'role_tag'), help="The AWS tag name to search for instances with")
conf_parser.add_argument("-s", "--script_mode", action='store_true', default=False, help="Output in script friendly mode (IP address list only)")
conf_parser.add_argument("role_name")

args = conf_parser.parse_args()

region = args.region
tag = args.tag
script_mode = args.script_mode
filters = []

if tag.find(',') >= 0:
    for t in tag.split(','):
        filters.append({ "tag:%s" % (t): args.role_name })
else:
    filters.append({ "tag:%s" % (tag): args.role_name })

if not script_mode:
    print "Region: %s" % (region)
    print "Hosts with tag: %s:%s" % (tag, args.role_name)

ec2_conn = ec2.connect_to_region(region)

for ec2_filter in filters:

    reservations = ec2_conn.get_all_instances(filters=ec2_filter)
    instances = [i for r in reservations for i in r.instances]

    for instance in instances:
        if script_mode:
            print instance.private_ip_address
        else:    
            print "%s %s %s %s" % (instance.tags['Name'], instance.id, instance.private_ip_address, instance.ip_address)

