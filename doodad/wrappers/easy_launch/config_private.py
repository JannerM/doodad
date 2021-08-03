import os

CODE_DIRS_TO_MOUNT = [
   # '/media/4tb/qcli/projects/attentive-mbrl',
]
NON_CODE_DIRS_TO_MOUNT = [
   dict(
      local_dir='/home/janner/mount/attentive-mbrl',
      mount_point='/home/attentive-mbrl',
   ),
]
REMOTE_DIRS_TO_MOUNT = [
    dict(
        local_dir='/doodad_tmp/',
        mount_point='/doodad_tmp/',
    ),
]
LOCAL_LOG_DIR = '/home/janner/mount/logs/doodad/'

# DEFAULT_AZURE_GPU_MODEL = 'nvidia-tesla-v100'
DEFAULT_AZURE_GPU_MODEL = 'nvidia-tesla-t4'
DEFAULT_AZURE_INSTANCE_TYPE = 'Standard_DS1_v2'
DEFAULT_AZURE_REGION = 'eastus'

DEFAULT_DOCKER = 'docker.io/jannerm/ambr:latest'

try:
    AZ_SUB_ID=os.environ['AZURE_SUBSCRIPTION_ID']
    AZ_CLIENT_ID=os.environ['AZURE_CLIENT_ID']
    AZ_TENANT_ID=os.environ['AZURE_TENANT_ID']
    AZ_SECRET=os.environ['AZURE_CLIENT_SECRET']
    AZ_CONTAINER=os.environ['AZURE_STORAGE_CONTAINER']
    AZ_CONN_STR=os.environ['AZURE_STORAGE_CONNECTION_STRING']
except:
    print('config.py: Azure environment variables not set')

try:
    from doodad.wrappers.easy_launch.config_private import *
except ImportError:
    print("""
    Consider copying config.py to config_private.py, i.e.

    cp doodad/wrappers/easy_launch/config.py doodad/wrappers/easy_launch/config_private.py
    """)
