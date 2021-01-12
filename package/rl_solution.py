import numpy as np
import sys
from rl_glue import RLGlue
from Agent import BaseAgent 
from Environment import BaseEnvironment  
from manager import Manager
# from itertools import product
# from tqdm import tqdm
# import numpy as np

class SmartAgent(BaseAgent):

    def agent_init(self, agent_info={}, default_conf=None):
        '''
            Think about using net profit as a second classifier for state,
            so that our algorithm could act better based on how much money it's ahead of/behind others
        '''
        self.randGenerator = np.random.RandomState()
        self.epsilon = agent_info["epsilon"] ## variable for epsilon greedy choice
        self.rounds = agent_info["num_rounds"] ## number of rounds, for identifying this episode
        self.states = np.arange(self.rounds) ## COULD exist a 2nd index in tuple: The profit classifier (if we make max profit or not)
        self.visited_sa_pair = [] ## State action pair that we have visited each episode
        self.discount_factor = agent_info["discount"]
        self.config = default_conf
        self.curr_state = 0
        # self.score = agent_info["starting_money"] ## detect plateaus?
        self.num_actions = 5 # copycat and maximize(1. allocation 2. distance away from stores)
        ## attractiveness allocation
        # self.size_counter = np.zeroes((self.rounds, self.actions))
        self.q = agent_info["q_values"]
        
    def flatten_state(self, tup):
        '''
            Helper Function
        '''
        return tup[0] * 2 + tup[1]

    def agent_start(self, state):
        action = None
        if self.randGenerator.rand() < self.epsilon:
            '''
                Explore actions
            '''
            action = self.randGenerator.randint(self.num_actions)
        else:
            action = self.argmax(self.q[state, :])

        self.visited_sa_pair.append((state, action))
        return action

    def agent_step(self, state):
        '''
            Like above, we simply choose the action here.
        '''
        action = None
        self.curr_state = state
        if self.randGenerator.rand() < self.epsilon:
            '''
                Explore actions
            '''
            action = self.randGenerator.randint(self.num_actions)
        else:
            action = self.argmax(self.q[state, :])

        self.visited_sa_pair.append((state, action))
        return action

    def agent_end(self, reward):
        '''
            Apply the reward only at the end of a game.
            We can also consider applying reward at every step, 
            but that would require state to become a tuple of (a,b)
            where a is from 0 to self.episodes while b states 
            your net-profit (which can be positive or negative) 
        '''
        print("Before: %s" % self.q)
        print(self.visited_sa_pair)
        for i, pair in enumerate(self.visited_sa_pair):
            state, action = pair
            if action == 0 and i < 3:
                continue
            
            self.q[state, action] += reward
        
        if reward == -1:
            self.discount_factor = min(1, self.discount_factor * 1.02) ## Encourage more spending
        print("After: %s" % self.q)
    def agent_reset(self, discount_factor=None, epsilon=None):
        '''
            Use this chance to reassign values.
            Reassign discount factor
        '''        
        self.visited_sa_pair = []
        
    def agent_message(self, message):
        raise NotImplementedError

    def argmax(self, q_values):
        """argmax with random tie-breaking
        Args:
            q_values (Numpy array): the array of action-values
        Returns:
            action (int): an action with the highest value
        """
        top = float("-inf")
        ties = []

        for i in range(len(q_values)):
            if q_values[i] > top:
                top = q_values[i]
                ties = []

            if q_values[i] == top:
                ties.append(i)

        return self.randGenerator.choice(ties)