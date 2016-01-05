# LimitMonkey

Lambda application to periodically query Trusted Advisor for your AWS resource limits 
and publish messages to an SNS topic as a proactive alarm. Think "Push over Pull" for AWS Limits.

## Requirements

This sample project depends on Boto3, the AWS SDK for Python, and requires
Python 2.6 or 2.7. You can install Boto using pip:

    pip install boto

## Basic Configuration

You need to set up your AWS security credentials before the sample code is able
to connect to AWS. You can do this by creating a file named "credentials" at ~/.aws/ 
(C:\Users\USER_NAME\.aws\ for Windows users) and saving the following lines in the file:

    [default]
    aws_access_key_id = <your access key id>
    aws_secret_access_key = <your secret key>

See the [Security Credentials](http://aws.amazon.com/security-credentials) page
for more information on getting your keys. It's also possible to configure your
credentials via other configuration files. See the [Boto Config documentation](http://boto.readthedocs.org/en/latest/boto_config_tut.html)
for more information.

## License

This sample application is distributed under the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

