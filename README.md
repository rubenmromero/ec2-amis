# EC2-AMIs

Tool to create and rotate EC2 AMIs and associated snapshots.

## Prerequisites

* An IAM User or an AWS IAM Role attached to the EC2 instance (only for executions from EC2 instances) with the following IAM policy attached:

      Policy Name : EC2-ManageAMIs-<YYYYMMDD>

      {
          "Version": "2012-10-17",
          "Statement": [
              {
                  "Sid": "Stmt1430150596000",
                  "Effect": "Allow",
                  "Action": [
                      "ec2:CreateImage",
                      "ec2:DeleteSnapshot",
                      "ec2:DeregisterImage",
                      "ec2:DescribeImageAttribute",
                      "ec2:DescribeImages"
                  ],
                  "Resource": [
                      "*"
                  ]
              }
          ]
      }

* Pip tool for Python packages management. Installation:

      $ curl -O https://bootstrap.pypa.io/get-pip.py
      $ sudo python get-pip.py

* AWS SDK for Python. Installation:

      $ sudo pip install boto3

* Requests module for Python. Installation:

      $ sudo pip install requests

* AWS CLI to configure the profile to use (access key and/or region). Installation and configuration:

      $ sudo pip install awscli

      $ aws configure [--profile <profile-name>]
      AWS Access Key ID [None]: <access_key_id>         # Leave blank in EC2 instances with associated IAM Role
      AWS Secret Access Key [None]: <secret_access_key> # Leave blank in EC2 instances with associated IAM Role
      Default region name [None]: <region>              # eu-west-1, eu-central-1, us-east-1, ...
      Default output format [None]:

## Configuration

1. Download the project code in your favourite path:

       $ git clone https://github.com/rubenmromero/ec2-amis.git

2. If you want to schedule the periodic tool execution, copy the [ec2-amis](cron.d/ec2-amis) template to the `/etc/cron.d` directory and replace the existing `<tags>` with the appropiate values:

       # From the project root folder
       $ sudo cp cron.d/ec2-amis /etc/cron.d
       $ sudo vi /etc/cron.d/ec2-amis

## Execution Method

Here you have the message that you will get if you request help to the `ec2_ami.py` tool:

    $ ./ec2_ami.py --help
    usage: ec2_ami.py [-h] -n AMI_NAME [-t] [-d AMI_DESCRIPTION] [-i INSTANCE_ID]
                      [-r] [-b BLOCK_DEVICE_LIST_JSON] [-c COPIES_NUMBER]
                      [-p PROFILE]
                      {create,rotate}

    Tool to create and rotate EC2 AMIs and associated snapshots

    optional arguments:
      -h, --help            show this help message and exit

    Options:
      -n AMI_NAME, --name AMI_NAME
                            Name for the AMI to create or rotate
      -t, --time            Add the time to the name format: AMI_NAME-AAAA_MM_DD-
                            HH_MM (default: AMI_NAME-AAAA_MM_DD)
      -d AMI_DESCRIPTION, --description AMI_DESCRIPTION
                            Description for the AMI to create (default: AMI_NAME
                            AMI created by ec2_ami.py)
      -i INSTANCE_ID, --instance-id INSTANCE_ID
                            Instance ID from which create the AMI (default: Self
                            Instance ID)
      -r, --reboot          Reboot the instance to create the AMI (default: No
                            reboot)
      -b BLOCK_DEVICE_LIST_JSON, --block-device-mappings BLOCK_DEVICE_LIST_JSON
                            JSON format list of one or more block device mappings
                            to include in the AMI (default: Include all block
                            device mappings attached to the instance)
      -c COPIES_NUMBER, --rotation-copies COPIES_NUMBER
                            Number of copies for rotation (default: 10)
      -p PROFILE, --profile PROFILE
                            Use a specific profile from AWS CLI stored
                            configurations

    Actions:
      {create,rotate}       Command to execute

## Execution Examples

* Create an AMI with AMI_NAME-AAAA_MM_DD name format from an EC2 instance with 'i-12345678' id, executing the `ec2_ami.py` tool from your own workstation and rebooting the instance to create the AMI:

      $ ./ec2_ami.py --name Foo-Test --instance-id i-12345678 --reboot create

* Create an AMI with AMI_NAME-AAAA_MM_DD-HH_MM name format from an EC2 instance with 'i-87654321' id, executing the `ec2_ami.py` tool from the own instance:

      $ ./ec2_ami.py --name Bar-Test --time create

* Create an AMI with AMI_NAME-AAAA_MM_DD-HH_MM name format from an EC2 instance with 'i-12345678' id, executing the `ec2_ami.py` tool from your own workstation and including only the root device with several properties customized in the block device mapping of the AMI:

      $ ./ec2_ami.py --name Foo-Test --time --instance-id i-12345678 --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeType":"gp2","DeleteOnTermination":true}}]' create

* Create an AMI with AMI_NAME-AAAA_MM_DD name format from an EC2 instance with 'i-87654321' id, executing the `ec2_ami.py` tool from the own instance and suppressing the `/dev/sdf` device included in the block device mapping of the AMI:

      $ ./ec2_ami.py --name Bar-Test --block-device-mappings '[{"DeviceName":"/dev/sdf","NoDevice":""}]' create

* Rotate the existing AMIs registered with 'Foo-Test-AAAA_MM_DD' name pattern keeping the last 7 most recent copies:

      $ ./ec2_ami.py --name Foo-Test --rotation-copies 7 rotate

* Rotate the existing AMIs registered with 'Bar-Test-AAAA_MM_DD-HH_MM' name pattern keeping the last 20 most recent copies:

      $ ./ec2_ami.py --name Bar-Test --time --rotation-copies 20 rotate

## Related Links

* [AWS SDK for Python (Boto3)](https://aws.amazon.com/sdk-for-python/)
* [EC2 - Boto 3 Docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html)
* [Installing the AWS CLI Using pip](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv1.html#install-tool-pip)
* [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)
