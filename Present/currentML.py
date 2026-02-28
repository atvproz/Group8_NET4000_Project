import numpy as np
import random
from collections import defaultdict

def get_delay(h1):
    """Run ping, return delay in ms as float"""
    result = h1.cmd('ping -c 3 -W 1 10.0.0.2')
    for line in result.split('\n'):
        if 'avg' in line:
            try:
                return float(line.split('/')[4])
            except:
                pass
    return 50.0

class SimpleQLearning:
    def __init__(self, net):
        self.net           = net
        self.switches      = ['s1', 's2', 's3', 's4', 's5']
        self.qtable        = defaultdict(float)
        self.learning_rate = 0.1
        self.discount      = 0.9
        self.epsilon       = 0.3

    def get_neighbors(self, switch_name):
        try:
            sw        = self.net.get(switch_name)
            neighbors = []
            for intf in sw.intfs.values():
                if hasattr(intf, 'link') and intf.link:
                    other = intf.link.intf1 if intf.link.intf2 == intf else intf.link.intf2
                    node  = other.node.name
                    if node.startswith('s'):
                        neighbors.append(node)
            return list(set(neighbors))
        except:
            return []

    def get_state(self, current_switch):
        return current_switch

    def choose_action(self, state, neighbors):
        if random.random() < self.epsilon or not neighbors:
            return random.choice(neighbors) if neighbors else None
        q_values    = [self.qtable[(state, n)] for n in neighbors]
        max_q       = max(q_values)
        best        = [n for n, q in zip(neighbors, q_values) if q == max_q]
        return random.choice(best)

    def update_q(self, state, action, reward, next_state):
        old_q      = self.qtable[(state, action)]
        neighbors  = self.get_neighbors(next_state)
        max_next_q = max([self.qtable[(next_state, n)] for n in neighbors], default=0)
        self.qtable[(state, action)] = (
            old_q + self.learning_rate * (reward + self.discount * max_next_q - old_q)
        )


def train_ddpg_model(net):
    print("Training Q-Learning Agent...")
    agent       = SimpleQLearning(net)
    h1          = net.get('h1')
    num_episodes = 200 #increased the number of episodes for better learning

    for episode in range(num_episodes):
        current      = 's3'
        target       = 's2'
        path         = [current]
        total_reward = 0

        for step in range(10):
            state     = agent.get_state(current)
            neighbors = agent.get_neighbors(current)
            if not neighbors:
                break

            action = agent.choose_action(state, neighbors)
            if not action:
                break

            done = (action == target)

            #New section for less loss
            delay  = get_delay(h1)
            reward = -delay * 0.5 #increase delay
            reward += -1
            reward += 100 if done else 0


            next_state = agent.get_state(action)
            agent.update_q(state, action, reward, next_state)

            total_reward += reward
            path.append(action)
            current = action

            if done:
                break

        agent.epsilon = max(0.05, agent.epsilon * 0.995)

        if (episode + 1) % 20 == 0:
            print(f"Episode {episode+1}/{num_episodes} | "
                  f"Reward={total_reward:.2f} | "
                  f"ε={agent.epsilon:.3f} | "
                  f"Path={'->'.join(path)}")

    print("Training complete!")
    return agent, None


def test_ddpg_model(model, env):
    print("\nTesting trained model:")
    model.epsilon = 0.0 #Eliminate randomness for testing
    
    current = 's3'
    target  = 's2'
    path    = [current]

    for step in range(10):
        neighbors = model.get_neighbors(current)
        if not neighbors:
            break
        state    = model.get_state(current)
        q_values = [model.qtable[(state, n)] for n in neighbors]
        best     = neighbors[np.argmax(q_values)]
        path.append(best)
        print(f"  Step {step+1}: {path[-2]} -> {path[-1]}  Q={max(q_values):.2f}")
        current = best
        if current == target:
            print("  Reached target!")
            break

    print(f"  Final path: {'->'.join(path)}")
