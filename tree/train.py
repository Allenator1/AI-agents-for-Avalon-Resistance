from game import Game
from myagent import MyAgent
from tree import Tree
import random
import numpy as np
import pprint

def train():
    num_player = 7
    total_rounds = 10
    total_set = num_player*2
    winner = []
    interval = total_rounds/10
    #keep, random, child, mutate
    exploit_explore = [
        [0,14,0,0],
        [4,7,3,0],
        [4,6,3,1],
        [4,5,3,2],
        [5,4,2,3],
        [5,3,2,4],
        [5,2,2,5],
        [6,1,1,6],
        [6,0,2,6],
        [7,0,0,7]
    ]


    for i in range(total_rounds):
        iteration = i/interval 
        total_set = []
        total_set.extend(generate_random_trees(num_random_tree))
        total_set.extend(generate_next_generation(winner,num_child_tree,0.2))
        total_set.extend(generate_mutated_generation(winner,num_mutate_tree))
        train_game_per_round = 30
        
        while train_game_per_round > 0:
            #split in to two sets to play two games
            tree_set_1 = []
            tree_index_1 = []
            for i in range(num_player):
                x = random.randrange[len(total_set)]
                if total_set[x] not in tree_set_1:
                    tree_set_1.append(total_set[x])
                    tree_index_1.append(x)
            tree_set_2 = []
            tree_index_2 = []
            for i in range(num_player):
                x = random.randrange[len(total_set)]
                if total_set[x] not in tree_set_2 and total_set[x] not in tree_set_2:
                    tree_set_2.append(total_set[x])
                    tree_index_2.append(x)

            #records score of each game a set of tree have won
            score_of_each_tree_1 = [0]*7
            score_of_each_tree_2 = [0]*7

            winner_1,winning_tree_1 = play_game(tree_set_1)
            winner_2,winning_tree_2 = play_game(tree_set_2)

            for i in winning_tree_1:
                score_of_each_tree_1[i]+=1
            train_game_per_round -=1

            for i in winning_tree_2:
                score_of_each_tree_2[i]+=1
            train_game_per_round -=1
        all_scores = score_of_each_tree_1.extend(score_of_each_tree_2)
        all_index = tree_index_1.extend(tree_index_2)
        winner = []
        included = 0
        while included < winner_to_keep:
            high_score = 0
            for x in range(len(all_scores)):
                if all_scores[x] > high_score:
                    winner.append(all_index[x])
            included += 1
        

def play_game(trees):
    agent_to_index = {
        'Agent alpha':0,
        'Agent beta':1, 
        'Agent gamma':2,
        'Agent delta':3, 
        'Agent epslion':4,
        'Agent zeta':5, 
        'Agent eta':6
    }
    agents = [MyAgent(name='alpha',tree=trees[0]), 
        MyAgent(name='beta',tree=trees[1]),  
        MyAgent(name='gamma',tree=trees[2]),  
        MyAgent(name='delta',tree=trees[3]),  
        MyAgent(name='epslion',tree=trees[4]),  
        MyAgent(name='zeta',tree=trees[5]),  
        MyAgent(name='eta',tree=trees[6])]

    game = Game(agents)
    game.play()
    #print(game)
    agents = game.agents
    spies = game.spies
    resistance = [i for i in range(len(agents)) if i not in spies ]
    winning_trees = []
    winner = None
    if game.missions_lost>3:
        winner = "SPY"
        for spy in spies:
            winning_trees.append(agent_to_index[str(agents[spy])])
    else:
        for res in resistance:
            winning_trees.append(agent_to_index[str(agents[res])])
        winner = "RESISTANCE"
    return winner,winning_trees


def generate_random_trees(num):
    tree_obj = Tree()
    trees = [None]*num
    for i in range(len(trees)):
        trees[i] = [tree_obj.generate_tree("PROPOSE"),tree_obj.generate_tree("VOTE"),tree_obj.generate_tree("BETRAY")]
    return trees

#list of list of 3 trees select from random 
def generate_next_generation(winner,num,select_rate):
    tree_obj = Tree()
    used_pair = []
    trees = []
    while num > 0:
        found = False
        while not found:
            current_pair = [random.randrange(len(winner))]
            next = random.randrange(len(winner))
            if next != current_pair[0]:
                current_pair.append(next)
            reverse_pair = [current_pair[1],current_pair[0]]
            if current_pair not in used_pair and reverse_pair not in used_pair:
                trees.append(tree_obj.generate_child_tree(current_pair[0],current_pair[1]),select_rate,[])
            else:
                continue
        num -= 1
    return trees

def generate_mutated_generation(winner,num):
    pass

train()