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
    def __init__(self, state_name, rnd, missions_succeeded, player, mission=[], num_selection_fails=0):
        self.player = player       
        self.state_name = state_name                        # Defines the current game state (SELECTION, VOTING, SABOTAGE or TERMINAL)
        self.rnd = rnd
        self.missions_succeeded = missions_succeeded
        self.mission = mission                                
        self.num_selection_fails = num_selection_fails     
    
    def __eq__(self, other):
        self.state_name = other.state_name and \
        self.rnd == other.rnd and \
        self.missions_succeeded == other.missions_succeed and \
        self.num_selection_fails == other.num_selection_fails and \
        self.mission == other.mission


'''
A class used to define a perfect information representation of a game state in 
Avalon Resistance, including methods to get all moves and apply moves.
'''
class ResistanceState():
    def __init__(self, determination, game_state):
        self.player = game_state.player                                  
        self.determination = determination                    # Array of booleans where the player is spy if value is True
        self.state_name = game_state.state_name                # Defines the current game state (SELECTION, VOTING, SABOTAGE or TERMINAL)
        self.rnd = game_state.rnd
        self.missions_succeeded = game_state.missions_succeeded
        self.mission = game_state.mission                                
        self.num_selection_fails = game_state.num_selection_fails        


    # Returns all possible actions from this state => A(state)
    def get_moves(self):
        actions = []
        num_players = len(self.determination)

        if self.gamestate == StateNames.SELECTION:
            mission_size = Agent.mission_sizes[num_players][self.rnd - 1]
            possible_missions = combinations(range(num_players), mission_size) 
            actions = [{'type': StateNames.SELECTION, 'action': mission} for mission in possible_missions]
            
        elif self.gamestate == StateNames.VOTING:
            voting_combinations = product([False, True], repeat=num_players)    # e.g., [[False, True], [True, False], [False, False], [True, True]] for 2 players
            actions = [{'type': StateNames.VOTING, 'action': enumerate(votes)} for votes in voting_combinations]

        elif self.gamestate == StateNames.SABOTAGE:
            spies = [p for p in range(num_players) if self.determination[p]]
            spies_in_mission = [p for p in self.mission if p in spies]

            sabotage_combinations = product((False, True), repeat=spies_in_mission)
            sabotage_combinations = [zip(spies_in_mission, sabotages) for sabotages in sabotage_combinations]
            actions = [{'type': StateNames.SABOTAGE, 'action': sabotages} for sabotages in sabotage_combinations]

        return actions

    
    # Changes the game state object into a new state s' where s' = s(move)
    def make_move(self, move):
        num_players = len(self.determination)
        spies = [p for p in range(num_players) if self.determination[p]]

        if move['type'] == StateNames.SELECTION:
            self.gamestate = StateNames.VOTING
            self.player = range(num_players)
            self.mission = move['action']

        elif move['type'] == StateNames.VOTING:
            spies_in_mission = [p for p in self.mission if p in spies]
            player_votes = move['action']
            votes = [vote for _, vote in player_votes]
            num_votes_for = sum(votes)

            if num_votes_for * 2 > len(votes):
                if spies_in_mission:
                    self.gamestate = StateNames.SABOTAGE
                    self.player = spies_in_mission
                else:
                    self.gamestate = StateNames.SELECTION
                    self.player = (self.player + 1) % len(self.determination) # BOOKMARK #
                    self.rnd += 1
                    self.missions_succeeded += 1
                self.num_selection_fails = 0

            elif self.num_selection_fails < 5:
                self.gamestate = StateNames.SELECTION
                self.player = (self.player + 1) % len(self.determination) # BOOKMARK #
                self.num_selection_fails += 1

            else:
                self.gamestate = StateNames.SELECTION
                self.player = (self.player + 1) % len(self.determination) # BOOKMARK #
                self.num_selection_fails = 0
                self.rnd += 1

        elif move['type'] == StateNames.SABOTAGE:
            sabotages = move['action']
            num_fails_required = Agent.fails_required[num_players][self.rnd]
            self.rnd += 1

            if len(sabotages) < num_fails_required: # BOOKMARK #
                self.missions_succeeded += 1

            if self.rnd == 5:
                self.gamestate = StateNames.TERMINAL
            else:
                self.gamestate = StateNames.SELECTION


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
        return GameState(self.state_name, self.rnd, self.missions_succeeded, self.player, 
            self.mission, self.num_selection_fails)

    
    def __repr__(self):
        return f'STATE:{self.gamestate} rnd/successes/fails: ' + \
            f'{self.rnd}/{self.missions_succeeded}/{self.rnd - self.missions_succeeded}'