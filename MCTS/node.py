from math import sqrt, log
import random
from MCTS.state import Gamestates

'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and playouts.
'''
class Node:
    def __init__(self, player, parent=None, action=None):
        self.parent = parent    # None if root state
        self.action = action    # Action that parent took to lead to this node. None if root state.
        self.player = player    # Player id
        self.reward = 0         # MCTS reward during backpropagation
        self.visits = 0         # MCTS visits during backpropagation
        self.avails = 0         # Number of times parent has been visited during backpropagation
        self.child_nodes = {}
           

    def ucb_selection(self, possible_actions, exploration):
        legal_children = filter(lambda c: c.action in possible_actions, self.child_nodes)
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(c.avails) / c.visits)
        
        for child in legal_children:
            child.avails += 1

        node = max(legal_children, key=ucb_eq)

        return (node, node.action)

    
    def expand(self, next_player, possible_actions):
        unexplored_actions = self.unexplored_actions(possible_actions)
        if unexplored_actions != []:
            action = random.choice(unexplored_actions)
            node = self.append_child(next_player, action)
            return (node, action)


    def append_child(self, next_player, action):
        child_node = Node(player=next_player, parent=self, action=action)
        self.child_nodes[action] = child_node
        return (child_node, action)

    
    def backpropagate(self, terminal_state, child_node):
        self.reward += terminal_state.get_result(self.player)
        self.visits += 1


    def unexplored_actions(self, possible_actions):
        explored_actions = list(self.child_nodes.keys())
        return filter(lambda a: a not in explored_actions, possible_actions)


'''
A class used to define nodes in the Monte Carlo tree, where the game state
contains simultaneous actions. Uses Decoupled UCT Selection (DUCT) to choose a
child node during the selection phase.
'''
class ActionMatrix(Node):
    def __init__(self, player, parent, action):
        self.parent = parent
        self.action = action
        self.player = -1
        self.player_actions = {}
        self.child_nodes = {}

    
    def ucb_selection(self, possible_actions, exploration):
        legal_actions = filter(lambda a: a.action in possible_actions, self.player_actions.values())
        joint_action = [None] * len(self.player_actions)
        for p in self.player_actions:
            actions = self.player_actions[p]
            ucb_eq = lambda a: a.reward / a.visits + exploration * sqrt(log(a.avails) / a.visits)
            
            for action in legal_actions:
                action.avails += 1

            selected_action = max(actions, key=ucb_eq)
            joint_action.append((p, selected_action))
            node = self.child_nodes[joint_action]
        return node, joint_action

    
    def append_child(self, next_player, joint_action):
        for p, action in enumerate(joint_action['action']):
            if p not in self.player_actions:
                self.player_actions[p] = []
            self.player_actions[p].append(ActionNode(parent=self, player=p, action=action))

        child_node = Node(player=next_player, parent=self, action=joint_action)
        self.child_nodes[joint_action] = child_node
        return (child_node, joint_action)

    
    def backpropagate(self, terminal_state, child_node):
        joint_action = child_node.action
        for p, _ in enumerate(joint_action['action']):
            action_node = self.player_actions[p]
            action_node.reward += terminal_state.get_result(p)
            action_node.visits += 1
    

class ActionNode():
    def __init__(self, parent, player, action):
        self.parent = parent
        self.action = action                # Action made by a single player. True or False (for voting and sabotaging)
        self.player = player 
        self.reward = 0
        self.visits = 0
        self.avails = 0

    def backpropagate(self, terminal_state):
        self.reward += terminal_state.winner == self.team
        self.visits += 1


def playout(state):
    while state.get_moves() != []:
        state.make_move(random.choice(state.get_moves()))
    return state
        


    