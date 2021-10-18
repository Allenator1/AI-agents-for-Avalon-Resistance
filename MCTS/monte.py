import random
from copy import deepcopy, copy
from itertools import combinations
from MCTS.state import ResistanceState, Gamestates, Roles
from MCTS.node import Node, SimultaneousMoveNode, PlayerTree
from agent import Agent

NUM_ITERATIONS = 1000

class Monte(Agent):

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
        self.player = player_number
        self.num_players = number_of_players
        self.rnd = 0
        self.missions_succeeded = 0
        self.num_selection_fails = 0
        self.total_iterations = 0
        
        if spies == []:
            self.is_spy = False
            self.determinations, self.probabilities = initialise_determinations(player_number, number_of_players)


    def propose_mission(self, team_size, fails_required = 1):
        '''
        expects a team_size list of distinct agents with id between 0 (inclusive) and number_of_players (exclusive)
        to be returned. 
        fails_required are the number of fails required for the mission to fail.
        '''
        self.gamestate = Gamestates.SELECTION
        self.current_player = self.player
        if self.total_iterations == 0:
            self.forest = initialise_player_trees(self.current_player)
        
        if not self.is_spy:
            selected_node = self.inference_ISMCTS(NUM_ITERATIONS)
            self.total_iterations += NUM_ITERATIONS
            self.mission = selected_node.action

        return self.mission    


    def vote(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The function should return True if the vote is for the mission, and False if the vote is against the mission.
        '''
        self.gamestate = Gamestates.VOTING
        self.current_player = [p for p in range(self.num_players)]
        if self.rnd == 0:
            self.forest = initialise_player_trees(self.current_player)

        if not self.is_spy:
            selected_node = self.inference_ISMCTS(NUM_ITERATIONS)
            self.total_iterations += NUM_ITERATIONS
            all_votes = selected_node.action

        return all_votes[self.player][1]


    def vote_outcome(self, mission, proposer, votes):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        votes is a dictionary mapping player indexes to Booleans (True if they voted for the mission, False otherwise).
        No return value is required or expected.
        '''
        self.action = [(p, v) for p, v in votes.items()]
        num_votes_for = sum(votes.values())
        if num_votes_for * 2 > len(votes):
            self.gamestate = Gamestates.SABOTAGE
        else:
            self.gamestate = Gamestates.SELECTION
            self.num_selection_fails += 1


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
        self.action = num_fails
        self.state = Gamestates.SELECTION
        self.rnd += 1
        self.missions_succeeded += mission_success


    def round_outcome(self, rounds_complete, missions_failed):
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the numbe of missions (0-3) that have failed.
        '''
        self.rnd = rounds_complete + 1
        self.missions_succeeded = self.rnd - missions_failed
        self.num_selection_fails = 0
        self.mission = []
    

    def game_outcome(self, spies_win, spies):
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''
        pass


    def inference_ISMCTS(self, itermax):
        for _ in range(itermax):
            # determinize
            determination = random.choice(self.determinations)
            state = ResistanceState(determination, self.gamestate, self.rnd, self.missions_succeeded, self.player,
                self.mission, self.num_selection_fails)
            
            # extracting the trees where player roles are compatible with the current determination, producing a single tree for each player
            d_forest = [self.forest[p][determination[p]] for p in range(self.num_players)] 
            current_node = lambda p: d_forest[p].current_node

            # selection and parallel tree descent  
            node = select_from_forest(state, d_forest)
            while state.get_moves() != [] and node.unexplored_actions(state.get_moves()) == []:     # while node is non-terminal and fully explored
                node = node.ucb_selection(state.get_moves(), 0.7)

                for p in range(self.num_players):
                    children = current_node(p).children.values()
                    d_forest[p].current_node, = [c for c in children if c == node]

                state = state.make_move(node.action)
                node = select_from_forest(state, d_forest)

            # expansion
            if state.get_moves() != []:    # if node is non-terminal
                unexplored_actions = node.unexplored_actions(state.get_moves())
                action = random.choice(unexplored_actions)
                state = state.make_move(action)
                # expand for each player tree via the action in their perspective
                for p in range(self.num_players):
                    observed_action = get_observed_action(p, action, state)
                    if observed_action not in current_node(p).children:
                        child = current_node(p).append_child(state.get_game_state(), observed_action)
                        d_forest[p].current_node = child

            # playout
            terminal_state = playout(state)

            # backpropagation
            for p in range(self.num_players):
                while (current_node(p).parent != None):   # backpropagate to root node
                    current_node(p).parent.backpropagate(terminal_state, current_node(p))
                    d_forest[p].current_node = current_node(p).parent

        return max(current_node(self.player).children.values(), key=lambda c: c.visits)


def playout(state):
    while state.get_moves() != []:
        state.make_move(random.choice(state.get_moves()))
    return state       


def select_from_forest(state, forest):
    player = state.player
    if type(player) == int:                       # SELECTION node
        node = forest[player].current_node
    elif type(player) == list:                    # Simultaneous action node (VOTING or SABOTAGE)
        node = forest[random.choice(player)].current_node
    return node


def initialise_player_trees(num_players, starting_player):
    if type(starting_player) == list:
        root_node = SimultaneousMoveNode(starting_player)
    else:
        root_node = Node(starting_player)

    monte_carlo_forest = [{} for _ in range(num_players)]
    for p in range(num_players):
        monte_carlo_forest[p][False] = PlayerTree(deepcopy(root_node))
        monte_carlo_forest[p][True] = PlayerTree(deepcopy(root_node))
    return monte_carlo_forest


def initialise_determinations(player, num_players):
    num_spies = Agent.spy_count[num_players]
    possible_spies = filter(lambda p: p != player, range(num_players))
    spy_configurations = combinations(possible_spies, num_spies)
    determinations = []
    probabilities = []
    for spies in spy_configurations:
        d = [True if p in spies else False for p in range(num_players)]
        p = 1 / len(spy_configurations)          # Equal probability to choose a determination
        determinations.append(d)
        probabilities.append(p)
    return determinations, probabilities


def get_observed_action(player, action, parent_state):
    if parent_state.gamestate == Gamestates.SABOTAGE and player in parent_state.player:
        betrays = [betrayed for _, betrayed in action]
        observed_action = sum(betrays)
    else:
        observed_action = action
    return observed_action


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