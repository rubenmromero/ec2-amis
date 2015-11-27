#!/usr/bin/python

'''
Herramienta para la creacion y rotacion de AMIs y de sus snapshots
asociados, pertenecientes a instancias EC2

@autor Ruben
@fecha 24/09/2014

'''

#
# Importacion de modulos
#
import sys, os, argparse, time, subprocess, shlex, json, requests
from operator import itemgetter

#
# Definicion de variables
#
instance_id_metadata_url = 'http://169.254.169.254/latest/meta-data/instance-id'

#
# Funcion para el parseo de los argumentos de entrada y construccion del mensaje de ayuda
#
def arguments_parser():
   parser = argparse.ArgumentParser(description='Tool for create and rotate EC2 AMIs and associated snapshots', add_help=False)

   options = parser.add_argument_group('Options')
   options.add_argument('-h', '--help', action='help', help='Show this help message and exit')
   options.add_argument('-n', '--name', type=str, action='store', dest='ami_name', required=True, help='Name for the AMI to create or rotate')
   options.add_argument('-t', '--time', action='store_true', dest='time', help='Add the time to the name format: AMI_NAME-AAAA_MM_DD-HH_MM (default: AMI_NAME-AAAA_MM_DD)')
   options.add_argument('-d', '--description', type=str, action='store', dest='ami_description', default='TBD', help='Description for the AMI to create (default: AMI_NAME AMI created by '+os.path.basename(sys.argv[0])+')')
   options.add_argument('-i', '--instance-id', type=str, action='store', dest='instance_id', default='TBD', help='Instance ID from which create the AMI (default: Self Instance ID)')
   options.add_argument('-r', '--reboot', action='store_true', dest='reboot', help='Reboot the instance to create the AMI (default: No reboot)')
   options.add_argument('-c', '--rotation-copies', type=int, action='store', dest='rotation_copies', default=10, help='Number of copies for rotation (default: 10)')

   commands = parser.add_argument_group('Actions')
   commands.add_argument('command', type=str, choices=['create', 'rotate'], help='Command to be exectuted')

   args = parser.parse_args()
   return args

#
# Funcion para la eliminacion de una AMI y de sus snapshots asociados
#
# Argumento de entrada => ami_info : Diccionario que contiene los atributos de una AMI
#
def deregister_ami(ami_info):
   # Se deregistra la AMI
   image_id = str(ami_info['ImageId'])
   print '\nIt proceeds to deregister "'+image_id+'" AMI with "'+ami_info['Name']+'" name:'
   deregister_ami_command = shlex.split('aws ec2 deregister-image --image-id '+image_id)
   output, error = subprocess.Popen(deregister_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
   print output

   # Se eliminan los snapshots asociados
   for device in ami_info['BlockDeviceMappings']:
      # Si el dispositivo se corresponde con un volumen EBS se procede a eliminar su snapshot asociado
      if 'Ebs' in device:
         snapshot_id = str(device['Ebs']['SnapshotId'])
         print '\nIt proceeds to delete "'+snapshot_id+'" associated snapshot:'
         delete_snapshot_command = shlex.split('aws ec2 delete-snapshot --snapshot-id '+snapshot_id)
         output, error = subprocess.Popen(delete_snapshot_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
         print output

#
# Programa principal
#

# Parseo de los argumentos de entrada
arguments = arguments_parser()

# Definicion de los parametros necesarios para la gestion de las AMIs
if arguments.time:
   actual_date = time.strftime('%Y_%m_%d-%H_%M')
else:
   actual_date = time.strftime('%Y_%m_%d')
filter_name = arguments.ami_name
ami_name = filter_name+'-'+actual_date

if (not arguments.ami_description) or (arguments.ami_description == 'TBD'):
   ami_description = '"'+arguments.ami_name+' AMI created by '+os.path.basename(sys.argv[0])+'"'
else:
   ami_description = '"'+arguments.ami_description+'"'

if (not arguments.instance_id) or (arguments.instance_id == 'TBD'):
   instance_id = str(requests.get(instance_id_metadata_url).text)
else:
   instance_id = arguments.instance_id

rotation_copies = arguments.rotation_copies

# Si la accion especificada es 'create' se ejecuta el siguiente bloque de codigo
if (arguments.command == 'create'):
   # Se comprueba si ya existe alguna AMI creada con nombre ami_name
   describe_ami_command = shlex.split('aws ec2 describe-images --owner self --filters Name=name,Values='+ami_name)
   output, error = subprocess.Popen(describe_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

   # Decodificacion de la respuesta JSON
   result = json.loads(output)

   # Si ya existe una AMI creada con nombre ami_name se procede a su eliminacion para poder crearla de nuevo
   if (result['Images']) and (result['Images'][0]['Name'] == ami_name):
      print '\nAlready exists an AMI with "'+ami_name+'" name. This AMI will be deleted before create the new one...'
      deregister_ami(result['Images'][0])

   print '\nCreation of "'+ami_name+'" AMI with',ami_description,'description from "'+instance_id+'" instance:'
   if arguments.reboot:
      create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description)
   else:
      create_ami_command = shlex.split('aws ec2 create-image --instance-id '+instance_id+' --name '+ami_name+' --description '+ami_description+' --no-reboot')
   output, error = subprocess.Popen(create_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
   print output

# Si la accion especificada es 'rotate' se ejecuta el siguiente bloque de codigo
if (arguments.command == 'rotate'):
   # Se obtiene la lista de AMIs registradas cuyo nombre comienza por filter_name
   describe_ami_command = shlex.split('aws ec2 describe-images --owner self --filters Name=name,Values='+filter_name+'-*')
   output, error = subprocess.Popen(describe_ami_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

   # Decodificacion de la respuesta JSON
   result = json.loads(output)

   # Ordenacion de la lista de AMIs por el atributo 'Name'
   sorted_images = sorted(result['Images'], key=itemgetter('Name'), reverse=True) 

   print '\nAMIs currently registered:\n'
   for ami in sorted_images:
      print '\t'+ami['Name']

   if (len(sorted_images) > rotation_copies):
      print '\nThere are',len(sorted_images) - rotation_copies,'AMIs to deregister...'
      for i in xrange(rotation_copies, len(sorted_images)):
         deregister_ami(sorted_images[i])
   else:
      print '\nThe number of registered AMIs with "'+filter_name+'-*" name is less or equal than the rotation copies number. No need to deregister any AMIs\n'
