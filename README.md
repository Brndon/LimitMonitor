# LimitMonkey

We have created a CloudFormation template that you can run to start receiving alerts with just a couple of clicks.  You can configure the Limits Monitor to alert you as you are approaching limits, all via Scheduled Lambda functions, so there is no additional infrastructure to monitor.  

## Basic Configuration

You will need to download the Lambda functions which are contained in a zip file, and place them in an S3 bucket in your account.
The template will create three Lambda functions, a master function which will spawn a child function for each account it is checking, along with a configuration Lambda which will be used when launching the CloudFormation template to complete some final setup steps.


## License

This sample application is distributed under the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

