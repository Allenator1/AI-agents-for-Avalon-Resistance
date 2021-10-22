import json
import random

from numpy.lib.function_base import select
from model import States
import numpy as np
import pprint


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

