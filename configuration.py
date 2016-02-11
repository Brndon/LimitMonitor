#!bin/bash/python

import boto3
import ConfigParser
import json
import requests

def lambda_handler(event, context):
    responseStatus = 'SUCCESS'
    targetResponse = {}
    if event['RequestType'] == 'Delete':
        sendResponse(event, context, responseStatus,targetResponse)
    client = boto3.client('events')
    print json.dumps(event)
    inputString = '{\"CheckRoleName\":\"'+event['ResourceProperties']['CheckRoleName']+'\",\"Region\":\"'+event['ResourceProperties']['Region']+'\",\"AccountList\":'+json.dumps(event['ResourceProperties']['AccountList'])+',\"RegionList\":'+json.dumps(event['ResourceProperties']['RegionList'])+',\"ChildLambda\":\"'+event['ResourceProperties']['ChildLambda']+'\",\"SNSArn\":\"'+event['ResourceProperties']['SNSTopic']+'\"}'
    ruleResponse = client.put_rule(Name='Limits', ScheduleExpression='rate(24 hours)',State='ENABLED')
    targetResponse = client.put_targets(Rule='Limits',Targets=[{'Id':'Limits','Arn':event['ResourceProperties']['MasterArn'],'Input':inputString}])

    iamclient = boto3.client('iam')
    rolecreateresponse = iamclient.create_role(RoleName=event['ResourceProperties']['CheckRoleName'],AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"AWS": "'+event['ResourceProperties']['AccountNumber']+'"},"Action": "sts:AssumeRole"}]}')
    putpolicyresponsero = iamclient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess')
    putpolicyresponsesupport = iamclient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/AWSSupportAccess')
    putpolicyresponsecfn = iamclient.put_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyName='CloudFormationDescribe',PolicyDocument='{"Version": "2012-10-17","Statement": [{"Sid": "Stmt1455149881000","Effect": "Allow","Action": ["cloudformation:DescribeAccountLimits"],"Resource": ["*"]}]}')
    print ruleResponse
    print targetResponse
    print rolecreateresponse
    print putpolicyresponsero
    print putpolicyresponsesupport
    print putpolicyresponsecfn

    sendResponse(event, context, responseStatus,targetResponse)
 
def sendResponse(event, context, responseStatus,targetResponse):
    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': context.log_stream_name,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId'],
                    'Data': targetResponse}
    print 'RESPONSE BODY:\n' + json.dumps(responseBody)

    try:
        req = requests.put(event['ResponseURL'], data=json.dumps(responseBody))
        if req.status_code != 200:
            print req.text
            raise Exception('Recieved non 200 response while sending response to CFN.')
        return str(event)
    except requests.exceptions.RequestException as e:
        print req.text
        print e
        raise
 
if __name__ == '__main__':
    lambda_handler('event', 'handler')
