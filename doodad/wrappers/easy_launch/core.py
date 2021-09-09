import sys
import time
import os.path as osp
import importlib

from doodad import mode as ddmode
from doodad.utils import REPO_DIR

import doodad
from doodad.wrappers.easy_launch import run_experiment, metadata
from doodad.wrappers.easy_launch.metadata import save_doodad_config
from doodad.wrappers.sweeper import DoodadSweeper
from doodad.wrappers.sweeper.hyper_sweep import Sweeper

def load_from_file(path):
    spec = importlib.util.spec_from_file_location('spec', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

CWD = osp.dirname(__file__)

def sweep_function(
        method_call,
        params,
        log_path,
        default_params={},
        use_cloudpickle=True,
        add_date_to_logname=False,
        mode='azure',
        use_gpu=False,
        num_gpu=1,
        name_runs_by_id=False,
        add_time_to_run_id='behind',
        start_run_id=0,
        config_path=osp.join(CWD, 'config.py'),
        docker_image=None,
        extra_launch_info=None,
        code_dirs_to_mount=None,
        non_code_dirs_to_mount=None,
        remote_mount_configs=None,
        azure_region=None,
        instance_type=None,
        gpu_model=None,
        resource_group=None,
        vm_name=None,
        vm_password=None,
        **mount_kwargs,
):
    """
    Usage:
    ```
    def function(doodad_config, variant):
        x = variant['x']
        y = variant['y']
        z = variant['z']
        with open(doodad_config.output_directory + '/function_output.txt', "w") as f:
            f.write('sum = {}'.format(x+y+z))

    params_to_sweep = {
        'x': [1, 4],
        'y': [3, 4],
    }
    default_params = {
        'z': 10,
    }
    sweep_function(
        function,
        params_to_sweep,
        default_params=default_params,
        log_path='my-experiment',
        mode='azure',
    )
    ```
    :param mode: Mode to run this in. Supported modes:
        - 'azure'
        - 'here_no_doodad'
        - 'local'
        - 'gcp' (untested)
    :param method_call: A function that takes in two parameters:
        doodad_config: metadata.DoodadConfig
        variant: dictionary
    :param params:
    :param log_path:
    :param name_runs_by_id: If true, then each run will be in its own
    ```
    sub-directory to create a structure of
        log_path/
            run0/
            run1/
            run2/
            ...
    ```
    otherwise, all the runs will be saved to `log_path/` directly. The way path
    collisions are handled depends on the mode.
    :param add_time_to_run_id: If true, append the time to the run id name
    :param start_run_id:
    :return: How many
    """

    print(f'[ doodad/core ] Config path: {config_path}')
    config = load_from_file(config_path)

    docker_image = docker_image or config.DEFAULT_DOCKER
    code_dirs_to_mount = code_dirs_to_mount or config.CODE_DIRS_TO_MOUNT
    non_code_dirs_to_mount = non_code_dirs_to_mount or config.NON_CODE_DIRS_TO_MOUNT
    remote_mount_configs = remote_mount_configs or config.REMOTE_DIRS_TO_MOUNT
    azure_region = azure_region or config.DEFAULT_AZURE_REGION
    instance_type = instance_type or config.DEFAULT_AZURE_INSTANCE_TYPE
    gpu_model = gpu_model or config.DEFAULT_AZURE_GPU_MODEL
    azure_resource_group = resource_group or config.DEFAULT_AZURE_RESOURCE_GROUP
    azure_vm_name = vm_name or config.DEFAULT_AZURE_VM_NAME
    azure_vm_password = vm_password or config.DEFAULT_AZURE_VM_PASSWORD

    print(f'[ doodad/core ] Docker image: {docker_image}')
    print(f'[ doodad/core ] GPU model: {gpu_model}')
    print(f'[ doodad/core ] Default region: {azure_region}')

    if extra_launch_info is None:
        extra_launch_info = {}
    if add_date_to_logname:
        datestamp = time.strftime("%y-%m-%d")
        log_path = '%s_%s' % (datestamp, log_path)
    target = osp.join(REPO_DIR, 'doodad/wrappers/easy_launch/run_experiment.py')
    sweeper, output_mount = create_sweeper_and_output_mount(
        mode,
        log_path,
        docker_image,
        code_dirs_to_mount=code_dirs_to_mount,
        non_code_dirs_to_mount=non_code_dirs_to_mount,
        remote_mount_configs=remote_mount_configs,
        config=config,
        use_gpu=use_gpu,
        azure_resource_group=azure_resource_group,
        azure_vm_name=azure_vm_name,
        azure_vm_password=azure_vm_password,
        **mount_kwargs,
    )
    git_infos = metadata.generate_git_infos(config.CODE_DIRS_TO_MOUNT)

    doodad_config = metadata.DoodadConfig(
        use_gpu=use_gpu,
        num_gpu=num_gpu,
        git_infos=git_infos,
        script_name=' '.join(sys.argv),
        output_directory=output_mount.mount_point,
        extra_launch_info=extra_launch_info,
    )

    def _create_final_log_path(base_path, run_id):
        if name_runs_by_id:
            if add_time_to_run_id == 'in_front':
                timestamp = time.strftime("%Hh-%Mm-%Ss")
                path_suffix = '/{}_run{}'.format(timestamp, start_run_id + run_id)
            elif add_time_to_run_id == 'behind':
                timestamp = time.strftime("%Hh-%Mm-%Ss")
                path_suffix = '/run{}_{}'.format(start_run_id + run_id, timestamp)
            else:
                path_suffix = '/run{}'.format(start_run_id + run_id)
        else:
            path_suffix = ''
        return base_path + path_suffix

    if mode == 'here_no_doodad':
        return _run_method_here_no_doodad(
            method_call,
            config,
            doodad_config,
            params,
            default_params,
            log_path,
            _create_final_log_path,
        )

    def postprocess_config_and_run_mode(config, run_mode, config_idx):
        new_log_path = _create_final_log_path(log_path, config_idx)
        args = {
            'method_call': method_call,
            'output_dir': output_mount.mount_point,
            'doodad_config': doodad_config,
            'variant': config,
            'mode': mode,
        }
        if isinstance(run_mode, ddmode.AzureMode):
            run_mode.log_path = new_log_path
        if isinstance(run_mode, ddmode.GCPMode):
            run_mode.gcp_log_path = new_log_path
        if isinstance(run_mode, ddmode.LocalMode):
            args['output_dir'] = _create_final_log_path(
                args['output_dir'], config_idx
            )
        args_encoded, cp_version = run_experiment.encode_args(args, cloudpickle=use_cloudpickle)
        new_config = {
            run_experiment.ARGS_DATA: args_encoded,
            run_experiment.USE_CLOUDPICKLE: str(int(use_cloudpickle)),
            run_experiment.CLOUDPICKLE_VERSION :cp_version,
        }
        return new_config, run_mode

    def _run_sweep():
        if mode == 'azure':
            sweeper.run_sweep_azure(
                target,
                params,
                default_params=default_params,
                log_path=log_path,
                add_date_to_logname=False,
                postprocess_config_and_run_mode=postprocess_config_and_run_mode,
                instance_type=instance_type,
                gpu_model=gpu_model,
                use_gpu=use_gpu,
                num_gpu=num_gpu,
                region=azure_region,
                is_docker_interactive=False,
                **mount_kwargs,
            )
        elif mode == 'gcp':
            sweeper.run_sweep_gcp(
                target,
                params,
                default_params=default_params,
                log_prefix=log_path,
                add_date_to_logname=False,
                postprocess_config_and_run_mode=postprocess_config_and_run_mode,
                num_gpu=num_gpu,
                use_gpu=use_gpu,
                is_docker_interactive=False,
            )
        elif mode == 'local':
            sweeper.run_sweep_local(
                target,
                params,
                default_params=default_params,
                postprocess_config_and_run_mode=postprocess_config_and_run_mode,
                is_docker_interactive=True,
            )
        else:
            raise ValueError('Unknown mode: {}'.format(mode))

    _run_sweep()


def _run_method_here_no_doodad(
        method_call, config, doodad_config, params, default_params, log_path,
        create_final_log_path
):
    sweeper = Sweeper(params, default_params)
    for xid, param in enumerate(sweeper):
        new_log_path = create_final_log_path(log_path, xid)
        doodad_config = doodad_config._replace(
            output_directory=osp.join(config.LOCAL_LOG_DIR, new_log_path),
        )
        save_doodad_config(doodad_config)
        method_call(doodad_config, param)


def create_mounts(
        code_dirs_to_mount,
        non_code_dirs_to_mount,
        remote_mount_configs,
        config,
        **mount_kwargs,
):
    non_code_mounts = [
        doodad.MountLocal(**non_code_mapping, **mount_kwargs)
        for non_code_mapping in non_code_dirs_to_mount
    ] + [
        doodad.MountRemote(**non_code_mapping)
        for non_code_mapping in remote_mount_configs
    ]
    if REPO_DIR not in config.CODE_DIRS_TO_MOUNT:
        config.CODE_DIRS_TO_MOUNT.append(REPO_DIR)
    code_mounts = [
        doodad.MountLocal(local_dir=code_dir, pythonpath=True, **mount_kwargs)
        for code_dir in code_dirs_to_mount
    ]
    mounts = code_mounts + non_code_mounts
    return mounts


def create_sweeper_and_output_mount(
        mode,
        log_path,
        docker_image,
        code_dirs_to_mount,
        non_code_dirs_to_mount,
        remote_mount_configs,
        config,
        use_gpu=False,
        azure_vm_name=None,
        azure_resource_group=None,
        azure_vm_password=None,
        **mount_kwargs,
):
    mounts = create_mounts(
        code_dirs_to_mount=code_dirs_to_mount,
        non_code_dirs_to_mount=non_code_dirs_to_mount,
        remote_mount_configs=remote_mount_configs,
        config=config,
        **mount_kwargs,
    )
    az_mount = doodad.MountAzure(
        '',
        mount_point='/output',
    )
    sweeper = DoodadSweeper(
        mounts=mounts,
        docker_img=docker_image,
        azure_subscription_id=config.AZ_SUB_ID,
        azure_storage_connection_str=config.AZ_CONN_STR,
        azure_client_id=config.AZ_CLIENT_ID,
        azure_authentication_key=config.AZ_SECRET,
        azure_tenant_id=config.AZ_TENANT_ID,
        azure_storage_container=config.AZ_CONTAINER,
        mount_out_azure=az_mount,
        local_output_dir=osp.join(config.LOCAL_LOG_DIR, log_path),  # TODO: how to make this vary in local mode?
        local_use_gpu=use_gpu,
        azure_resource_group=azure_resource_group,
        azure_vm_name=azure_vm_name,
        azure_vm_password=azure_vm_password,
        **mount_kwargs,
    )
    # TODO: the sweeper should probably only have one output mount that is
    # set rather than read based on the mode
    if mode == 'azure':
        output_mount = sweeper.mount_out_azure
    elif mode == 'gcp':
        output_mount = sweeper.mount_out_gcp
    elif mode == 'here_no_doodad':
        output_mount = sweeper.mount_out_local  # this will be ignored
    elif mode == 'local':
        output_mount = sweeper.mount_out_local
    else:
        raise ValueError('Unknown mode: {}'.format(mode))
    return sweeper, output_mount
