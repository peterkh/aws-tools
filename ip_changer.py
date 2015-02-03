import boto.ec2
import boto.s3
import boto.sns
import requests
from boto.s3.key import Key

def search_for_rule(cidr, sg):
    for rule in sg.rules:
        sources = [c.cidr_ip for c in rule.grants]
        if cidr in sources and rule.to_port == '22' and rule.from_port == '22' and rule.ip_protocol == 'tcp':
            return True
    return False

def send_sns(message):
    sns_conn = boto.sns.connect_to_region('ap-southeast-2')
    sns_conn.publish(topic='xxxx', message=message)

if __name__ == '__main__':
    sg_name = 'xxxx'
    bucket_name = 'xxxx'

    s3conn = boto.s3.connect_to_region('ap-southeast-2')
    bucket = s3conn.get_bucket(bucket_name)
    
    k = Key(bucket)
    k.key = 'ip_changer.txt'
    old_cidr = k.get_contents_as_string()
    #print "The old IP is: %s" % old_cidr

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
        send_sns('IP_changer: Unable to get new IP address.')
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
        if sg.name == sg_name:
            #print "Found SG %s" % sg_name
            if search_for_rule(old_cidr, sg):
                message += "Found rule for old IP %s, removing.\n" % old_cidr
                sg.revoke('tcp', 22, 22, cidr_ip=old_cidr)
            if search_for_rule(current_cidr, sg):
                message += "Found rule for new IP %s already, nothing to do.\n" % current_cidr
            else:
                sg.authorize('tcp', 22, 22, current_cidr)
                message += "Adding rule for new IP %s.\n" % current_cidr
            k.set_contents_from_string(current_cidr)
            send_sns(message)


