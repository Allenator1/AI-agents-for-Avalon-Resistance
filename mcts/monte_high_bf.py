import random
import time
from itertools import combinations, product


MAX_TIME = 0.350

class Monte():

    def __init__(self, name):
        '''
        Initialises the agent, and gives it a name
        You can add configuration parameters etc here,
        but the default code will always assume a 1-parameter constructor, which is the agent's name.
        The agent will persist between games to allow for long-term learning etc.
        '''
        self.name = name


    def __str__(self):
        '''
        Returns a string represnetation of the agent
        '''
        return 'Agent ' + self.name


    def __repr__(self):
        '''
        returns a representation fthe state of the agent.
        default implementation is just the name, but this may be overridden for debugging
        '''
        return self.__str__()


    def new_game(self, number_of_players, player_number, spies):
        '''
        initialises the game, informing the agent of the number_of_players, 
        the player_number (an id number for the agent in the game),
        and a list of agent indexes, which is the set of spies if this agent is a spy,
        or an empty list if this agent is not a spy.
        '''
        self.spies = spies
        self.is_spy = False if spies == [] else True
        
        self.player = player_number
        self.num_players = number_of_players
        if self.is_spy:
            d = tuple([True if p in spies else False for p in range(number_of_players)])
            self.determinations = [d]
        else:
            self.determinations = initialise_determinations(self.player, self.num_players)

        self.rnd = 0
        self.missions_succeeded = 0
        self.mission = []
        self.num_selection_fails = 0


    def propose_mission(self, team_size, fails_required = 1):
        '''
        expects a team_size list of distinct agents with id between 0 (inclusive) and number_of_players (exclusive)
        to be returned. 
        fails_required are the number of fails required for the mission to fail.
        '''
        self.leader = self.player
        self.state_name = StateNames.SELECTION

        self.root_node = Node(self.player)

        selected_node = self.ISMCTS(MAX_TIME, self.player)
        mission = list(selected_node.action.value)
        return mission


    def vote(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The function should return True if the vote is for the mission, and False if the vote is against the mission.
        '''
        self.leader = proposer
        self.state_name = StateNames.VOTING
        self.mission = mission

        self.root_node = SimultaneousMoveNode(range(self.num_players))
        
        selected_node = self.ISMCTS(MAX_TIME, range(self.num_players))
        joint_action = selected_node.action.value
        self_action, = [a for p, a in joint_action if p == self.player]
        return self_action


    def vote_outcome(self, mission, proposer, votes):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        votes is a dictionary mapping player indexes to Booleans (True if they voted for the mission, False otherwise).
        No return value is required or expected.
        '''
        num_votes_for = sum(votes)
        if num_votes_for * 2 < self.num_players:
            self.num_selection_fails += 1
        else:
            self.num_selection_fails = 0


    def betray(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players, and include this agent.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The method should return True if this agent chooses to betray the mission, and False otherwise. 
        Only spies are permitted to betray the mission. 
        '''
        self.leader = proposer
        self.state_name = StateNames.SABOTAGE
        self.mission = mission
        spies_in_mission = tuple([s for s in self.spies if s in self.mission])

        self.root_node = SimultaneousMoveNode(spies_in_mission)

        selected_node = self.ISMCTS(MAX_TIME, spies_in_mission)
        joint_action = selected_node.action.value
        self_action, = [a for p, a in joint_action if p == self.player]
        return self_action


    def mission_outcome(self, mission, proposer, num_fails, mission_success):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        num_fails is the number of people on the mission who betrayed the mission, 
        and mission_success is True if there were not enough betrayals to cause the mission to fail, False otherwise.
        It iss not expected or required for this function to return anything.
        '''
        if num_fails < FAILS_REQUIRED[self.num_players][self.rnd]:
            self.missions_succeeded += 1 
        self.rnd += 1 
        if not self.is_spy:
            self.remove_illegal_worlds(num_fails, mission)


    def round_outcome(self, rounds_complete, missions_failed):
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the numbe of missions (0-3) that have failed.
        '''
        self.rnd = rounds_complete
        self.missions_succeeded = rounds_complete - missions_failed
        self.num_selection_fails = 0
    

    def game_outcome(self, spies_win, spies):
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''
        pass


    def ISMCTS(self, max_time, current_player, use_simulated_annealing=True):
        start_time = time.time()
        time_diff = 0
        it = 0
        while (time_diff < max_time):
            it += 1
            # determinize
            determination = random.choice(self.determinations)
            state = ResistanceState(determination, self.leader, current_player, self.state_name, self.rnd,
                self.missions_succeeded, self.mission, self.num_selection_fails)

            temperature = min(0.8, (1 - time_diff / MAX_TIME))
            exploration = temperature if use_simulated_annealing else 0.7

            # selection
            node = self.root_node
            moves = state.get_moves()
            while moves != [] and node.unexplored_actions(moves) == []: 
                node = node.ucb_selection(moves, exploration)
                state.make_move(node.action)
                moves = state.get_moves()

            # expansion
            if moves != []:    # if node is non-terminal
                unexplored_actions = node.unexplored_actions(moves)
                action = random.choice(unexplored_actions)
                state.make_move(action)
                node = node.append_child(state.player, action)

            # playout
            terminal_state = playout(state)
            
            # backpropagation
            child = node.backpropagate(terminal_state)
            while (node != self.root_node):   # backpropagate to root node
                node = node.parent
                child = node.backpropagate(terminal_state, child)
            
            time_diff = time.time() - start_time
            
        return max(self.root_node.children.values(), key=lambda c: c.visits)  


    def remove_illegal_worlds(self, num_sabotages, mission):
        for d in self.determinations:
            num_players = len(d)
            spies = [p for p in range(num_players) if d[p]]
            spies_in_mission = [s for s in spies if s in mission]
            if num_sabotages > len(spies_in_mission):
                self.determinations.remove(d)


def playout(state):
    moves = state.get_moves()
    while moves != []:
        state.make_move(random.choice(moves))
        moves = state.get_moves()
    return state       


def initialise_determinations(player, num_players):
    num_spies = SPY_COUNT[num_players]
    possible_spies = filter(lambda p: p != player, range(num_players))
    spy_configurations = list(combinations(possible_spies, num_spies))
    determinations = []
    for spies in spy_configurations:
        d = tuple([True if p in spies else False for p in range(num_players)])
        determinations.append(d)
    return determinations    
    
    
    
# CLASSES TO DEFINE THE GAME STATE ---------------------------------------------------------------------



MISSION_SIZES = {
    5:[2,3,2,3,3], \
    6:[3,3,3,3,3], \
    7:[2,3,3,4,5], \
    8:[3,4,4,5,5], \
    9:[3,4,4,5,5], \
    10:[3,4,4,5,5]
}

SPY_COUNT = {5:2, 6:2, 7:3, 8:3, 9:3, 10:4}

FAILS_REQUIRED = {
    5:[1,1,1,1,1], \
    6:[1,1,1,1,1], \
    7:[1,1,1,2,1], \
    8:[1,1,1,2,1], \
    9:[1,1,1,2,1], \
    10:[1,1,1,2,1]
}


class Roles():
    SPY = 'SPY'
    NON_SPY = 'RESISTANCE'


class StateNames():
    SELECTION = 'MISSION SELECTION'
    VOTING = 'VOTING'
    SABOTAGE = 'MISSION SABOTAGE'
    TERMINAL = 'GAME END'          


'''
A class to encapsulate information relevant to an action
'''
class Action():
    def __init__(self, src_type, dst_type, player, value):
        self.src_type = src_type
        self.dst_type = dst_type
        self.player = player
        self.value = value 
        self.is_simultaneous = False
        if src_type == StateNames.SABOTAGE or src_type == StateNames.VOTING:
            self.is_simultaneous = True


    def __hash__(self):
        return hash((self.src_type, self.dst_type, self.player, self.value))


    def __eq__(self, other):
        return (self.src_type, self.dst_type, self.player, self.value) == \
               (other.src_type, other.dst_type, self.player, other.value)


    def __repr__(self):
        return 'Action[' + str(self.value) + ']'


'''
A class used to define a perfect information representation of a game state in 
Avalon Resistance, including methods to get all moves and apply moves.
'''
class ResistanceState():
    def __init__(self, determination, leader, player, state_name, rnd, 
        missions_succeeded, mission=[], num_selection_fails=0):
        self.leader = leader                                    # Stores the player_id of the last leader (current leader if in SELECTION state)
        self.player = player                                    # Current player/players in the state. -1 for a terminal state.  
        self.determination = determination                      # Array of booleans such that player 'p_id' is a spy if determination[p_id] = True
        self.state_name = state_name                            # Defines the current game state (SELECTION, VOTING, SABOTAGE or TERMINAL)
        self.rnd = rnd       
        self.missions_succeeded = missions_succeeded 
        self.mission = mission                                
        self.num_selection_fails = num_selection_fails          # Number of times a team has been rejected in the same round (max 5)  


    # Returns all possible actions from this state => A(state)
    def get_moves(self):
        actions = []
        num_players = len(self.determination)

        if self.state_name == StateNames.SELECTION:
            mission_size = MISSION_SIZES[num_players][self.rnd]
            possible_missions = combinations(range(num_players), mission_size) 
            action_vals = [tuple(mission) for mission in possible_missions]
            actions = [self.generate_action(StateNames.SELECTION, val) for val in action_vals]
        
        elif self.state_name == StateNames.VOTING:
            voting_combinations = product([False, True], repeat=num_players) 
            action_vals = [tuple(enumerate(votes)) for votes in voting_combinations]
            actions = [self.generate_action(StateNames.VOTING, val) for val in action_vals]

        elif self.state_name == StateNames.SABOTAGE:
            spies = [p for p in range(num_players) if self.determination[p]]
            spies_in_mission = [p for p in self.mission if p in spies]

            sabotage_combinations = product((False, True), repeat=len(spies_in_mission))
            action_vals = [tuple(zip(spies_in_mission, sabotages)) for sabotages in sabotage_combinations]
            actions = [self.generate_action(StateNames.SABOTAGE, val) for val in action_vals]
        return actions


    def generate_action(self, src_state, action_val):
        rnd = self.rnd
        dst_state = None
        player = None
        num_players = len(self.determination)
        spies = [p for p in range(num_players) if self.determination[p]]

        if src_state == StateNames.SELECTION:
            dst_state = StateNames.VOTING  
            player = tuple(range(num_players))                

        elif src_state == StateNames.VOTING:
            spies_in_mission = tuple([p for p in self.mission if p in spies])
            player_votes = action_val                       
            votes = [vote for _, vote in player_votes]
            num_votes_for = sum(votes)

            if num_votes_for * 2 > len(votes):
                if spies_in_mission:
                    dst_state = StateNames.SABOTAGE
                    player = spies_in_mission
                else:
                    dst_state = StateNames.SELECTION
                    player = (self.leader + 1) % len(self.determination) 
                    rnd += 1

            else:
                dst_state = StateNames.SELECTION
                player = (self.leader + 1) % len(self.determination) 
                if self.num_selection_fails >= 5:
                    rnd += 1

        elif src_state == StateNames.SABOTAGE:
            dst_state = StateNames.SELECTION
            player = (self.leader + 1) % len(self.determination) 
            rnd += 1
        
        if rnd > 4:
            dst_state = StateNames.TERMINAL
            player = -1

        return Action(src_state, dst_state, player, action_val)


    # Changes the game state object into a new state s' where s' = s(move)
    def make_move(self, action):
        num_players = len(self.determination)
        spies = [p for p in range(num_players) if self.determination[p]]

        if action.src_type == StateNames.SELECTION:
            self.state_name = StateNames.VOTING
            self.player = tuple(range(num_players))
            self.mission = action.value                         # Action is a list of player ids in the mission

        elif action.src_type == StateNames.VOTING:
            spies_in_mission = tuple([p for p in self.mission if p in spies])
            player_votes = action.value                         # Action has format ((p1, action1), (p2, action2), (p3, action3), ...)
            votes = [vote for _, vote in player_votes]
            num_votes_for = sum(votes)

            if num_votes_for * 2 > len(votes):
                if spies_in_mission:
                    self.state_name = StateNames.SABOTAGE
                    self.player = spies_in_mission
                else:
                    self.state_name = StateNames.SELECTION
                    self.leader = (self.leader + 1) % len(self.determination) 
                    self.player = self.leader
                    self.rnd += 1
                    self.missions_succeeded += 1
                self.num_selection_fails = 0

            elif self.num_selection_fails < 5:
                self.state_name = StateNames.SELECTION
                self.leader = (self.leader + 1) % len(self.determination) 
                self.player = self.leader
                self.num_selection_fails += 1

            else:
                self.state_name = StateNames.SELECTION
                self.leader = (self.leader + 1) % len(self.determination) 
                self.player = self.leader
                self.num_selection_fails = 0
                self.rnd += 1

        elif action.src_type == StateNames.SABOTAGE:
            num_fails_required = FAILS_REQUIRED[num_players][self.rnd]
            self.rnd += 1
            _, sabotages = zip(*action.value)               # Action has format [(spy1, action1), (spy2, action2), ...]
            num_sabotages = sum(sabotages)

            if num_sabotages < num_fails_required:
                self.missions_succeeded += 1

            self.state_name = StateNames.SELECTION
            self.leader = (self.leader + 1) % len(self.determination) 
            self.player = self.leader
        
        if self.rnd > 4:
            self.state_name = StateNames.TERMINAL


    # Returns the reward for a player based on the current determination stored in the state
    def game_result(self, player):
        num_fails = self.rnd - self.missions_succeeded
        if self.determination[player]:  # player is a spy
            score = num_fails - self.missions_succeeded
        else:
            score = self.missions_succeeded - num_fails
        return score / 2    # rewards from [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]        

    
    def __repr__(self):
        s = f'game state = {self.state_name} |' + \
            f' current player/s = {self.player} |' + \
            f' R/S/F = {self.rnd}/{self.missions_succeeded}/{self.rnd - self.missions_succeeded} |' 
        return s    
        
           
        
# CLASSES TO DEFINE NODES IN THE MONTE CARLO TREE ------------------------------------------------------



from math import sqrt, log


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
        
        
        
        
        
