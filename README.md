# EC2-AMIs

Tool to create and rotate EC2 AMIs and associated snapshots.

## Prerequisites

* AWS IAM EC2 Role (only for executions from EC2 instances) or IAM User with the following associated IAM policy:

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

* AWS CLI for ec2 commands. Installation and configuration:

      $ sudo pip install awscli

      $ aws configure
      AWS Access Key ID [None]: <access_key>		# Leave blank in EC2 instances with associated IAM Role
      AWS Secret Access Key [None]: <secret_key>	# Leave blank in EC2 instances with associated IAM Role
      Default region name [None]: eu-west-1
      Default output format [None]:

* Requests module for Python. Installation:

      $ sudo pip install requests

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

    Actions:
      {create,rotate}       Command to be exectuted

## Execution Examples

* Create an AMI with AMI_NAME-AAAA_MM_DD name format from an EC2 instance with "i-12345678" id, executing the `ec2_ami.py` tool from your own workstation and rebooting the instance to create the AMI:

      $ ./ec2_ami.py --name Foo-Test --instance-id i-12345678 --reboot create

* Create an AMI with AMI_NAME-AAAA_MM_DD-HH_MM name format from an EC2 instance with "i-87654321" id, executing the `ec2_ami.py` tool from the own instance:

      $ ./ec2_ami.py --name Bar-Test --time create

* Rotate the existing AMIs registered with "Foo-Test-AAAA_MM_DD" name pattern keeping the last 7 most recent copies:

      $ ./ec2_ami.py --name Foo-Test --rotation-copies 7 rotate

* Rotate the existing AMIs registered with "Bar-Test-AAAA_MM_DD-HH_MM" name pattern keeping the last 20 most recent copies:

      $ ./ec2_ami.py --name Bar-Test --time --rotation-copies 20 rotate

## Related Links

* [Install the AWS CLI Using Pip](http://docs.aws.amazon.com/cli/latest/userguide/installing.html#install-with-pip)
* [Configuring the AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
