import numpy as np
import random

class SimpleQLearning:
    def __init__(self, net):
        self.net = net
        self.links = list(net.links)
        self.switches = ['s1', 's2', 's3', 's4', 's5']
        self.q_table = {}  # State-action Q-values
        self.learning_rate = 0.1                    # Learning rate is the degree to which the AI can deviate/adjust/correct its own parameters. 
        self.discount = 0.9                         # Discount factor is the tendency to value future reward over immediate reward.
        self.epsilon = 0.3                          # Epsilon is the chance that the agent will explore a new action and its associated reward.
        
    def get_neighbors(self, switch_name):
        """Get neighboring switches"""
        try:
            sw = self.net.get(switch_name)
            neighbors = []

            # Iterate through the interfaces of a switch to find its connected neighbors
            for intf in sw.intfs.values():
                if hasattr(intf, 'link') and intf.link:
                    other_intf = intf.link.intf1 if intf.link.intf2 == intf else intf.link.intf2
                    other_node = other_intf.node.name
                    if other_node.startswith('s'):
                        neighbors.append(other_node)
            return list(set(neighbors))
        except:
            return []
    
    def get_state(self, current_switch):
        """Simple state representation"""
        return current_switch
    
    def choose_action(self, state, neighbors):
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon or not neighbors:             
            return random.choice(neighbors) if neighbors else None
                    
        q_values = [self.q_table.get((state, n), 0) for n in neighbors]         # Obtains the rewards for all the neighbors (that' stored in the Q-table).
        
        max_q = max(q_values)                                                   # Obtains the maximum value among the neighboring switches. 
        best_actions = [n for n, q in zip(neighbors, q_values) if q == max_q]   # Create a list of tie-breakers
        return random.choice(best_actions)                                      # Randomly select among the best actions to break ties.      
    

    
    def update_q(self, state, action, reward, next_state):
        """Update Q-value"""
        old_q = self.q_table.get((state, action), 0)
        neighbors = self.get_neighbors(next_state)
        if neighbors:
            max_next_q = max([self.q_table.get((next_state, n), 0) for n in neighbors])
        else:
            max_next_q = 0
        
        new_q = old_q + self.learning_rate * (reward + self.discount * max_next_q - old_q)
        self.q_table[(state, action)] = new_q

def train_ddpg_model(net):
    """Train Q-learning model"""
    print("\n=== Training Q-Learning Agent ===")
    agent = SimpleQLearning(net)
    
    num_episodes = 100
    for episode in range(num_episodes):
        current = 's3'  # Start at h1's switch
        target = 's2'   # h2's switch
        path = [current]
        total_reward = 0
        
        for step in range(10):
            state = agent.get_state(current)                    
            neighbors = agent.get_neighbors(current)            # Obtains the neighbors of the current switch. 
            
            if not neighbors:                                   # If there are no neighbors, it means the agent is stuck and cannot move, so we break out of the loop.
                break
                
            action = agent.choose_action(state, neighbors)     
            if not action:      
                break
            
            # Reward: positive for getting closer to target
            if action == target:
                reward = 100
                done = True
            else:
                reward = -1
                done = False
            
            total_reward += reward                              # Accumulate total reward for the episode
            next_state = agent.get_state(action)                # Gets the next set of actions ready for the next episode 
            agent.update_q(state, action, reward, next_state)   # Updates the Q-table based on the action taken and the reward received
            
            path.append(action)                                 # Add the chosen action to the path
            current = action
            
            if done: 
                break
        
        if (episode + 1) % 20 == 0:
            # Print episode summary every 20 episodes
            print(f"Episode {episode + 1}/{num_episodes}, Reward: {total_reward:.2f}, Path: {' -> '.join(path)}")
    
    print("Training complete!")
    return agent, None

def test_ddpg_model(model, env):
    """Test the trained Q-learning model"""
    print("\n=== Testing trained model ===")
    
    current = 's3'          # Starting switch 
    target = 's2'           # Destination switch
    path = [current]
    
    for step in range(10):
        neighbors = model.get_neighbors(current)
        if not neighbors:
            break
        
        # Choose best action (greedy)
        state = model.get_state(current)
        q_values = [model.q_table.get((state, n), 0) for n in neighbors]
        best_neighbor = neighbors[np.argmax(q_values)]
        
        path.append(best_neighbor)
        current = best_neighbor
        
        print(f"Step {step + 1}: {path[-2]} -> {path[-1]}, Q-value: {max(q_values):.2f}")
        
        if current == target:
            print("Reached target!")
            break
    
    print(f"\nOptimal path: {' -> '.join(path)}")