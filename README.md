If your viewing this in Visual Studio Code, press Ctrl + Shift + V, to view file in the intended Markdown format. <br><br>

# Project 5: Delay-Predictive Routing for Emulated Non-Terrestial Networks
Contributors: Spencer Craig, Alexandre Picard, Cameron Wellman, Justin Le<br>
Space is an unpredictable environment, causing fluctations in latency for Low Earth Orbit (LEO) satellites. Our project emulates LEO satellites, and aims to predict the best path by integrating machine-learning.<br>

The chosen machine-learning algorithm is DDPG or *Deep Deterministic Policy Gradient*. Reason why we chose DDPG ... blah blah ...<br>


**Other notes:**
- Code language: Python 
- By default, 
    - The machine learning algorithm executes 100 iterations. 
    - The starting satellite is S2. 
    - The destination satellite is S3. 
- Requires Linux Ubuntu and Mininet.
<br><br>

**Simulated Topology** <br>
![Topology](NET4000%20_Topology_A1.png)



# How to run the code
<br>

# Dictionary 


### Learning rate 
`self.learning_rate=0.1`

0 > x > 1<br>
Learning rate is the degree to which the AI can deviate/adjust/correct its own parameters. <br>
- High score = overcorrection <br>
- Low score = little variance in action <br>
Best to start high, then go lower. <br>
Source: [Reddit - Learning Rate](https://www.reddit.com/r/MLQuestions/comments/h7z4o8/what_is_the_best_learning_rate_why/)<br><br><br>


### Discount 
`self.discount = 0.9`

0 > x > 1 <br>
The tendency to choose long-term rewards. <br>
- Lower score will make agent learn actions that produce an immediate reward.<br>
- Higher score will make agent evaluate each of its action based on the sum total of all its future rewards. <br>

Source: [Stack Exchange - Discount factor in reinforcement learning](https://stats.stackexchange.com/questions/221402/understanding-the-role-of-the-discount-factor-in-reinforcement-learning) <br>
Source: [Medium.com - Discount factor](https://medium.com/@bhavya_kaushik_/the-discount-factor-c9fb4984085e) <br><br><br>

### Epsilon 
`self.epsilon=0.1`<br>
`random.random() < self.epsilon `

0 > x > 1 <br>
The chance that the agent will explore a new action and its associated reward. <br>
In this case: <br>
- the exploration is 10%. <br>
- the chance to pick an already-known action is 90%. <br>

Source: [GeeksForGeeks.com - Epilson](https://www.geeksforgeeks.org/machine-learning/epsilon-greedy-algorithm-in-reinforcement-learning/) <br>
Look under "Exploration vs Exploitation" section. 