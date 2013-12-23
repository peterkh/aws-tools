#! /usr/bin/env python
import argparse
import boto.ec2 as ec2
import ConfigParser
import os
from os.path import expanduser



config = ConfigParser.SafeConfigParser()
config.set('DEFAULT', 'region', os.environ.get('AWS_DEFAULT_REGION'))
config.set('DEFAULT', 'role_tag', 'role')
config.read("%s/.awstools.conf" % (expanduser("~")))

conf_parser = argparse.ArgumentParser()
conf_parser.add_argument("-r", "--region", dest="region", help="EC2 region instances are located in")
conf_parser.add_argument("-t", "--tag", dest="tag", help="The AWS tag name to search for instances with")
conf_parser.add_argument("role_name")

args = conf_parser.parse_args()

if args.region:
    region = args.region
else:
    region = config.get('DEFAULT', 'region')
if args.tag:
    tag = args.tag
else:
    tag = config.get('DEFAULT', 'role_tag')

filters = []

if tag.find(',') >= 0:
    for t in tag.split(','):
        filters.append({ "tag:%s" % (t): args.role_name })
else:
    filters.append({ "tag:%s" % (tag): args.role_name })

print "Region: %s" % (region)
print "Hosts with tag: %s:%s" % (tag, args.role_name)

ec2_conn = ec2.connect_to_region(region)

for ec2_filter in filters:

    reservations = ec2_conn.get_all_instances(filters=ec2_filter)
    instances = [i for r in reservations for i in r.instances]

    for instance in instances:
        print "%s %s %s %s" % (instance.tags['Name'], instance.id, instance.private_ip_address, instance.ip_address)

