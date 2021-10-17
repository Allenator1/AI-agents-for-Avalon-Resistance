from math import sqrt, log
import random
from MCTS.state import StateNames


class PlayerTree:
    def __init__(self, root_node):
        self.root_node = root_node
        self.current_node = root_node


'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and playouts.
'''
class Node:
    def __init__(self, player, game_state, parent=None, action=None):     
        self.player = player                # Player id for the player that this node belongs to. -1 for terminal node
        self.game_state = game_state        # Representation of the game
        self.parent = parent                # None if root state
        self.action = action                # Action that parent took to lead to this node. None if root state.
        self.reward = 0                     # MCTS reward during backpropagation
        self.visits = 0                     # MCTS visits during backpropagation
        self.avails = 0                     # Number of times parent has been visited during backpropagation
        self.determination_visits = {}      # Number of visits for each determination during backpropagation - format is {determination: visits, ...}
        self.children = {}                  # {action: childnode, ...}
           

    def ucb_selection(self, possible_actions, exploration):
        legal_children = filter(lambda c: c.action in possible_actions, self.children.values())
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(c.avails) / c.visits)
        
        for child in legal_children:
            child.avails += 1

        node = max(legal_children, key=ucb_eq)

        return node

    
    def expand(self, next_player, possible_actions):
        unexplored_actions = self.unexplored_actions(possible_actions)
        if unexplored_actions != []:
            action = random.choice(unexplored_actions)
            node = self.append_child(next_player, action)
            return node


    def append_child(self, next_player, action):
        if type(next_player) == list:
            child_node = SimultaneousMoveNode(player=next_player, parent=self, action=action)
        else:
            child_node = Node(player=next_player, parent=self, action=action)
        self.children[action] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node):
        self.reward += terminal_state.get_result(self.player)
        self.determination_visits[terminal_state.determination] += 1
        self.visits += 1


    def unexplored_actions(self, possible_actions):
        return filter(lambda a: a not in self.children.keys(), possible_actions)


    def __eq__(self, other):
        return self.game_state == other.game_state                                                                   


'''
A class used to define nodes in the Monte Carlo tree, where the game state
contains simultaneous actions. Uses Decoupled UCT Selection (DUCT) to choose a
child node during the selection phase.
'''
class SimultaneousMoveNode(Node):
    def __init__(self, player, game_state, parent=None, action=None):
        self.player = player                # player = -1 if TERMINAL node
        self.game_state = game_state
        self.parent = parent
        self.action = action
        self.visits = 0
        self.determination_visits = {}
        self.player_actions = {}            # {player_id: [action_node, ...], ...}
        self.children = {}                  # {joint_action: childnode, ...}

    
    def ucb_selection(self, possible_actions, exploration):
        joint_action = []
        for p, actions in self.player_actions.items():

            ucb_eq = lambda a: a.reward / a.visits + exploration * sqrt(log(a.avails) / a.visits)
            
            for action in actions:
                action.avails += 1

            selected_action = max(actions, key=ucb_eq)
            joint_action.append((p, selected_action))
        node = self.children[joint_action]
        return node

    
    def append_child(self, next_player, joint_action):
        for p, action in joint_action['action']:
            if p not in self.player_actions:
                self.player_actions[p] = []
            self.player_actions[p].append(ActionNode(parent=self, player=p, action=action))

        if type(next_player) == list:
            child_node = SimultaneousMoveNode(player=next_player, parent=self, action=action)
        else:
            child_node = Node(player=next_player, parent=self, action=action)
        self.children[joint_action['action']] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node):
        joint_action = child_node.action
        for p, action in joint_action:
            action_node, = [node for node in self.player_actions[p] if node.action == action]
            action_node.reward += terminal_state.get_result(p)
            action_node.visits += 1
        self.visits += 1 
        self.determination_visits[terminal_state.determination] += 1
    

class ActionNode():
    def __init__(self, player, parent, action):
        self.player = player           
        self.parent = parent
        self.action = action                    # action is either True or False (e.g., a player voted True)                
        self.reward = 0
        self.visits = 0
        self.avails = 0


    def backpropagate(self, terminal_state):
        self.reward += terminal_state.get_result(self.player)
        self.visits += 1
        


    