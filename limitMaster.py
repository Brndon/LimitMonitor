#!bin/bash/python

import boto3
import ConfigParser

#Sets up the process to read the config file
config = ConfigParser.ConfigParser()
config_dict = {}
regions = []
config.read("accounts.config")
options = config.options('Settings')
for option in options:
	config_dict[option] = config.get('Settings', option)

ids = config_dict['id'].split(',')

lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
	for id in ids:
		print "do stuff here with AWS account "+id+"\n"
		response = lambda_client.invoke(
			FunctionName='LimitMonkeyEE',
			InvocationType='Event',
			ClientContext='string',
			Payload=id 
		)
	return;
