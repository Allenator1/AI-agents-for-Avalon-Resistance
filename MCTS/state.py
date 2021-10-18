from agent import Agent
from itertools import combinations, product


class Roles():
    SPY = 'SPY'
    NON_SPY = 'RESISTANCE'


class StateNames():
    SELECTION = 'MISSION SELECTION'
    VOTING = 'VOTING'
    SABOTAGE = 'MISSION SABOTAGE'
    TERMINAL = 'GAME END'          


'''
Stores all information pertaining to the state of the game at any point in time.
'''
class GameState():
    def __init__(self, leader, player, state_name, rnd, missions_succeeded, mission=[], num_selection_fails=0):
        self.leader = leader                                # Stores the player_id of the last leader (current leader if in SELECTION state)
        self.player = player                                # Current player/players in the state. -1 for a terminal state.
        self.state_name = state_name                        # Defines the current game state (SELECTION, VOTING, SABOTAGE or TERMINAL)
        self.rnd = rnd
        self.missions_succeeded = missions_succeeded
        self.mission = mission                                
        self.num_selection_fails = num_selection_fails      # Number of times a team has been rejected in the same round (max 5)  
    
    
    def __eq__(self, other):
        self.leader = other.leader
        self.state_name = other.state_name and \
        self.rnd == other.rnd and \
        self.missions_succeeded == other.missions_succeed and \
        self.num_selection_fails == other.num_selection_fails and \
        self.mission == other.mission

    
    def __repr__(self):
        s = f'game state = {self.state_name} |' + \
            f' current player/s = {self.player} |' + \
            f' R/S/F = {self.rnd}/{self.missions_succeeded}/{self.rnd - self.missions_succeeded} |' 
        return s

'''
A class to encapsulate information relevant to an action
'''
class Action():
    def __init__(self, type, value, partially_observable):
        self.type = type
        self.value = value 
        if type == StateNames.SABOTAGE or type == StateNames.VOTING:
            self.is_simultaneous = True
        else: 
            self.is_simultaneous = False
        self.partially_observable = partially_observable
    

    def __eq__(self, other):
        return self.type == other.type and self.value == other.value and \
        self.partially_observable == other.partially_observable and \
        self.is_simultaneous == other.is_simultaneous

    
    def __repr__(self):
        return 'Action[' + str(self.value) + ']'


'''
A class used to define a perfect information representation of a game state in 
Avalon Resistance, including methods to get all moves and apply moves.
'''
class ResistanceState(GameState):
    def __init__(self, determination, game_state):
        self.leader = game_state.leader                             
        self.player = game_state.player                                       
        self.determination = determination                          # Array of booleans such that player 'p_id' is a spy if determination[p_id] = True
        self.state_name = game_state.state_name                     
        self.rnd = game_state.rnd       
        self.missions_succeeded = game_state.missions_succeeded 
        self.mission = game_state.mission                                
        self.num_selection_fails = game_state.num_selection_fails             


    # Returns all possible actions from this state => A(state)
    def get_moves(self):
        actions = []
        num_players = len(self.determination)

        if self.state_name == StateNames.SELECTION:
            mission_size = Agent.mission_sizes[num_players][self.rnd - 1]
            possible_missions = combinations(range(num_players), mission_size) 
            actions = [Action(StateNames.SELECTION, tuple(mission), False) for mission in possible_missions]
            
        elif self.state_name == StateNames.VOTING:
            voting_combinations = product([False, True], repeat=num_players) 
            actions = [Action(StateNames.VOTING, tuple(enumerate(votes)), False) for votes in voting_combinations]

        elif self.state_name == StateNames.SABOTAGE:
            spies = [p for p in range(num_players) if self.determination[p]]
            spies_in_mission = [p for p in self.mission if p in spies]

            sabotage_combinations = product((False, True), repeat=len(spies_in_mission))
            sabotage_combinations = [zip(spies_in_mission, sabotages) for sabotages in sabotage_combinations]
            actions = [Action(StateNames.SABOTAGE, tuple(sabotages), False) for sabotages in sabotage_combinations]

        return actions

    
    # Changes the game state object into a new state s' where s' = s(move)
    def make_move(self, action):
        num_players = len(self.determination)
        spies = [p for p in range(num_players) if self.determination[p]]

        if action.type == StateNames.SELECTION:
            self.state_name = StateNames.VOTING
            self.player = range(num_players)
            self.mission = action.value                         # Action is a list of player ids in the mission

        elif action.type == StateNames.VOTING:
            spies_in_mission = [p for p in self.mission if p in spies]
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

        elif action.type == StateNames.SABOTAGE:
            num_fails_required = Agent.fails_required[num_players][self.rnd]
            self.rnd += 1
            if action.partially_observable:
                num_sabotages = action.value[0]                 # Action has format (num_sabotages, list_of_players_in_mission)
            else:
                _, sabotages = zip(*action.value)               # Action has format [(s1, action1), (s2, action2), ...]
                num_sabotages = sum(sabotages)

            if num_sabotages < num_fails_required:
                self.missions_succeeded += 1

            if self.rnd >= 5:
                self.state_name = StateNames.TERMINAL
            else:
                self.state_name = StateNames.SELECTION
                self.leader = (self.leader + 1) % len(self.determination) 
                self.player = self.leader


    # Returns the reward for a player based on the current determination stored in the state
    def game_result(self, player):
        if self.determination[player]:  # player is a spy
            score = self.rnd - self.missions_succeeded  # number of fails
        else:
            score = self.missions_succeeded
        if score < 3:
            score = 0
        return score / 3        # reward from [0, 1, 4/3 5/3] depending on number of wins

    
    def get_game_state(self):
        return GameState(self.leader, self.player, self.state_name, self.rnd, self.missions_succeeded, 
            self.mission, self.num_selection_fails)