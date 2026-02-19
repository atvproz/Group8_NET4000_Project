from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import RemoteController, OVSSwitch
from mininet.log import setLogLevel
from mininet.cli import CLI
import time
import numpy as np
import gym
from gym.spaces import Box
from stable_baselines3 import DDPG
from stable_baselines3.common.noise import NormalActionNoise
from collections import deque

class BWPathEnv(gym.Env):
    def __init__(self, net):
        super().__init__()
        self.net = net
        self.links = list(net.links)
        self.switch_order = ['s1', 's2', 's3', 's4', 's5']
        self.switch_idx = {s: i for i, s in enumerate(self.switch_order)}
        
        # State: 10 link BWs + 5 switch position = 15 dims
        self.observation_space = Box(low=0, high=1, shape=(15,))
        # Action: weights for max 4 outgoing links
        self.action_space = Box(low=-1, high=1, shape=(4,))
        
        self.current_switch = 's3'  # Start at h1's switch
        self.episode_steps = 0
        self.max_steps = 10

    def reset(self):
        self.current_switch = 's3'
        self.episode_steps = 0
        self._randomize_bandwidths()
        return self._get_observation()

    def _randomize_bandwidths(self):
        """Randomize link BWs between 10-100 Mbps"""
        for link in self.links:
            bw = np.random.uniform(10, 100)
            link.intf1.tc(bw=bw)

    def _get_observation(self):
        # Normalize BWs (10-100 → 0-1)
        bws = np.array([min(link.intf1.bw / 100.0, 1.0) for link in self.links])
        # One-hot current switch position
        pos = np.zeros(5)
        pos[self.switch_idx[self.current_switch]] = 1.0
        return np.concatenate([bws[:10], pos])  # Use first 10 links

    def _get_neighbors(self, switch_name):
        """Get neighboring switches"""
        sw = self.net.get(switch_name)
        neighbors = [link.intf2.node.name for link in sw.links if 's' in link.intf2.node.name]
        return neighbors

    def step(self, action):
        neighbors = self._get_neighbors(self.current_switch)
        if not neighbors:
            return self._get_observation(), -100, True, {}
        
        # Softmax action → next hop probabilities
        action_probs = np.softmax(action[:len(neighbors)])
        next_switch = neighbors[np.argmax(action_probs)]
        self.current_switch = next_switch
        
        self.episode_steps += 1
        
        # Reward: BW of traversed path + reach destination
        path_reward = sum(link.intf1.bw for link in self.links if link.intf1.node.name == self.current_switch)[-1]
        congestion_penalty = sum(1 for link in self.links if link.intf1.bw < 20) * 5
        
        if self.current_switch == 's2':  # Reached h2's switch
            reward = 100 - congestion_penalty
            done = True
        else:
            reward = path_reward / 100.0 - congestion_penalty
            done = self.episode_steps >= self.max_steps
        
        return self._get_observation(), reward, done, {}

def install_ddp_flows(net, model, current_switch='s3'):
    """Install DDPG-optimal flows from current switch"""
    env = BWPathEnv(net)
    obs = env.reset()
    
    path = [current_switch]
    for _ in range(10):  # Max path length
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _ = env.step(action)
        neighbors = env._get_neighbors(path[-1])
        next_hop = neighbors[np.argmax(np.softmax(action[:len(neighbors)]))]
        path.append(next_hop)
        if done or next_hop == 's2':
            break
    
    print(f"DDPG Path: {' -> '.join(path)}")
    
    # Install flows along optimal path (simplified)
    for i in range(len(path)-1):
        src_sw = net.get(path[i])
        dst_port = None
        for intf in src_sw.intfs.values():
            if intf.link.intf2.node.name == path[i+1]:
                dst_port = intf.name
                break
        if dst_port:
            src_sw.cmd(f'ovs-ofctl add-flow {src_sw.name} in_port=*,actions=output:{dst_port}')

def main():
    setLogLevel('info')
    topo = CustomTopo()
    c0 = RemoteController('c0', ip='127.0.0.1', port=6633)
    
    net = Mininet(
        topo=topo, link=TCLink, controller=c0, switch=OVSSwitch,
        autoSetMacs=True, autoStaticArp=False
    )
    
    print("\nStarting Network...")
    net.start()
    
    # DISABLE STP for DDPG control
    print("\nDisabling STP...")
    for switch in net.switches:
        switch.cmd(f'ovs-vsctl set Bridge {switch.name} stp_enable=false')
    
    print("\nTraining DDPG agent...")
    env = BWPathEnv(net)
    n_actions = env.action_space.shape[-1]
    action_noise = NormalActionNoise(
        mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions)
    )
    
    model = DDPG(
        'MlpPolicy', env, action_noise=action_noise,
        learning_rate=1e-3, buffer_size=10000, verbose=1
    )
    model.learn(total_timesteps=5000)  # Quick training
    model.save('ddpg_mininet_path')
    
    print("\nInstalling DDPG flows...")
    install_ddp_flows(net, model)
    
    print("\nTesting connectivity...")
    net.pingAll()
    
    print("\nDDPG-optimized network ready. Run iperf h1 h2 for throughput tests.")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    main()
