from typing import Tuple
from agent import Agent
import random
import numpy as np
from model import States
from tree import Tree
import json
import os
import pprint


class DecisionTreeAgent(Agent):        
    '''A sample implementation of a random agent in the game The Resistance'''

    def __init__(self, name='a'):
        '''
        Initialises the agent.
        Nothing to do here.
        '''
        self.name = name
        self.pretrained = {'PROPOSE': {'num_mission_fail': {'next_proposer': {'num_mission_success': {'rejected_votes': {'option_2': 'enough_spy_exposed', 'option_1': 'enough_spy_exposed'}, 'option_2': 'enough_spy_not_exposed', 'option_1': 'enough_spy_not_exposed'}, 'fail_required': {'this_proposer': {'option_2': 'enough_spy_exposed', 'option_1': 'enough_spy_exposed'}, 'option_1': 'no_spy'}}, 'option_2': 'no_spy', 'option_1': 'enough_spy_not_exposed'}}, 'VOTE': {'mission': {'this_proposer': {'next_proposer': {'option_2': True, 'option_1': False}, 'option_1': False}, 'rejected_votes': {'fail_required': {'num_mission_fail': {'option_3': False, 'num_mission_success': {'option_3': True, 'option_2': False, 'option_1': False}, 'option_1': True}, 'option_1': False}, 'option_1': True}}}, 'BETRAY': {'mission': {'num_mission_success': {'this_proposer': {'option_2': True, 'option_1': True}, 'fail_required': {'next_proposer': {'option_2': True, 'num_mission_fail': {'option_3': False, 'rejected_votes': {'option_2': False, 'option_1': False}, 'option_1': True}}, 'option_1': True}, 'option_1': True}, 'option_1': True}}}
        self.thistree = [self.pretrained['PROPOSE'],self.pretrained['VOTE'],self.pretrained['BETRAY']]

    def new_game(self, number_of_players, player_number, spy_list):
        '''
        initialises the game, informing the agent of the 
        number_of_players, the player_number (an id number for the agent in the game),
        and a list of agent indexes which are the spies, if the agent is a spy, or empty otherwise
        '''
        self.number_of_players = number_of_players
        self.player_number = player_number
        self.spy_list = spy_list
        self.states = States(self.is_spy(),player_number,number_of_players,spy_list)
        self.tree = Tree()

    def is_spy(self):
        '''
        returns True iff the agent is a spy
        '''
        return self.player_number in self.spy_list

    def propose_mission(self, team_size, betrayals_required = 1):
        '''
        expects a team_size list of distinct agents with id between 0 (inclusive) and number_of_players (exclusive)
        to be returned. 
        betrayals_required are the number of betrayals required for the mission to fail.
        '''
        self.states.update_stage("PROPOSE")
        self.states.update_proposer(self.player_number)

        if self.is_spy():
            team = []
            principle = self.tree.traverse_tree(self.thistree[0],self.states)
            if principle == 'enough_spy_not_exposed' or  principle == 'enough_spy_exposed':
                selected = 0
                while selected < betrayals_required and len(team)<team_size:
                    #select the most suspicious spy
                    if principle == 'enough_spy_not_exposed':
                        score = 1000
                        least_suspicious_spy = None
                        for spy in self.states.spys:
                            if self.states.expose[spy] < score:
                                score = self.states.expose[spy]
                                least_suspicious_spy = spy
                        team.append(least_suspicious_spy)
                    #select the least suspicious spy
                    if principle == 'enough_spy_exposed':
                        score = -1000
                        most_suspicious_spy = None
                        for spy in self.states.spys:
                            if self.states.expose[spy] > score:
                                score = self.states.expose[spy]
                                most_suspicious_spy = spy
                        team.append(most_suspicious_spy)
                    selected += 1
                #fill up the rest
                while len(team)<team_size:
                    next = random.randrange(0,self.states.num_player)
                    if next not in team:
                        team.append(next)
            elif principle == 'no_spy':
                while len(team)<team_size:
                    next = random.randrange(0,self.states.num_player)
                    if next not in team:
                        team.append(next)
            else:
                team = [0,1]
                print("error")
            return team
        else:
            team = []
            while len(team)<team_size:
                score = 1000
                most_trusted = None
                for player in range(self.states.num_player):
                    if self.states.distrust[player]<score and player not in team:
                        score = self.states.distrust[player]
                        most_trusted = player
                team.append(most_trusted)
            return team    

    def vote(self, mission, proposer):
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The function should return True if the vote is for the mission, and False if the vote is against the mission.
        '''
        self.states.update_stage("VOTE")
        self.states.update_current_mission(mission,proposer)
        return self.tree.traverse_tree(self.thistree[1],self.states)


    def vote_outcome(self, mission, proposer, votes):
        # print("\nvote outcome:\n","mission: ",mission,"\nproposer: ",proposer,"\nvotes: ",votes)
        self.states.update_vote(mission, proposer, votes)
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        votes is a dictionary mapping player indexes to Booleans (True if they voted for the mission, False otherwise).
        No return value is required or expected.
        '''
        pass

    def betray(self, mission, proposer):
        self.states.update_stage("BETRAY")
        self.states.update_current_mission(mission, proposer)
        if self.is_spy():
            return self.tree.traverse_tree(self.thistree[2],self.states)
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players, and include this agent.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        The method should return True if this agent chooses to betray the mission, and False otherwise. 
        By default, spies will betray 30% of the time. 
        '''

    def mission_outcome(self, mission, proposer, betrayals, mission_success):
        #print("\n\nmission outcome:\n","mission: ",mission,"\nproposer: ",proposer,"\nbetryals: ",betrayals, "\nmission success: ",mission_success,'\n-------------------------')
        self.states.update_mission(mission,proposer,betrayals,mission_success)
        '''
        mission is a list of agents to be sent on a mission. 
        The agents on the mission are distinct and indexed between 0 and number_of_players.
        proposer is an int between 0 and number_of_players and is the index of the player who proposed the mission.
        betrayals is the number of people on the mission who betrayed the mission, 
        and mission_success is True if there were not enough betrayals to cause the mission to fail, False otherwise.
        It iss not expected or required for this function to return anything.
        '''
        #nothing to do here
        pass

    def round_outcome(self, rounds_complete, missions_failed):
        #print("round outcome: ",rounds_complete, missions_failed)
        '''
        basic informative function, where the parameters indicate:
        rounds_complete, the number of rounds (0-5) that have been completed
        missions_failed, the numbe of missions (0-3) that have failed.
        '''
        #nothing to do here
        pass
    
    def game_outcome(self, spies_win, spies):
        #print("spy Wins: ",spies_win, spies)
        '''
        basic informative function, where the parameters indicate:
        spies_win, True iff the spies caused 3+ missions to fail
        spies, a list of the player indexes for the spies.
        '''
        #nothing to do here
        pass



