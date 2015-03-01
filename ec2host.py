#! /usr/bin/env python
import argparse
import boto.ec2 as ec2
import ConfigParser
import os
import shlex
from os.path import expanduser
from subprocess import check_call

def get_instances(region, tags, tag_value, profile):
    filters = []
    all_instances = []
    for tag in tags:
        filters.append({ "tag:%s" % (tag): tag_value })

    print "using profile: %s" % profile
    for ec2_filter in filters:
        ec2_conn = ec2.connect_to_region(region, profile_name=profile)
        reservations = ec2_conn.get_all_instances(filters=ec2_filter)
        all_instances += [i for r in reservations for i in r.instances]
    return all_instances

def get_role_names(region, tags, profile):
    filters = []
    all_role_names = []
    for tag in tags:
        filters.append({ 'tag-key': tag, 'resource-type': 'instance' })
    for ec2_filter in filters:
        ec2_conn = ec2.connect_to_region(region, profile_name=profile)
        tags = ec2_conn.get_all_tags(filters=ec2_filter)
        all_role_names += [str(t.value) for t in tags]
    return sorted(list(set(all_role_names)))


default_region_env = os.environ.get('AWS_DEFAULT_REGION')

config = ConfigParser.SafeConfigParser()
if default_region_env:
    config.set('DEFAULT', 'region', default_region_env)
else:
    config.set('DEFAULT', 'region', 'ap-southeast-2')
config.set('DEFAULT', 'role_tag', 'role')
config.set('DEFAULT', 'host_script', '/usr/local/bin/csshX')
config.set('DEFAULT', 'profile', '')
config.set('DEFAULT', 'separator', ' ')
config.read("%s/.awstools.conf" % (expanduser("~")))

conf_parser = argparse.ArgumentParser()
conf_parser.add_argument("-R", "--get-roles", dest="get_roles", default=False, action='store_true', help="Get a list of roles in the region")
conf_parser.add_argument("-r", "--region", dest="region", default=config.get('DEFAULT', 'region'), help="EC2 region instances are located in")
conf_parser.add_argument("-p", "--profile", dest="profile", default=config.get('DEFAULT', 'profile'), help="Boto profile name to use")
conf_parser.add_argument("-t", "--tag", dest="tag", default=config.get('DEFAULT', 'role_tag'), help="The AWS tag name to search for instances with")
conf_parser.add_argument("-s", "--script_mode", action='store_true', default=False, help="Output in script friendly mode (IP address list only)")
conf_parser.add_argument("-S", "--script_run_mode", action='store_true', default=False, help="Output in script friendly mode and runs host_script in config. Defaults to csshx")
conf_parser.add_argument("--separator", dest='separator', default=config.get('DEFAULT', 'separator'), help="Character used to separate ip addresses when using -S. Defaults to space")
conf_parser.add_argument("--host_script", dest="host_script", default=config.get('DEFAULT', 'host_script'), help="The script to run against lists of hosts when using -S")
conf_parser.add_argument("role_name", default="", nargs='*')

args = conf_parser.parse_args()

region = args.region

if args.tag.find(',') >= 0:
    tag = args.tag.split(',')
else:
    tag = [args.tag]

if args.profile == '':
    profile = None
else:
    profile = args.profile

script_mode = args.script_mode or args.script_run_mode
script_run_mode = args.script_run_mode
host_script = args.host_script
separator = args.separator
filters = []
all_instances = []

if args.get_roles:
    role_list = get_role_names(region, tag, profile)
    for role in role_list:
        print role
    exit(0)
else:
    if not args.role_name:
        print "Error: Must provide a role name to search for"
        conf_parser.print_help()
        exit(1)

for role in args.role_name:
    all_instances += get_instances(region, tag, role, profile)

if not script_mode:
    print "Region: %s" % (region)
    print "Hosts with tag: %s:%s" % (tag, args.role_name)

for instance in all_instances:
    if script_mode:
        print instance.private_ip_address
    else:
        print "%s %s %s %s" % (instance.tags['Name'], instance.id, instance.private_ip_address, instance.ip_address)

if script_run_mode:
    ip_string = str(separator.join([instance.private_ip_address for instance in all_instances]))
    print ip_string
    check_call(shlex.split(host_script + " " + ip_string))
