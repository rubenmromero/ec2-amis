#!/usr/bin/python

#
# Modules Import
#
import sys, os, argparse, time, subprocess, shlex, json, requests
from operator import itemgetter

#
# Variables Definition
#
instance_id_metadata_url = 'http://169.254.169.254/latest/meta-data/instance-id'

#
# Function to parse the input arguments and build the help message
#
def arguments_parser():
    parser = argparse.ArgumentParser(description='Tool to create and rotate EC2 AMIs and associated snapshots', add_help=False)

    options = parser.add_argument_group('Options')
    options.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    options.add_argument('-n', '--name', type=str, action='store', dest='ami_name', required=True, help='Name for the AMI to create or rotate')
    options.add_argument('-t', '--time', action='store_true', dest='time', help='Add the time to the name format: AMI_NAME-AAAA_MM_DD-HH_MM (default: AMI_NAME-AAAA_MM_DD)')
    options.add_argument('-d', '--description', type=str, action='store', dest='ami_description', default='TBD', help='Description for the AMI to create (default: AMI_NAME AMI created by '+os.path.basename(sys.argv[0])+')')
    options.add_argument('-i', '--instance-id', type=str, action='store', dest='instance_id', default='TBD', help='Instance ID from which create the AMI (default: Self Instance ID)')
    options.add_argument('-r', '--reboot', action='store_true', dest='reboot', help='Reboot the instance to create the AMI (default: No reboot)')
    options.add_argument('-b', '--block-device-mappings', type=str, action='store', dest='block_device_list_json', default='TBD', help='JSON format list of one or more block device mappings to include in the AMI (default: Include all block device mappings attached to the instance)')
    options.add_argument('-c', '--rotation-copies', type=int, action='store', dest='copies_number', default=10, help='Number of copies for rotation (default: 10)')

    commands = parser.add_argument_group('Actions')
    commands.add_argument('command', type=str, choices=['create', 'rotate'], help='Command to be exectuted')

    args = parser.parse_args()
    return args

#
# Function to deregister an AMI and delete its associated snapshots
#
# Input argument => ami_info : Dictionary that contains the AMI attributes
#
def deregister_ami(ami_info):
    # Deregister the AMI
    image_id = str(ami_info['ImageId'])
    print '\nIt proceeds to deregister "'+image_id+'" AMI with "'+ami_info['Name']+'" name:'
    deregister_ami_command = shlex.split('aws ec2 deregister-image --image-id '+image_id)
    output, error = subprocess.Popen(deregister_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if output != '':
        print output
    if error != '':
        print error

    # Delete the associated snapshots
    for device in ami_info['BlockDeviceMappings']:
        # If device is an EBS volume, it proceeds to delete the associated snapshot
        if 'Ebs' in device:
            snapshot_id = str(device['Ebs']['SnapshotId'])
            print '\nIt proceeds to delete "'+snapshot_id+'" associated snapshot:'
            delete_snapshot_command = shlex.split('aws ec2 delete-snapshot --snapshot-id '+snapshot_id)
            output, error = subprocess.Popen(delete_snapshot_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
            if output != '':
                print output
            if error != '':
                print error

#
# Main
#

# Parsing of input arguments
arguments = arguments_parser()

# If the specified action is 'create', the following block is executed
if (arguments.command == 'create'):
    # Definition of required parameters to create AMIs
    if arguments.time:
        actual_date = time.strftime('%Y_%m_%d-%H_%M')
    else:
        actual_date = time.strftime('%Y_%m_%d')
    ami_name = arguments.ami_name+'-'+actual_date

    if (not arguments.ami_description) or (arguments.ami_description == 'TBD'):
        ami_description = '"'+arguments.ami_name+' AMI created by '+os.path.basename(sys.argv[0])+'"'
    else:
        ami_description = '"'+arguments.ami_description+'"'

    if (not arguments.instance_id) or (arguments.instance_id == 'TBD'):
        try:
            instance_id = str(requests.get(instance_id_metadata_url).text)
        except requests.exceptions.RequestException as err:
            print '\nThis is not an EC2 instance, so --instance_id option must be specified\n'
            os.system(__file__+' --help')
            exit(1)
    else:
        instance_id = arguments.instance_id

    if (not arguments.block_device_list_json) or (arguments.block_device_list_json == 'TBD'):
        block_device_list_json = None
    else:
        block_device_list_json = arguments.block_device_list_json

    # Check if already exists any created AMI with ami_name name
    describe_ami_command = shlex.split('aws ec2 describe-images --owner self --filters Name=name,Values='+ami_name)
    output, error = subprocess.Popen(describe_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Decoding of JSON response
    try:
        result = json.loads(output)
    except ValueError as err:
        print error
        exit(255)

    # If already exists a created AMI with ami_name name, it proceeds to deregister in order to create it again
    if (result['Images']) and (result['Images'][0]['Name'] == ami_name):
        print '\nAlready exists an AMI with "'+ami_name+'" name. This AMI will be deleted before create the new one...'
        deregister_ami(result['Images'][0])

    print '\nCreation of "'+ami_name+'" AMI with',ami_description,'description from "'+instance_id+'" instance:'
    if block_device_list_json is None:
        if arguments.reboot:
            create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description)
        else:
            create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description+' --no-reboot')
    else:
        if arguments.reboot:
            create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description+' --block-device-mappings \''+block_device_list_json+'\'')
        else:
            create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description+' --block-device-mappings \''+block_device_list_json+'\' --no-reboot')
    output, error = subprocess.Popen(create_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    if output != '':
        print output
    if error != '':
        print error

# If the specified action is 'rotate', the following block is executed
if (arguments.command == 'rotate'):
    # Definition of required parameters to rotate AMIs
    if arguments.time:
        filter_date = '????_??_??-??_??'
    else:
        filter_date = '????_??_??'
    filter_name = arguments.ami_name+'-'+filter_date

    rotation_copies = arguments.copies_number

    # Get the list of registered AMIs which name match the filter_name pattern
    describe_ami_command = shlex.split('aws ec2 describe-images --owner self --filters Name=name,Values='+filter_name)
    output, error = subprocess.Popen(describe_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    # Decoding of JSON response
    try:
        result = json.loads(output)
    except ValueError as err:
        print error
        exit(255)

    # Sort the AMIs list by the 'Name' attribute
    sorted_images = sorted(result['Images'], key=itemgetter('Name'), reverse=True)

    print '\nAMIs currently registered:\n'
    for ami in sorted_images:
        print '\t'+ami['Name']

    if (len(sorted_images) > rotation_copies):
        print '\nThere are',len(sorted_images) - rotation_copies,'AMIs to deregister...'
        for i in xrange(rotation_copies, len(sorted_images)):
            deregister_ami(sorted_images[i])
    else:
        print '\nThe number of registered AMIs with "'+filter_name+'" name pattern is less or equal than the rotation copies number. No need to deregister any AMIs\n'
