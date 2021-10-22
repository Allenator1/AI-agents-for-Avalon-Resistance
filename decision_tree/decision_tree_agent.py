from typing import Tuple
from agent import Agent
import random
import os
import json
import numpy as np
import pprint


class States():
    def __init__(self, spy:bool,my_id:int, num_player:int, spys:list):
        self.valid_stages = ['VOTE','PROPOSE','BETRAY']
        self.is_spy = spy
        self.spys = spys
        self.id = my_id
        #number of past succeed missions
        self.no_success = 0
        #number of past failed missions
        self.no_fail = 0
        #number of time vote have been rejected
        self.no_reject = 0
        #fail required matrix
        self.fails_required = {
            5:[1,1,1,1,1], \
            6:[1,1,1,1,1], \
            7:[1,1,1,2,1], \
            8:[1,1,1,2,1], \
            9:[1,1,1,2,1], \
            10:[1,1,1,2,1]
            }
        
        ## same index
        #what are the past proposed mission
        self.past_missions = []
        #who voted what for each mission
        self.past_votes = []
        #who is the proposer of that mission
        self.past_proposer = []
        #whether if that vote have succeed
        self.vote_succeed = []

        '''
        Expose rating of spy
        if is a spy the likely hood of each spy already exposed 
        if a player voted for a failed mission
        if a player participated in a failed mission
        if a player down voted a failed mission
        if a player proposed a failed mission
        if a player proposed a successufull mission
        '''
        self.expose = [0.5] * num_player
        '''
        set of values indicates the trust value towards a certain player
        if a player voted for a failed mission
        if a player participated in a failed mission
        if a player down voted a failed mission
        if a player proposed a failed mission
        if a player proposed a successufull mission
        '''
        self.distrust = [0.5] * num_player
        #current stage
        self.stage = None
        self.current_mission = None
        self.num_player = num_player
        self.next_proposer = 1
        self.this_proposer = 0
        self.current_required_fails = self.fails_required[self.num_player][len(self.past_missions)]
    
    #called at each call to agent 
    def update_stage(self,sta:str):
        if sta in self.valid_stages:
            self.stage = sta
        else:
            print("invalid stage")
            return None
    
    def update_current_mission(self,current_mission, proposer):
        self.current_mission = current_mission
        self.update_proposer(proposer)
    
    def update_proposer(self,proposer):
        self.this_proposer = proposer
        self.next_proposer = (proposer+1) % self.num_player

    def update_mission(self, mission, proposer, betryals, success):
        
        if betryals != 0:
            betryal_factor = betryals/len(mission)*2
        else:
            betryal_factor = 0.1
        if success:
            if self.is_spy:
                for player in mission:
                    if player in self.spys:
                        self.expose[player]-=0.1
            else:
                for player in mission:
                    self.distrust[player]-=0.1
            self.no_success +=1
        else:
            if self.is_spy:
                for player in mission:
                    if player in self.spys:
                        self.expose[player]+=betryal_factor
                if proposer in self.spys:
                    self.expose[proposer]+=betryal_factor
            else:
                for player in mission:
                    self.distrust[player]+=betryal_factor
                    self.distrust[proposer]+=betryal_factor
            self.no_fail +=1
        self.update_fail_required()
    
    def update_vote(self, mission, proposer,votes):
        self.past_proposer.append(proposer)
        self.past_missions.append(mission)
        self.past_votes.append(votes)
        self.update_proposer(proposer)
        if len(votes)*2 > self.num_player:
            self.vote_succeed.append(True)
            self.no_reject = 0
        else:
            self.vote_succeed.append(False)
            self.no_reject +=1
    
    def update_fail_required(self):
        if len(self.past_missions) <5:
            self.current_required_fails = self.fails_required[self.num_player][len(self.past_missions)]

