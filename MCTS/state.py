from agent import Agent
from itertools import combinations, product
import time

get_actions_time = {'selection':0, 'voting':0, 'sabotage':0}

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

        t1 = time.time()
        if self.state_name == StateNames.SELECTION:
            mission_size = Agent.mission_sizes[num_players][self.rnd]
            possible_missions = combinations(range(num_players), mission_size) 
            action_vals = [tuple(mission) for mission in possible_missions]
            actions = [self.generate_action(StateNames.SELECTION, val) for val in action_vals]
            get_actions_time['selection'] += time.time() - t1
        
        elif self.state_name == StateNames.VOTING:
            voting_combinations = product([False, True], repeat=num_players) 
            action_vals = [tuple(enumerate(votes)) for votes in voting_combinations]
            actions = [self.generate_action(StateNames.VOTING, val) for val in action_vals]
            get_actions_time['voting'] += time.time() - t1

        elif self.state_name == StateNames.SABOTAGE:
            spies = [p for p in range(num_players) if self.determination[p]]
            spies_in_mission = [p for p in self.mission if p in spies]

            sabotage_combinations = product((False, True), repeat=len(spies_in_mission))
            action_vals = [tuple(zip(spies_in_mission, sabotages)) for sabotages in sabotage_combinations]
            actions = [self.generate_action(StateNames.SABOTAGE, val) for val in action_vals]
            get_actions_time['sabotage'] += time.time() - t1
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
            num_fails_required = Agent.fails_required[num_players][self.rnd]
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