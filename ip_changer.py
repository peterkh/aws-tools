import boto.ec2
import boto.s3
import boto.sns
import ConfigParser
import os.path
import requests
from boto.s3.key import Key

def read_config():
    conf_dict = {}
    config_file = os.path.expanduser('~/.ip_changer')
    config = ConfigParser.ConfigParser()
    if os.path.isfile(config_file):
        config.read(config_file)
    else:
        print "Cannot load config file: %s" % config_file
        exit(1)
    for opt in config.options('default'):
        value = config.get('default', opt)
        if opt == 'tcp_ports':
            try:
                conf_dict[opt] = set([int(port) for port in value.split(" ")])
            except ValueError:
                print "Invalid port numbers passed in for tcp_ports: %s" % value
                exit(1)
        else:
            conf_dict[opt] = value
    return conf_dict

def search_for_rule(cidr, sg):
    for rule in sg.rules:
        sources = [c.cidr_ip for c in rule.grants]
        if cidr in sources and rule.to_port == '22' and rule.from_port == '22' and rule.ip_protocol == 'tcp':
            return True
    return False

def send_sns(message, region, topic):
    sns_conn = boto.sns.connect_to_region(region)
    sns_conn.publish(topic=topic, message=message)

if __name__ == '__main__':
    config = read_config()

    s3conn = boto.s3.connect_to_region(config['region'])
    bucket = s3conn.get_bucket(config['bucket_name'])

    k = Key(bucket)
    k.key = '%s/ip_changer_%s.txt' % (config['bucket_path'], config['ip_source_name'])
    try:
        old_cidr = k.get_contents_as_string()
    except boto.exception.S3ResponseError:
        old_cidr = '0.0.0.0/0'

    t = 0
    got_ip = False
    while t < 5:
        try:
            r = requests.get('http://ifconfig.me/ip')
            got_ip = True
            break
        except:
            t += 1
            pass
    if not got_ip:
        send_sns('IP_changer: Unable to get new IP address.', config['region'], config['sns_topic'])
        exit(1)
    current_ip = r.text.strip()
    current_cidr = '%s/32' % current_ip

    if old_cidr == current_cidr:
        #print "Old and current IPs the same, nothing to do."
        exit(0)


    #print "My IP is %s" % current_ip
    
    conn = boto.ec2.connect_to_region('ap-southeast-2')

    rs = conn.get_all_security_groups()
    message = 'IP_changer:\n'

    for sg in rs:
        if sg.name == config['security_group_name']:
            #print "Found SG %s" % sg_name
            if search_for_rule(old_cidr, sg):
                message += "Found rule for old IP %s, removing.\n" % old_cidr
                sg.revoke('tcp', 0, 65535, cidr_ip=old_cidr)
            if search_for_rule(current_cidr, sg):
                message += "Found rule for new IP %s already, nothing to do.\n" % current_cidr
            else:
                sg.authorize('tcp', 0, 65535, current_cidr)
                message += "Adding rule for new IP %s.\n" % current_cidr
            k.set_contents_from_string(current_cidr)
            send_sns(message, config['region'], config['sns_topic'])


