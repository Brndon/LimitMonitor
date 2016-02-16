#!bin/bash/python

import boto3
import ConfigParser
import json
import requests

def lambda_handler(event, context):
    print json.dumps(event) # Dump Event Data for troubleshooting
    responseStatus = 'SUCCESS'
    targetResponse = {}
    # If the CloudFormation Stack is being deleted, exit with success
    # To Do - Delete Role and Schedule Resoures
    if event['RequestType'] == 'Delete':
        sendResponse(event, context, responseStatus,targetResponse)

    # Establish connection with Lambda
    lambdaClient = boto3.client('lambda')
    # Establish connection with CloudWatch Events
    eventsClient = boto3.client('events')
    
    # Build Input String for Event JSON input
    inputString = '{\"CheckRoleName\":\"'+event['ResourceProperties']['CheckRoleName']+'\",\"Region\":\"'+event['ResourceProperties']['Region']+'\",\"AccountList\":'+json.dumps(event['ResourceProperties']['AccountList'])+',\"RegionList\":'+json.dumps(event['ResourceProperties']['RegionList'])+',\"ChildLambda\":\"'+event['ResourceProperties']['ChildLambda']+'\",\"SNSArn\":\"'+event['ResourceProperties']['SNSTopic']+'\"}'
    # Create rule to run every 24 hours
    ruleResponse = eventsClient.put_rule(Name='Limits', ScheduleExpression='rate(24 hours)',State='ENABLED')
    # Give the rule permission to invoke the Master Lambda
    lambdaResponse = lambdaClient.add_permission(FunctionName=event['ResourceProperties']['MasterLambda'], StatementId='Limits', Action='lambda:InvokeFunction', Principal='events.amazonaws.com', SourceArn=ruleResponse['RuleArn'])
    # Create target to have rule fire the Lambda function every 24 hours
    targetResponse = eventsClient.put_targets(Rule='Limits',Targets=[{'Id':'Limits','Arn':event['ResourceProperties']['MasterArn'],'Input':inputString}])
    # To Do - Error Handling
    # Dump Response Data for troubleshooting
    print json.dumps(ruleResponse)
    print json.dumps(lambdaResponse)
    print json.dumps(targetResponse)


    # Establish connection to IAM
    iamClient = boto3.client('iam')

    #Create a role for the Child Lambda to assume, attach required policies
    rolecreateresponse = iamClient.create_role(RoleName=event['ResourceProperties']['CheckRoleName'],AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"AWS": "'+event['ResourceProperties']['AccountNumber']+'"},"Action": "sts:AssumeRole"}]}')
    putpolicyresponsero = iamClient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess')
    putpolicyresponsesupport = iamClient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/AWSSupportAccess')
    putpolicyresponsecfn = iamClient.put_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyName='CloudFormationDescribe',PolicyDocument='{"Version": "2012-10-17","Statement": [{"Sid": "Stmt1455149881000","Effect": "Allow","Action": ["cloudformation:DescribeAccountLimits"],"Resource": ["*"]}]}')

    # To Do - Error Handling
    # Dump Response Data for troubleshooting
    print rolecreateresponse
    print putpolicyresponsero
    print putpolicyresponsesupport
    print putpolicyresponsecfn

    #Send response to CloudFormation to signal success so stack continues.  If there is an error, direct user at CloudWatch Logs to investigate responses
    sendResponse(event, context, responseStatus,targetResponse)
 
def sendResponse(event, context, responseStatus,targetResponse):
    #Build Response Body
    responseBody = {'Status': responseStatus,
                    'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
                    'PhysicalResourceId': context.log_stream_name,
                    'StackId': event['StackId'],
                    'RequestId': event['RequestId'],
                    'LogicalResourceId': event['LogicalResourceId'],
                    'Data': targetResponse}
    print 'RESPONSE BODY:\n' + json.dumps(responseBody)

    try:
        #Put response to pre-signed URL
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
