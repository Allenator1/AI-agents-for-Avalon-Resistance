from math import sqrt, log
import random

'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and playouts
'''
class Node:
    def __init__(self, state, parent=None, player=-1, team=None):
        self.parent = parent    # None if root state
        self.reward = 0         # MCTS reward during backpropagation
        self.visits = 0         # MCTS visits during backpropagation
        self.avails = 0         # Number of times parent has been visited during backpropagation
        self.player = player    # Player id; None if environmental state
        self.team = team        # SPY or NON-SPY; None if environmental state
        self.state = state      # Gamestate that the node represents
        self.child_nodes = []


    def ucb_selection(self, possible_actions, exploration):
        legal_children = filter(lambda c: c.action in possible_actions, self.child_nodes)
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(self.avails) / self.visits)
        
        for child in legal_children:
            child.avails += 1

        return max(legal_children, ucb_eq)


    def append_child(self, state, player):
        child_node = Node(state=state, parent=self, player=player)
        self.child_nodes.append(child_node)
        return child_node

    
    def backpropagate(self, terminal_state):
        self.reward += terminal_state.winner == self.team
        self.visits += 1


    def unexplored_actions(self, possible_actions):
        tried_actions = [child.action for child in self.child_nodes]
        return filter(lambda m: m not in tried_actions, possible_actions)


def rollout(state):
    while state.get_actions != []:
        state.make_move(random.choice(state.get_actions()))
    return state
        


    