from doodad.wrappers.easy_launch import sweep_function, save_doodad_config
import os
def example_function(doodad_config, variant):
    os.system("export PYTHONPATH=$PYTHONPATH:/home/code && export CUDA_VISIBLE_DEVICES=0 && python /home/code/scripts/gpt.py --seed {seed} --n_epochs 1".format(seed=variant['seed']))
    save_doodad_config(doodad_config)

if __name__ == "__main__":
    params_to_sweep = {
        'seed': [1, 2, 3],
        # 'y': [100],
    }
    default_params = {
    }
    for mode in [
        #'here_no_doodad',
        #'local',
        'azure',
    ]:
        sweep_function(
            example_function,
            params_to_sweep,
            default_params=default_params,
            log_path='test_easy_launch_{}'.format(mode),
            mode=mode,
            use_gpu=True,
        )
