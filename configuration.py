#!bin/bash/python

import boto3
import ConfigParser
import json
import requests

def lambda_handler(event, context):
    print "Event JSON: \n" + json.dumps(event) # Dump Event Data for troubleshooting
    responseStatus = 'SUCCESS'
    targetResponse = {}
    
    # If the CloudFormation Stack is being deleted, delete the limits and roles created
    if event['RequestType'] == 'Delete':
        try: # Remove targets and rules
            eventsClient = boto3.client('events')
            targetResponse = eventsClient.remove_targets(Rule='Limits',Ids=['Limits'])
            ruleResponse = eventsClient.delete_rule(Name='Limits')
        except:
            print targetResponse
            print ruleResponse
            pass

        try: # Remove IAM Role
            iamClient = boto3.client('iam')
            detachpolicyresponsero = iamClient.detach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess')
            detachpolicyresponsesupport = iamClient.detach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/AWSSupportAccess')
            deletepolicuresponse = iamClient.delete_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyName='CloudFormationDescribe')
            roledeleteresponse = iamClient.delete_role(RoleName=event['ResourceProperties']['CheckRoleName'])
        except:
            print detachpolicyresponsero
            print detachpolicyresponsesupport
            print deletepolicuresponse
            print roledeleteresponse
            pass

        sendResponse(event, context, responseStatus,targetResponse)

    # If the CloudFormation Stack is being updated, do nothing, exit with success
    if event['RequestType'] == 'Update':
        sendResponse(event, context, responseStatus,targetResponse)

    # If the Cloudformation Stack is being created, create the 
    if event['RequestType'] == 'Create':
        try: #Create Rule and Target, and give permission for target to run the Lambda function
            lambdaClient = boto3.client('lambda')
            eventsClient = boto3.client('events')
            # Build Input String for Event JSON input
            inputString = '{\"CheckRoleName\":\"'+event['ResourceProperties']['CheckRoleName']+'\",\"Region\":\"'+event['ResourceProperties']['Region']+'\",\"AccountList\":'+json.dumps(event['ResourceProperties']['AccountList'])+',\"RegionList\":'+json.dumps(event['ResourceProperties']['RegionList'])+',\"ChildLambda\":\"'+event['ResourceProperties']['ChildLambda']+'\",\"SNSArn\":\"'+event['ResourceProperties']['SNSTopic']+'\"}'
            # Create rule to run every 24 hours
            ruleResponse = eventsClient.put_rule(Name='Limits', ScheduleExpression='rate(24 hours)',State='ENABLED')
            # Give the rule permission to invoke the Master Lambda
            lambdaResponse = lambdaClient.add_permission(FunctionName=event['ResourceProperties']['MasterLambda'], StatementId='Limits', Action='lambda:InvokeFunction', Principal='events.amazonaws.com', SourceArn=ruleResponse['RuleArn'])
            # Create target to have rule fire the Lambda function every 24 hours
            targetResponse = eventsClient.put_targets(Rule='Limits',Targets=[{'Id':'Limits','Arn':event['ResourceProperties']['MasterArn'],'Input':inputString}])
        except:
            # Dump Response Data for troubleshooting
            print json.dumps(ruleResponse)
            print json.dumps(lambdaResponse)
            print json.dumps(targetResponse)
            pass

        try: # Create IAM Role for Child Lambda to assume
            iamClient = boto3.client('iam')
            rolecreateresponse = iamClient.create_role(RoleName=event['ResourceProperties']['CheckRoleName'],AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"AWS": "'+event['ResourceProperties']['AccountNumber']+'"},"Action": "sts:AssumeRole"}]}')
            putpolicyresponsero = iamClient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/ReadOnlyAccess')
            putpolicyresponsesupport = iamClient.attach_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyArn='arn:aws:iam::aws:policy/AWSSupportAccess')
            putpolicyresponsecfn = iamClient.put_role_policy(RoleName=event['ResourceProperties']['CheckRoleName'],PolicyName='CloudFormationDescribe',PolicyDocument='{"Version": "2012-10-17","Statement": [{"Sid": "Stmt1455149881000","Effect": "Allow","Action": ["cloudformation:DescribeAccountLimits"],"Resource": ["*"]}]}')
        except:
            # Dump Response Data for troubleshooting
            print rolecreateresponse
            print putpolicyresponsero
            print putpolicyresponsesupport
            print putpolicyresponsecfn
            pass

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
