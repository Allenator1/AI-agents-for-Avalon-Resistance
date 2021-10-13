from agent import Agent
from itertools import combinations, count, product


class Roles():
    SPY = 'SPY'
    NON_SPY = 'RESISTANCE'


class Gamestates():
    SELECTION = 'MISSION SELECTION'
    VOTING = 'VOTING'
    MISSION = 'MISSION SABOTAGE'
    TERMINAL = 'GAME END'


'''
A class used to define an Information Set Monte Carlo Tree for a single player in a single role
'''
class ResistanceTree():
    def __init__(self, player, player_role, determinations):
        self.player = player
        self.player_role = player_role
        self.determinations = determinations
        self.current_determination = None           # Array of booleans where the player is spy if value is True
        self.root_node = ResistanceState()
        self.current_node = self.root_node


'''
A class used to define a single game state in Avalon Resistance
'''
class ResistanceState():
    def __init__(self, determination, gamestate, rnd, missions_succeeded, player=-1):
        self.player = player            
        self.determination = determination          # Array of booleans where the player is spy if value is True
        self.gamestate = gamestate
        self.rnd = rnd
        self.missions_succeeded = missions_succeeded
        self.mission = []                           # for when gamestate = MISSION
        self.num_selection_fails = 0                # for when gamestate = VOTING/SELECTION


    def get_next_player(self):
        return (self.player + 1) % len(self.determination)


    # Returns all possible actions from this state => A(s)
    def get_moves(self):
        actions = []
        num_players = len(self.determination)

        if self.gamestate == Gamestates.SELECTION:
            mission_size = Agent.mission_sizes[num_players][self.rnd - 1]
            possible_missions = combinations(range(num_players), mission_size)  
            actions = [{'type': Gamestates.SELECTION, 'action': mission} for mission in possible_missions]
            
        elif self.gamestate == Gamestates.VOTING:
            voting_combinations = product([False, True], repeat=num_players)
            actions = [{'type': Gamestates.VOTING, 'action': enumerate(votes)} for votes in voting_combinations]

        elif self.gamestate == Gamestates.MISSION:
            spies = [p for p in range(num_players) if self.determination[p]]
            spies_in_mission = [p for p in self.mission if p in spies]
            if spies_in_mission:
                sabotage_combinations = product((False, True), repeat=spies_in_mission)
                sabotage_combinations = [zip(spies_in_mission, sabotages) for sabotages in sabotage_combinations]
                actions = [{'type': Gamestates.MISSION, 'action': sabotages} for sabotages in sabotage_combinations]
            else:
                actions = [{'type': Gamestates.MISSION, 'action': None}]

        return actions

    
    # Changes the game state object into a new state s' where s' = s(move)
    def make_move(self, move):
        num_players = len(self.determination)

        if move['type'] == Gamestates.SELECTION:
            self.mission = move['action']
            self.gamestate = Gamestates.VOTING
            self.player = -1    # Environmental player

        elif move['type'] == Gamestates.VOTING:
            player_votes = move['action']
            votes = [vote for _, vote in player_votes]
            num_votes_for = sum(votes)
            if num_votes_for * 2 > len(votes):
                self.gamestate = Gamestates.MISSION
                self.player = -1
                self.num_selection_fails = 0
            elif self.num_selection_fails < 5:
                self.gamestate = Gamestates.SELECTION
                self.player = (self.player + 1) % num_players
                self.num_selection_fails += 1
            else:
                self.gamestate = Gamestates.SELECTION
                self.player = (self.player + 1) % num_players
                self.num_selection_fails = 0
                self.rnd += 1

        elif move['type'] == Gamestates.MISSION:
            sabotages = move['action']
            num_fails_required = Agent.fails_required[num_players][self.rnd]
            self.rnd += 1

            if len(sabotages) < num_fails_required:
                self.missions_succeeded += 1

            if self.rnd == 5:
                self.gamestate = Gamestates.TERMINAL
            else:
                self.gamestate = Gamestates.SELECTION

        
    def __repr__(self):
        return f'STATE:{self.gamestate} rnd/successes/fails: ' + \
            f'{self.rnd}/{self.missions_succeeded}/{self.rnd - self.missions_succeeded}'


    # Returns the reward for a player based on the current determination stored in the state
    def game_result(self, player):
        if self.determination[player]:  # player is a spy
            score = self.rnd - self.missions_succeeded
        else:
            score = self.missions_succeeded
        if score < 3:
            score = 0
        return score / 3        # reward => [0, 5/3] 