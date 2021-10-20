import random
from copy import deepcopy, copy
from itertools import combinations
from MCTS.state import StateNames, Roles, Action, StateInfo, ResistanceState
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
        self.player = 0
        self.num_players = 5
        self.determinations, self.probabilities = initialise_determinations(self.player, self.num_players)

        self.leader = self.player
        self.state_name=StateNames.SELECTION
        self.rnd=0
        self.missions_succeeded=0
        self.mission=[]
        self.num_selection_fails=0

        state_info = StateInfo(self.leader, self.player, self.state_name, self.rnd, self.missions_succeeded,
            self.mission, self.num_selection_fails)

        self.forest = initialise_player_trees(self.player, state_info, self.num_players)

        selected_node = self.inference_ISMCTS(NUM_ITERATIONS)


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


    def inference_ISMCTS(self, itermax):
        for i in range(itermax):
            # determinize
            determination = random.choice(self.determinations)
            state = ResistanceState(determination, self.leader, self.player, self.state_name, self.rnd,
                self.missions_succeeded, self.mission, self.num_selection_fails)
            
            # extracting the trees where player roles are compatible with the current determination, producing a single tree for each player
            d_forest = [self.forest[p][determination[p]] for p in range(self.num_players)] 
            # Returns all trees for player p (1 for each role they may take)
            all_trees = lambda p: self.forest[p].items() 

            # selection
            node = select_from_trees(state, d_forest)
            while state.get_moves() != [] and node.unexplored_actions(state.get_moves()) == []: 
                node = node.ucb_selection(state.get_moves(), 0.7)

                # tree descent for other player trees
                for p in range(self.num_players):
                    for _, tree in all_trees(p):
                        children = tree.current_node.children
                        tree.current_node, = [c for c in children.values() if c.state_info == node.state_info and c.action.equivalent(node.action)]

                state.make_move(node.action)
                node = select_from_trees(state, d_forest)

            # expansion
            if state.get_moves() != []:    # if node is non-terminal
                unexplored_actions = node.unexplored_actions(state.get_moves())
                action = random.choice(unexplored_actions)
                prev_state = deepcopy(state)
                state.make_move(action)
                # expand for each player tree via the action in their perspective
                for p in range(self.num_players):
                    for observer_is_spy, tree in all_trees(p):
                        expansion(tree, observer_is_spy, prev_state, state, action)

            # playout
            terminal_state = playout(state)
            
            # backpropagation
            for p in range(self.num_players):
                for _, tree in all_trees(p):
                    child = tree.current_node.backpropagate(terminal_state)
                    tree.current_node = tree.current_node.parent
                    
                    while (tree.current_node != None):   # backpropagate to root node
                        child = tree.current_node.backpropagate(terminal_state, child)
                        tree.current_node = tree.current_node.parent

            # reset tree iteration position
            for p in range(self.num_players):
                for _, tree in all_trees(p):
                    tree.current_node = tree.root_node

        return max(d_forest[self.player].current_node.children.values(), key=lambda c: c.visits)   


def expansion(tree, observer_is_spy, current_state, next_state, action):
    observed_action = get_observed_action(observer_is_spy, current_state, action)
    if observed_action not in tree.current_node.children:
        child = tree.current_node.append_child(observer_is_spy, next_state, observed_action)
        tree.current_node = child


def playout(state):
    while state.get_moves() != []:
        state.make_move(random.choice(state.get_moves()))
    return state       


def select_from_trees(state, forest):
    player = state.player
    if type(player) == int:                       # SELECTION node
        node = forest[player].current_node
    elif type(player) == tuple:                    # Simultaneous action node (VOTING or SABOTAGE)
        node = forest[random.choice(player)].current_node
    return node


def initialise_player_trees(starting_player, state_info, num_players):
    if type(starting_player) == list:
        root_node = SimultaneousMoveNode(starting_player, state_info)
    else:
        root_node = Node(starting_player, state_info)

    monte_carlo_forest = [{} for _ in range(num_players)]
    for p in range(num_players):
        monte_carlo_forest[p][False] = PlayerTree(deepcopy(root_node))
        monte_carlo_forest[p][True] = PlayerTree(deepcopy(root_node))
    return monte_carlo_forest


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


def get_observed_action(observer_is_spy, current_state, action):
    if not observer_is_spy and current_state.state_name == StateNames.SABOTAGE:  
        betrays = [betrayed for _, betrayed in action.value]
        observed_action_val = (sum(betrays), current_state.mission)
        observed_action = current_state.generate_action(StateNames.SABOTAGE, observed_action_val, True)
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

m = Monte('monte')