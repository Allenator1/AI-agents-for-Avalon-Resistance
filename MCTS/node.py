from math import sqrt, log
from MCTS.state import StateNames


'''
A class used to define nodes in the Monte Carlo tree, including methods
used for node expansion, selection and backpropagation.
'''
class Node:
    def __init__(self, player, parent=None, action=None):     
        self.player = player                # Player id for the player about to move
        self.parent = parent                # None if root state
        self.action = action                # Action that parent took to lead to this node. None if root state.
        self.reward = 0                     # MCTS reward during backpropagation
        self.visits = 0                     # MCTS visits during backpropagation
        self.avails = 0                     # Number of times parent has been visited during backpropagation
        self.determination_visits = {}      # Number of visits for each determination during backpropagation - format is {determination: visits, ...}
        self.children = {}                  # {action: childnode, ...}

    def ucb_selection(self, possible_actions, exploration):
        legal_children = [c for a, c in self.children.items() if a in possible_actions]
        ucb_eq = lambda c: c.reward / c.visits + exploration * sqrt(log(c.avails) / c.visits)
        
        for child in legal_children:
            child.avails += 1

        node = max(legal_children, key=ucb_eq)

        return node


    def append_child(self, next_player, action):
        if type(next_player) == tuple:
            child_node = SimultaneousMoveNode(next_player, self, action)
        else:
            child_node = Node(next_player, self, action)

        self.children[action] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node=None):
        player_just_moved = None if self.parent is None else self.parent.player
        if type(player_just_moved) == int:
            self.reward += terminal_state.game_result(player_just_moved)
        
        d = terminal_state.determination
        if d not in self.determination_visits:
            self.determination_visits[d] = 0
        
        self.determination_visits[d] += 1
        self.visits += 1
        return self


    def unexplored_actions(self, possible_actions):
        return [a for a in possible_actions if a not in self.children.keys()]

    
    def __repr__(self):
        return "Node - Player %i [%s  W/V/A: %i/%i/%i]" % (
            self.player,
            self.action,
            self.reward,
            self.visits,
            self.avails,
        )

    
    def __str__(self):
        return "[%i/%i/%i]" % (
            self.reward,
            self.visits,
            self.avails,
        )


    def stringify_tree(self, indent):
        """ Represent the tree as a string, for debugging purposes.
        """
        s = self.indent_string(indent) + str(self)
        for c in self.children.values():
            s += c.stringify_tree(indent + 1)
        return s


    def indent_string(self, indent):
        s = "\n"
        for i in range(1, indent + 1):
            s += "| "
        return s


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

        self.initialise_player_actions()

    
    def initialise_player_actions(self):
        for p in self.player:
            self.player_actions[p] = []
            self.player_actions[p].append(ActionNode(p, self, True))
            self.player_actions[p].append(ActionNode(p, self, False))

    
    def ucb_selection(self, possible_actions, exploration):
        legal_children = [c for a, c in self.children.items() if a in possible_actions]
        for child in legal_children:
            child.avails += 1

        joint_action = []    
        for p, actions in self.player_actions.items():
            ucb_eq = lambda a: 0 if a.visits == 0 else \
                a.reward / a.visits + exploration * sqrt(log(self.visits) / a.visits)

            selected_action = max(actions, key=ucb_eq)
            joint_action.append((p, selected_action.value))

        joint_action, = [a for a in possible_actions if set(a.value) == set(joint_action)]
        
        node = self.children[joint_action]
        return node

    
    def append_child(self, next_player, joint_action):
        if type(next_player) == tuple:
            child_node = SimultaneousMoveNode(next_player, self, joint_action)
        else:
            child_node = Node(next_player, self, joint_action)
        
        self.children[joint_action] = child_node
        return child_node

    
    def backpropagate(self, terminal_state, child_node=None):
        if child_node:
            joint_action = child_node.action
            for p, action in joint_action.value:
                backpropagated_action, = [node for node in self.player_actions[p] if node.value == action]
                backpropagated_action.reward += terminal_state.game_result(p)
                backpropagated_action.visits += 1

        d = terminal_state.determination
        if d not in self.determination_visits:
            self.determination_visits[d] = 0
        
        player_just_moved = None if self.parent is None else self.parent.player
        if type(player_just_moved) == int:
            self.reward += terminal_state.game_result(player_just_moved)
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
    def __init__(self, player, parent, value):
        self.player = player           
        self.parent = parent
        self.value = value                    # action is either True or False (e.g., a player voted True)                
        self.reward = 0
        self.visits = 0
        self.avails = 0


    def __repr__(self):
        return 'A[' + str(self.value) + ']'
    
        


    