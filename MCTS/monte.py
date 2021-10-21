import random
import time
from copy import deepcopy, copy
from itertools import combinations
from MCTS.state import StateNames, ResistanceState, get_actions_time
from MCTS.node import Node
from agent import Agent

MAX_TIME = 0.350

class Monte(Agent):

    def __init__(self, name):
        '''
        Initialises the agent, and gives it a name
        You can add configuration parameters etc here,
        but the default code will always assume a 1-parameter constructor, which is the agent's name.
        The agent will persist between games to allow for long-term learning etc.
        '''
        self.name = name
        self.player = 0
        self.num_players = 5
        self.determinations, self.probabilities = initialise_determinations(self.player, self.num_players)

        self.leader = self.player
        self.state_name=StateNames.SELECTION
        self.rnd=0
        self.missions_succeeded=0
        self.mission=[]
        self.num_selection_fails=0


        self.root_node = Node(self.player)
        selected_node = self.ISMCTS(MAX_TIME)


    def __str__(self):
        '''
        Returns a string represnetation of the agent
        '''
        return 'Agent '+self.name


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
        pass


    def propose_mission(self, team_size, fails_required = 1):
        '''
        expects a team_size list of distinct agents with id between 0 (inclusive) and number_of_players (exclusive)
        to be returned. 
        fails_required are the number of fails required for the mission to fail.
        '''
        pass 


    def vote(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The function should return True if the vote is for the mission, and False if the vote is against the mission.
        '''
        pass


    def vote_outcome(self, mission, proposer, votes):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        votes is a dictionary mapping player indexes to Booleans (True if they voted for the mission, False otherwise).
        No return value is required or expected.
        '''
        pass


    def betray(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players, and include this agent.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The method should return True if this agent chooses to betray the mission, and False otherwise. 
        Only spies are permitted to betray the mission. 
        '''
        pass


    def mission_outcome(self, mission, proposer, num_fails, mission_success):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        num_fails is the number of people on the mission who betrayed the mission, 
        and mission_success is True if there were not enough betrayals to cause the mission to fail, False otherwise.
        It iss not expected or required for this function to return anything.
        '''
        pass


    def round_outcome(self, rounds_complete, missions_failed):
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the numbe of missions (0-3) that have failed.
        '''
        pass
    

    def game_outcome(self, spies_win, spies):
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''
        pass


    def ISMCTS(self, max_time):
        start_time = time.time()
        time_diff = 0
        it = 0
        while (time_diff < max_time):
            it += 1
            # determinize
            determination = random.choice(self.determinations)
            state = ResistanceState(determination, self.leader, self.player, self.state_name, self.rnd,
                self.missions_succeeded, self.mission, self.num_selection_fails)

            temperature = min(0.7, (1 - (i + 1) / itermax))

            t1 = time.time()
            # selection
            node = self.root_node
            moves = state.get_moves()
            while moves != [] and node.unexplored_actions(moves) == []: 
                node = node.ucb_selection(moves, temperature)
                state.make_move(node.action)
                moves = state.get_moves()
            t2 = time.time()

            # expansion
            if moves != []:    # if node is non-terminal
                unexplored_actions = node.unexplored_actions(moves)
                action = random.choice(unexplored_actions)
                state.make_move(action)
                node = node.append_child(state.player, action)
            t3 = time.time()

            # playout
            terminal_state = playout(state)
            t4 = time.time()
            
            # backpropagation
            child = node.backpropagate(terminal_state)
            while (node != self.root_node):   # backpropagate to root node
                node = node.parent
                child = node.backpropagate(terminal_state, child)
            
            time_diff = time.time() - start_time
            
        print(self.root_node.stringify_tree(4))
        print(it)
        return max(self.root_node.children.values(), key=lambda c: c.visits).action   


def playout(state):
    moves = state.get_moves()
    while moves != []:
        state.make_move(random.choice(moves))
        moves = state.get_moves()
    return state       


def initialise_determinations(player, num_players):
    num_spies = Agent.spy_count[num_players]
    possible_spies = filter(lambda p: p != player, range(num_players))
    spy_configurations = list(combinations(possible_spies, num_spies))
    determinations = []
    probabilities = []
    for spies in spy_configurations:
        d = tuple([True if p in spies else False for p in range(num_players)])
        p = 1 / len(spy_configurations)          # Equal probability to choose a determination
        determinations.append(d)
        probabilities.append(p)
    return determinations, probabilities


# updates determination probabilities after observing (s, a) => v according to the assumption that
# P(d | a) = visits(v, d) / visits(v)
def particle_filter_inference(node_u, node_v, action, determinations, probabilities, itermax):  
    w = node_u.visits / itermax
    for i in range(len(determinations)):
        d = determinations[i]
        if not legal_action(d, action):
            probabilities[i] = 0
            normalise_probabilities(determinations)
        else:
            probabilities[i] = (1 - w) * probabilities[i] + w * node_v.determination_visits[d] / node_v.visits 


def legal_action(determination):
    pass

def normalise_probabilities(determinations):
    pass

m = Monte('monte')