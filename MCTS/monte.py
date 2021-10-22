import random
import time
from itertools import combinations
from MCTS.state import StateNames, ResistanceState, FAILS_REQUIRED, SPY_COUNT
from MCTS.node import Node, SimultaneousMoveNode


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
            self.probabilities = [1.0]
        else:
            self.determinations, self.probabilities = initialise_determinations(self.player, self.num_players)

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

        self.ISMCTS(MAX_TIME, range(self.num_players))
        self_action = max(self.root_node.player_actions[self.player], 
            key=lambda a: a.visits).value
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

        self.ISMCTS(MAX_TIME, spies_in_mission)
        self_action = max(self.root_node.player_actions[self.player], 
            key=lambda a: a.visits).value
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


    def ISMCTS(self, max_time, current_player):
        start_time = time.time()
        time_diff = 0
        it = 0
        while (time_diff < max_time):
            it += 1
            # determinize
            determination = random.choices(self.determinations, self.probabilities)[0]
            state = ResistanceState(determination, self.leader, current_player, self.state_name, self.rnd,
                self.missions_succeeded, self.mission, self.num_selection_fails)

            temperature = min(0.9, (1 - time_diff / max_time))

            # selection
            node = self.root_node
            moves = state.get_moves()
            while moves != [] and node.unexplored_actions(moves) == []: 
                node = node.ucb_selection(moves, 0.7)
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
        for i in range(len(self.determinations)):
            d = self.determinations[i]
            num_players = len(d)
            spies = [p for p in range(num_players) if d[p]]
            spies_in_mission = [s for s in spies if s in mission]
            if num_sabotages > len(spies_in_mission):
                self.probabilities[i] = 0
            normalise_probabilities(self.probabilities)


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
    probabilities = []
    for spies in spy_configurations:
        d = tuple([True if p in spies else False for p in range(num_players)])
        p = 1 / len(spy_configurations)          # Equal probability to choose a determination
        determinations.append(d)
        probabilities.append(p)
    return determinations, probabilities
        

def normalise_probabilities(probabilities):
    n_legal_determinations = [p for p in probabilities if p != 0]
    for i in range(len(probabilities)):
        if probabilities[i] != 0: probabilities[i] = 1 / len(n_legal_determinations)
