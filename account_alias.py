#!/usr/bin/env python

import boto.iam

conn=boto.iam.connect_to_region('universal')

result = conn.get_account_alias()

print str(result['list_account_aliases_response']['list_account_aliases_result']['account_aliases'][0])
