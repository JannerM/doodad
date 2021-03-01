"""
Instructions:
1) Set up testing/config.py (copy from config.py.example and fill in the fields)
2) Run this script
3) Look inside your AZ_CONTAINER and you should see results in test_azure_with_mounts/azure_script_output/output.out
"""
import doodad
from doodad.utils import TESTING_DIR
from doodad.easy_launch.config_private import AZ_SUB_ID, AZ_CLIENT_ID, AZ_TENANT_ID, AZ_SECRET, AZ_CONN_STR, AZ_CONTAINER


def run():
    launcher = doodad.AzureMode(
         azure_subscription_id=AZ_SUB_ID,
         azure_storage_connection_str=AZ_CONN_STR,
         azure_client_id=AZ_CLIENT_ID,
         azure_authentication_key=AZ_SECRET,
         azure_tenant_id=AZ_TENANT_ID,
         azure_storage_container=AZ_CONTAINER,
         log_path='test_azure_with_mounts',
         region='eastus',
         instance_type='Standard_DS1_v2',
    )
    az_mount = doodad.MountAzure(
        'azure_script_output',
        mount_point='/output',
    )
    local_mount = doodad.MountLocal(
        local_dir=TESTING_DIR,
        mount_point='/data',
        output=False
    )
    code_mount1 = doodad.MountLocal(
        local_dir='/home/user/code/CQL/d4rl',
        mount_point='/code/cql', pythonpath=True)
    code_mount2 = doodad.MountLocal(
        local_dir='/home/user/code/d4rl',
        mount_point='/code/d4rl', pythonpath=True)
    code_mount3 = doodad.MountLocal(
        local_dir='/home/user/code/doodad',
        mount_point='/code/doodad', pythonpath=True)
    mounts = [local_mount, az_mount, code_mount1, code_mount2, code_mount3]
    doodad.run_command(
        command='python -u /code/cql/examples/cql_pytest.py > /output/output.out 2> /output/output.err',
        mode=launcher,
        mounts=mounts,
        verbose=True,
        docker_image="anair17/railrl-dice-v1",
    )
if __name__ == '__main__':
    run()