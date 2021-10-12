from math import sqrt, log
import random
from MCTS.state import Gamestates

'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and playouts
'''
class Node:
    def __init__(self, state, parent=None, action=None, player=-1, team=None):
        self.parent = parent    # None if root state
        self.action = action    # Action that parent took to lead to this node. None if root state.
        self.player = player    # Player id; -1 if environmental state
        self.reward = 0         # MCTS reward during backpropagation
        self.visits = 0         # MCTS visits during backpropagation
        self.avails = 0         # Number of times parent has been visited during backpropagation
        self.state = state      # Gamestate that the node represents
        self.child_nodes = []


    def ucb_selection(self, possible_actions, exploration):
        legal_children = filter(lambda c: c.action in possible_actions, self.child_nodes)
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(c.avails) / c.visits)
        
        for child in legal_children:
            child.avails += 1

        return max(legal_children, key=ucb_eq)


    def append_child(self, state, player):
        child_node = Node(state=state, parent=self, player=player)
        self.child_nodes.append(child_node)
        return child_node

    
    def backpropagate(self, terminal_state):
        self.reward += terminal_state.get_result(self.player)
        self.visits += 1


    def unexplored_actions(self, possible_actions):
        explored_actions = [child.action for child in self.child_nodes]
        return filter(lambda m: m not in explored_actions, possible_actions)


'''
A class used to define nodes in the Monte Carlo tree, where the game state
contains simultaneous actions. Environmental node.
'''
class ActionMatrix(Node):
    def __init__(self, state, parent, action):
        self.parent = parent
        self.action = action
        self.state = state
        self.child_nodes = []
        self.player_actions = {}

    
    def decoupled_uct_selection(self, possible_actions, exploration):
        legal_actions = filter(lambda a: a.action in possible_actions, self.player_actions.values())
        joint_action = [None] * len(self.player_actions)
        for p in self.player_actions:
            actions = self.player_actions[p]
            ucb_eq = lambda a: a.reward / a.visits + exploration * sqrt(log(a.avails) / a.visits)
            
            for action in legal_actions:
                action.avails += 1

            selected_action = max(actions, key=ucb_eq)

            if self.state.gamestate == Gamestates.VOTING:
                joint_action[p] = selected_action
            elif self.state.gamestate == Gamestates.MISSION:
                joint_action.append((p, selected_action))
        return joint_action

    
    def append_action_node(self, joint_action):
        if joint_action['type'] == Gamestates.VOTING:
            for p, vote in enumerate(joint_action['action']):
                if p not in self.player_actions:
                        self.player_actions[p] = []
                self.player_actions[p].append(ActionNode(parent=self, player=p, action=vote))

        elif joint_action['type'] == Gamestates.MISSION:
            for p, has_sabotaged in joint_action['action']:
                if p not in self.player_actions:
                    self.player_actions[p] = []
                self.player_actions[p].append(ActionNode(parent=self, player=p, action=has_sabotaged))

        else:
            raise Exception("Initialising action matrix with non-simultaneous actions")

    
    def unexplored_actions(self, possible_actions):
        explored_actions = [action_node.action for action_node in self.player_actions]
        return filter(lambda m: m not in explored_actions, possible_actions)


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


def rollout(state):
    while state.get_moves() != []:
        state.make_move(random.choice(state.get_moves()))
    return state
        


    