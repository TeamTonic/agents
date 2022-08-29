import sys
import os
import time
import yaml
import json
import argparse
base_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_path, '../'))
from make_stable_baselines_env import make_stable_baselines_env
from wrappers.tektag_rew_wrap import TektagRoundEndChar2Penalty, TektagHealthBarUnbalancePenalty

from stable_baselines import PPO2

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--cfgFile', type=str, required=True, help='Training configuration file')
    opt = parser.parse_args()
    print(opt)

    # Read the cfg file
    yaml_file = open(opt.cfgFile)
    params = yaml.load(yaml_file, Loader=yaml.FullLoader)
    print("Config parameters = ", json.dumps(params, sort_keys=True, indent=4))
    yaml_file.close()

    time_dep_seed = int((time.time() - int(time.time() - 0.5)) * 1000)

    model_folder = os.path.join(base_path, "games_specific_files", params["settings"]["game_id"], params["folders"]["model"])

    # Settings
    settings = params["settings"]

    # Wrappers Settings
    wrappers_settings = params["wrappers_settings"]

    # Additional obs key list
    key_to_add = params["key_to_add"]

    env, num_env = make_stable_baselines_env(time_dep_seed, settings, wrappers_settings,
                                            key_to_add=key_to_add, no_vec=True)

    # Load the trained agent
    model_checkpoint = params["ppo_settings"]["model_checkpoint"]
    model = PPO2.load(os.path.join(model_folder, model_checkpoint))

    obs = env.reset()

    while True:

        action, _ = model.predict(obs, deterministic=True)

        obs, reward, done, info = env.step(action)

        if done:
            obs = env.reset()

    # Close the environment
    env.close()