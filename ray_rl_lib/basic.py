import sys
import os
import diambra.arena
from make_ray_env import DiambraArena, preprocess_ray_config
from ray.rllib.algorithms.ppo import PPO

if __name__ == "__main__":

    # Settings
    settings = {}
    settings["hardcore"] = True
    settings["frame_shape"] = [84, 84, 1]

    config = {
        # Define and configure the environment
        "env": DiambraArena,
        "env_config": {
            "game_id": "doapp",
            "settings": settings,
        },
        "num_workers": 0,
    }

    # Update config file
    config = preprocess_ray_config(config)

    # Create the RLlib Agent.
    agent = PPO(config=config)

    # Run it for n training iterations
    print("\nStarting training ...\n")
    for idx in range(1):
        print("Training iteration:", idx + 1)
        results = agent.train()
    print("\n .. training completed.")
    print("Training results: {}".format(results))

    # Run the trained agent (and render each timestep output).
    print("\nStarting trained agent execution ...\n")

    env = diambra.arena.make("doapp", settings)

    obs = env.reset()
    while True:
        env.render()

        action = agent.compute_action(obs)

        obs, reward, done, info = env.step(action)

        if done:
            obs = env.reset()
            break

    print("\n... trained agent execution completed.\n")

    env.close()