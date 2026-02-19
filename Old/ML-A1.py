#CODE WAS ALTERED BASED OFF OF: https://github.com/anisaskri0/MARL-CybORG-PPO, NOT MY CODE
import inspect
import time
import os
import gymnasium as gym 

from statistics import mean, stdev
from typing import Any
# import CybORG.Agents.SimpleAgents.BlueAgents_C1 as BlueAgents_C1
from CybORG.Agents.SimpleAgents.BaseAgent import BaseAgent
import CybORG.Agents.SimpleAgents.BlueAgents_C1 as BlueAgents_C1
from rich import print
from datetime import datetime



from CybORG import CybORG, env
from CybORG.Agents import SleepAgent, EnterpriseGreenAgent, FiniteStateRedAgent
from CybORG.Simulator.Scenarios import EnterpriseScenarioGenerator
from CybORG.Agents.Wrappers import VisualiseRedExpansion, EnterpriseMAE

#from EnterpriseMAE_CC4 import EnterpriseMAE
from CybORG.Agents.Wrappers import EnterpriseMAE
import ray
from ray.rllib.env import MultiAgentEnv
from ray.rllib.algorithms.ppo import PPOConfig, PPO, PPOTorchPolicy
from ray.rllib.policy.policy import PolicySpec
from ray.tune import register_env

# \from action_mask_model_CC4 import TorchActionMaskModel
from ray.rllib.models import ModelCatalog

from typing import Dict, Tuple
import torch
import warnings
import psutil



warnings.filterwarnings("ignore", category=DeprecationWarning)


now = datetime.now()
current_time = now.strftime("%M:%S")
print("\n\nCurrent Time =", current_time,"\n\n")



def env_creator_CC4(env_config: dict): 
    sg = EnterpriseScenarioGenerator(blue_agent_class=BlueAgents_C1, green_agent_class=EnterpriseGreenAgent, red_agent_class=FiniteStateRedAgent, steps=128)
    cyborg = CybORG(scenario_generator=sg)
    cyborg = EnterpriseMAE(cyborg)
    return cyborg


# Creating AI Agents
NUM_AGENTS = 5 
POLICY_MAP = {f"blue_agent_{i}":f"Agent{i}" for i in range(NUM_AGENTS)}
def policy_mapper (agent_id, episode, worker, **kwargs): return agent_id


# Creating Environment 
register_env(name="CC4", env_creator=lambda config: env_creator_CC4(config))
environment = env_creator_CC4({})



# Print statements 
print("\n\nBlue Agent 1: ")
print("     Action labels: ", environment.get_action_space('blue_agent_1'))
print("     Observation space: ", environment.get_observation('blue_agent_1'))

print("CPU count", psutil.cpu_count())
print("     Observation space: ", environment.get_observation('blue_agent_1'))
print("\n\n Number of actions in action mask: ", len(environment.actions('blue_agent_1')))


# Training the agents
algo_config = (
    PPOConfig()
    .framework("torch")
    .debugging(logger_config={"logdir":"logs/train_marl", "type":"ray.tune.logger.JsonLogger"})
    .environment("CC4")
    .experimental(
        _disable_preprocessor_api=True,
    )
    .env_runners(
        batch_mode="complete_episodes",    
        rollout_fragment_length="auto",     #Default 100
        sample_timeout_s=240,               #Default 120.0
    )
    .training(
        minibatch_size=128,             # Number of samples used in its training 
        train_batch_size=128,           # Number of minibatches you want to execute per episode 
        gamma = 0.9,                    # Tendency to value future reward over immediate reward             
        lambda_ = 0.9, 
        lr = 0.04,                      # Degree to which the AI can deviate/adjust/correct its own parameters.              
        num_epochs=4,
        )
    .multi_agent(
        policies={
            ray_agent: PolicySpec(
                policy_class =PPOTorchPolicy,
                observation_space=environment.observation_space(ray_agent),
                action_space=environment.action_space(ray_agent),
                config={"entropy_coeff": 0.001},
            )
            for ray_agent in environment.agents
        },
        policy_mapping_fn=policy_mapper,
    )
)

model_dir = "models/train_marl"         # Where policy information is stored 
algo = algo_config.build()              # Builds the AI agents
algo.train()                            # Trains the AI agents
algo.save()                             # Saves the resuolts 


print(ray.cluster_resources())
print(ray.available_resources())

for i in range(2):              # Default iteration: 200
    iteration = i + 4           # For restore, adjust iter, overwise you will  overwrite old models, e.g.  i + 156
    train_info = algo.train()
    print("\nIteration:", i, train_info)
    model_dir_crt = os.path.join(model_dir, "iter_"+str(iteration))
    print("\nSaving model in:", model_dir_crt)
    algo.save(model_dir_crt)

algo.save(model_dir_crt)


print("\n\nyo")
then = datetime.now()
current_time = then.strftime("%M:%S")
print("\n\nCurrent Time =", current_time,"\n\n")

# Off policy: soft actor critic, DDPG, 