class Tree():
    def __init__(self):
        #func dict
        self.funcs = {
            'this_proposer': self.this_proposer,
            'next_proposer': self.next_proposer,
            'mission': self.mission,
            'rejected_votes': self.rejected_votes,
            'fail_required': self.fail_required,
            'num_mission_fail': self.num_mission_fail,
            'num_mission_success': self.num_mission_success
        }
        #num of branch of each param
        self.num_of_branch = {
            'this_proposer': 2,
            'next_proposer': 2,
            'mission': 2,
            'rejected_votes': 2,
            'fail_required': 2,
            'num_mission_fail': 3,
            'num_mission_success': 3,
        }

        # spy propose choses enough or not enough and priortize
        # resistance propose with least suspicious level
        self.propose_option = ['enough_spy_not_exposed',
                              'no_spy', 'enough_spy_exposed']
        #list of params form vote/betray tree
        self.vote_betray_param = ['this_proposer', 'next_proposer', 'mission',
                                  'rejected_votes', 'fail_required', 'num_mission_fail', 'num_mission_success']
        #list of params form propose tree
        self.propose_param = ['this_proposer', 'next_proposer', 'rejected_votes',
                              'fail_required', 'num_mission_fail', 'num_mission_success']

    def this_proposer(self, state: States) -> int:
        if state.is_spy:
            # check if the next proposer is a spy or not
            if state.this_proposer in state.spys:
                return 0
            else:
                return 1
        else:
            # judge by trust
            if state.distrust[state.this_proposer] <= 0.5:
                return 0
            else:
                return 1

    def next_proposer(self, state: States) -> int:
        if state.is_spy:
            # check if the next proposer is a spy or not
            if state.next_proposer in state.spys:
                return 0
            else:
                return 1
        else:
            # judge by trust
            if state.distrust[state.next_proposer] <= 0.5:
                return 0
            else:
                return 1

    # who's on the mission
    def mission(self, state: States) -> int:
        #enough spy to sabotage mission?
        if state.is_spy:
            spys_on_team = 0
            for player in state.current_mission:
                if player in state.spys:
                    spys_on_team += 1
            if state.current_required_fails > spys_on_team:
                return 0
            else:
                return 1
        else:
            #judge by trust
            suspect_on_team = 0
            for player in state.current_mission:
                if state.distrust[player] > 0.5:
                    suspect_on_team += 1
            if state.current_required_fails > suspect_on_team:
                return 0
            else:
                return 1
        pass

    # number of rejected votes of this round
    def rejected_votes(self, state: States) -> int:
        if state.no_reject < 4:
            return 0
        else:
            return 1
        # check if it is 4

    # fail required of this round
    def fail_required(self, state: States) -> int:
        if state.current_required_fails > 1:
            return 0
        else:
            return 1

    #number of failed mission corrosponding to 0, 1 , or 2
    def num_mission_fail(self, state: States) -> int:
        if state.no_fail < 3:
            return state.no_fail
        else:
            return 0
    
    #number of successful mission corrosponding to 0, 1 , or 2
    def num_mission_success(self, state: States) -> int:
        if state.no_success < 3:
            return state.no_success
        else:
            return 0

    #generate decision from a given tree and game state object
    def traverse_tree(self, tree, state):
        index = self.funcs[list(tree.items())[0][0]](state)
        children = list(tree.items())[0][1]
        next_child = list(children.items())[index]
        dct = dict([next_child])
        if type(list(dct.items())[0][1]) == dict:
            result = self.traverse_tree(dct, state)
        else:
            result = next_child[1]
        return result
    
    #extract tree from jason 
    def tree_from_json(self, data):
        if isinstance(data, dict):
            return {key: self.tree_from_json(children) for key, children in data.items()}
        elif isinstance(data, list):
            return {idx: self.tree_from_json(children) for idx, children in enumerate(data, start=1)}
        else:
            return data

    # generates a decision tree for vote/betray stage
    def generate_vote_betray_tree(self, params, used_params, branching_factor, spliting_chance,split_decrease_rate):
        dct = {}
        splits = branching_factor
        while splits > 0:
            avaliable = [a for a in params +
                         used_params if a not in used_params]
            # terminate if by chance or if all params have been used
            if random.random() > spliting_chance or avaliable == []:
                dct["option_"+str(splits)] = random.random() < 0.5
            # keep splitting
            else:
                # select a
                this_param = random.choice(avaliable)
                used_params.append(this_param)
                dct[this_param] = self.generate_vote_betray_tree(
                    params, used_params, self.num_of_branch[this_param], spliting_chance*split_decrease_rate,split_decrease_rate)
            splits -= 1
        return dct

    #generates a propose phase decision tree
    def generate_propose_tree(self, params, used_params, branching_factor, spliting_chance,split_decrease_rate):
        dct = {}
        splits = branching_factor
        while splits > 0:
            avaliable = [a for a in params +
                         used_params if a not in used_params]
            # terminate if by chance or if all params have been used
            if random.random() > spliting_chance or avaliable == []:
                principle = random.choice(self.propose_option)
                #select 
                dct["option_"+str(splits)] = principle
            # keep splitting
            else:
                # select a
                this_param = random.choice(avaliable)
                used_params.append(this_param)
                dct[this_param] = self.generate_propose_tree(
                    params, used_params, self.num_of_branch[this_param], spliting_chance*split_decrease_rate,split_decrease_rate)
            splits -= 1
        return dct

    #a mutated tree will be generated from mutating the leaf nodes of a given tree.
    def generate_mutated_tree(self,tree,type_of_tree,mutate_rate):
        if type_of_tree == "VOTE" or type_of_tree == "BETRAY":
            for key in tree:
                if random.random()<mutate_rate and type(tree[key])!= dict:
                    tree[key] = not tree[key]
                elif  type(tree[key]) == dict:
                    tree[key] = self.generate_mutated_tree(tree[key],"VOTE",mutate_rate)
            return tree
        else:
            for key in tree:
                if random.random()<mutate_rate and type(tree[key])!= dict:
                    tree[key] = random.choice(self.propose_option)
                elif  type(tree[key]) == dict:
                    tree[key] = self.generate_mutated_tree(tree[key],"PROPOSE",mutate_rate)
            return tree

    #this algorithm reproduces a new decision tree by replacing a subtree of tree_a with a subtree of tree_b
    #select rate determines the chance of at which deepth the replace will take place
    def generate_child_tree(self,tree_a:dict, tree_b:dict, select_rate, existing_node:list):
        have_child = False
        for key in tree_a:
            if type(tree_a[key]) == dict:
                have_child = True
        if not have_child:
            select_rate = 1
        for key in tree_a:
            #keep searching
            if random.random() > select_rate:
                if type(tree_a[key]) == dict:
                    seen = [param for param in tree_a if type(tree_a[key]) == dict]
                    seen = list(np.append(seen,existing_node))
                    if type(tree_a[key]) != dict:
                        continue
                    if select_rate<1:
                        select_rate += 0.3
                    connect = self.generate_child_tree(tree_a[key],tree_b,select_rate,seen)
                    if connect != None and len(connect) == self.num_of_branch[key]:
                        tree_a[key] = connect
                        return tree_a     
            #try replace this one
            else:
                return self.node_trace_back(existing_node,tree_b)
        
    
    #once the location of concatination is determined, search for a muturaly exclusive subtree from tree_b
    def node_trace_back(self,existing,tree_b)->dict:
        for key in tree_b:
            if type(tree_b[key]) == dict:
                node_below = self.examine_nodes(tree_b[key],[])
            else:
                continue
            intersection = np.intersect1d(node_below,existing)
            #keep searching
            if intersection.size != 0:
                if type(tree_b[key]) == dict:
                    return self.node_trace_back(existing, tree_b[key])
            #concatnate this part of the tree
            else:
                return tree_b[key]
        return tree_b
        
    #return all key of nodes below the start node of a decision tree
    def examine_nodes(self,start_node,examined:list) -> list:
        for key in start_node:
            examined.append(key)
            if type(start_node[key]) == dict:
                examined = self.examine_nodes(start_node[key],examined)
        return examined
    
    #generate random decision tree of type vote, betray or propose
    def generate_tree(self,type):
        if type == "VOTE" or type == "BETRAY":
            initial = random.choice(self.vote_betray_param)
            tree = {
                initial: self.generate_vote_betray_tree(self.vote_betray_param, [initial], self.num_of_branch[initial], 0.9,0.7)
            }
            return tree
        else:
            initial = random.choice(self.propose_param)
            tree = {
                initial: self.generate_propose_tree(self.propose_param, [initial], self.num_of_branch[initial], 0.9,0.7)
            }
            return tree


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
                            if self.states.expose[spy] < score and spy not in team:
                                score = self.states.expose[spy]
                                least_suspicious_spy = spy
                        team.append(least_suspicious_spy)
                    #select the least suspicious spy
                    if principle == 'enough_spy_exposed':
                        score = -1000
                        most_suspicious_spy = None
                        for spy in self.states.spys:
                            if self.states.expose[spy] > score and spy not in team:
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



