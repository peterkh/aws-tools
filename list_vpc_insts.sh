#!/bin/bash
#use awscli to print a list of the private IPs of instances within a given VPC
vpc_name=$1
get_vpc_id="aws ec2 describe-vpcs --filter 'Name=tag:vpc-cn,Values=${vpc_name}' --query Vpcs[*].[VpcId] --output text"
id=$(eval $get_vpc_id)
get_instances="aws ec2 describe-instances --filter 'Name=vpc-id,Values=${id}' 'Name=instance-state-name,Values=running' --output text --query 'Reservations[*].Instances[*].[PrivateIpAddress]'"
ips=$(eval $get_instances)
for ip in $ips; do
    echo $ip
done
