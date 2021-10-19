from math import sqrt, log
import random
from MCTS.state import StateNames


class PlayerTree:
    def __init__(self, root_node):
        self.root_node = root_node
        self.current_node = root_node

    def __repr__(self):
        return f'Root node: {str(self.root_node)} | Current node: {str(self.current_node)}'


'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and backpropagation.
'''
class Node:
    def __init__(self, player, parent=None, action=None):     
        self.player = player                # Player id for the player that this node belongs to
        self.parent = parent                # None if root state
        self.action = action                # Action that parent took to lead to this node. None if root state.
        self.reward = 0                     # MCTS reward during backpropagation
        self.visits = 0                     # MCTS visits during backpropagation
        self.avails = 0                     # Number of times parent has been visited during backpropagation
        self.determination_visits = {}      # Number of visits for each determination during backpropagation - format is {determination: visits, ...}
        self.children = {}                  # {action: childnode, ...}
           

    def ucb_selection(self, possible_actions, exploration):
        possible_actions = [a.value for a in possible_actions]
        legal_children = [c for a, c in self.children.items() if a in possible_actions]
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(c.avails) / c.visits)
        
        for child in legal_children:
            child.avails += 1

        node = max(legal_children, key=ucb_eq)

        return node


    def append_child(self, observer_is_spy, next_state, action):
        next_player = next_state.player

        # does the next state produce partially observable moves in the perspective of the observer.
        is_partial_observer = not observer_is_spy and next_state.state_name == StateNames.SABOTAGE

        if is_partial_observer or next_state.state_name == StateNames.TERMINAL:
            child_node = EnvironmentalNode(parent=self, action=action)
        elif type(next_player) == tuple:
            child_node = SimultaneousMoveNode(next_player, self, action)
        else:
            child_node = Node(next_player, self, action)

        self.children[action.value] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node):
        self.reward += terminal_state.game_result(self.player)
        
        d = terminal_state.determination
        if d not in self.determination_visits:
            self.determination_visits[d] = 0
        
        self.determination_visits[d] += 1
        self.visits += 1
        return self


    def unexplored_actions(self, possible_actions):
        return [a for a in possible_actions if a.value not in self.children.keys()]

    
    def __repr__(self):
        return "Node - Player %i [%s  W/V/A: %i/%i/%i]" % (
            self.player,
            self.action,
            self.reward,
            self.visits,
            self.avails,
        )


'''
A class used to define nodes in the Monte Carlo tree, where there is no opportunity for any player to gain a reward. 
This includes TERMINAL states and SABOTAGE states, in the perspective of a non-saboteur. Such nodes are 
merely filler nodes to store information about successive and preceding nodes in a player tree.
'''
class EnvironmentalNode(Node):
    def __init__(self, parent=None, action=None):
        self.player = -1
        self.parent = parent
        self.action = action
        self.reward = 0                                                          
        self.visits = 0
        self.avails = 0
        self.determination_visits = {}
        self.children = {}

    def backpropagate(self, terminal_state, child_node):
        self.determination_visits[terminal_state.determination] += 1
        self.visits += 1
    
    def __repr__(self):
        return "Env node - [%s  V/A: %i/%i]" % (
            self.action,
            self.visits,
            self.avails,
        )


'''
A class used to define nodes in the Monte Carlo tree, where the game state contains simultaneous actions
- i.e., when players are unable to observe the actions of other actors until all actions have been performed.
The selection process uses Decoupled UCT Selection (DUCT) to choose a child node. DUCT performs UCT independently
over each player's possible actions and constructs an optimal 'joint action', through which a child node is chosen.
'''
class SimultaneousMoveNode(Node):
    def __init__(self, player, parent=None, action=None):
        self.player = player                
        self.parent = parent
        self.action = action
        self.reward = 0
        self.visits = 0
        self.avails = 0
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

    
    def append_child(self, observer_is_spy, next_state, joint_action):
        next_player = next_state.player
        for p, action in joint_action.value:
            if p not in self.player_actions:
                self.player_actions[p] = []
            self.player_actions[p].append(ActionNode(parent=self, player=p, action=action))

        # does the next state produce partially observable moves in the perspective of the observer.
        is_partial_observer = not observer_is_spy and next_state.state_name == StateNames.SABOTAGE

        if is_partial_observer or next_state.state_name == StateNames.TERMINAL:
            child_node = EnvironmentalNode(parent=self, action=action)
        elif type(next_player) == tuple:
            child_node = SimultaneousMoveNode(player=next_player, parent=self, action=action)
        else:
            child_node = Node(player=next_player, parent=self, action=action)
        self.children[joint_action.value] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node=None):
        if child_node:
            joint_action = child_node.action
            for p, action in joint_action:
                action_node, = [node for node in self.player_actions[p] if node.action == action]
                action_node.reward += terminal_state.game_result(p)
                action_node.visits += 1

        d = terminal_state.determination
        if d not in self.determination_visits:
            self.determination_visits[d] = 0

        self.visits += 1 
        self.determination_visits[terminal_state.determination] += 1
        return self
    

    def __repr__(self):
        return "SimultanousMoveNode - [%s  V/A: %i/%i]" % (
            self.action,
            self.visits,
            self.avails,
        )


"""
Stores the actions of a single player in a simultaneous move. DUCT evaluates
UCT on all action nodes for each player to find the optimal joint action.
"""
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
        


    