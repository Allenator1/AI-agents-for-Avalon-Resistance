from numpy.core.fromnumeric import trace
from game import Game
from myagent import MyAgent
from tree import Tree
from random_agent import RandomAgent
import random
import numpy as np
import pprint
import copy

def train():
    num_player = 7
    total_rounds = 10 
    total_set = num_player*2
    winner = []
    initial = []
    interval = int(total_rounds/10)
    #keep(for the next round), random, child, mutate
    exploit_explore = [
        [4,14,0,0],
        [4,7,3,0],
        [4,6,3,1],
        [5,5,3,2],
        [5,4,2,3],
        [5,3,2,4],
        [6,2,2,5],
        [7,1,1,6],
        [7,0,1,6],
        [2,0,0,7]
    ]


    for i in range(total_rounds):
        iteration = int(i/interval)
        if iteration > 9:
            print("invalid round")
            return None
        total_set = []
        total_set.extend(winner)
        next_ramdom = generate_random_trees(exploit_explore[iteration][1])
        total_set.extend(next_ramdom)
        next_gen = generate_next_generation(winner,exploit_explore[iteration][2],0)
        total_set.extend(next_gen)
        next_mutate = generate_mutated_generation(winner,exploit_explore[iteration][3])
        total_set.extend(next_mutate)
        train_game_per_round = 35
        score_of_each_tree = [0]*14
        if i == 0:
            initial =  random.choices(total_set,  k = 2)
        while train_game_per_round > 0:
            #split in to two sets to play two games
            tree_set_1 = []
            tree_index_1 = []
            used = []
            i1 = 0
            while i1 < num_player:
                x = random.randrange(len(total_set))
                if total_set[x] not in tree_set_1:
                    tree_set_1.append(total_set[x])
                    tree_index_1.append(x)
                    used.append(x)
                    i1 +=1
            tree_set_2 = []
            tree_index_2 = []
            for x in range(len(total_set)):
                if x not in used:
                    tree_set_2.append(total_set[x])
                    tree_index_2.append(x)

            #records score of each game a set of tree have won
            
            if len(tree_set_1)<7 or len(tree_set_2)<7:
                print("error")
            winner_1,winning_tree_1 = play_game(tree_set_1)
            winner_2,winning_tree_2 = play_game(tree_set_2)

            for i in winning_tree_1:
                score_of_each_tree[tree_index_1[i]]+=1

            for i in winning_tree_2:
                score_of_each_tree[tree_index_2[i]]+=1
            train_game_per_round -=1
        winner = []
        included = 0
        while included < exploit_explore[iteration][0]:
            high_score = 0
            current_winner = None
            for x in range(len(score_of_each_tree)):
                if score_of_each_tree[x] > high_score and total_set[x] not in winner:
                    current_winner = x
                    high_score = score_of_each_tree[x]
            winner.append(total_set[current_winner])
            included += 1
    return winner, initial
        

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
            current_pair = [winner[random.randrange(len(winner))]]
            next = None
            while next == None:
                next = random.randrange(len(winner))
                if winner[next] != current_pair[0]:
                    current_pair.append(winner[next])
                else: 
                    next = None
            reverse_pair = [current_pair[1],current_pair[0]]
            if current_pair not in used_pair and reverse_pair not in used_pair:
                mutate_pair = [copy.deepcopy(current_pair[0]),copy.deepcopy(current_pair[1])]
                set_of_tree = [None]*3
                for i in range(3):
                    child = tree_obj.generate_child_tree(mutate_pair[0][i],mutate_pair[1][i],select_rate,[])
                    if child != None:
                        set_of_tree[i] = child
                    else:
                        set_of_tree[i] = mutate_pair[1][i]
                trees.append(set_of_tree)
                found = True
            else:
                continue
        num -= 1
    return trees

def generate_mutated_generation(winner,num):
    tree_obj = Tree()
    used = []
    trees = []
    while num > 0:
        mutant = None
        while mutant == None:
            c = random.choice(winner)
            if c not in used and c is not None:
                mutant = copy.deepcopy(c)
        set_of_trees = [tree_obj.generate_mutated_tree(mutant[0],"PROPOSE",0.5),\
                        tree_obj.generate_mutated_tree(mutant[1],"VOTE",0.2),\
                        tree_obj.generate_mutated_tree(mutant[2],"BETRAY",0.2),] 
        trees.append(set_of_trees)
        num -=1
    return trees

    
def check_difference():
    trained,initial = train()
    test = copy.deepcopy(trained)
    test.extend(initial)
    #trained : 0,1 // initial 2,3// rest are random
    score_of_each_tree = [0]*7
    for i in range(40):
        winner,winning_tree = test_game(test)
        for i in winning_tree:
            score_of_each_tree[i]+=1
    return score_of_each_tree,trained
    

def test_game(trees):
    if len(trees)!= 4:
        return None,None
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
        RandomAgent(name='epslion'),  
        RandomAgent(name='zeta'),  
        RandomAgent(name='eta')]

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

#
def check_converge():
    total = 0
    current_best_score = 0
    converged_tree = None
    converge = 0
    for i in range(20):
        score,trained = check_difference()
        total = score[0] + score[1] - score[2] - score[3]
        print("trained tree win {} more games than random decision tree".format(total))
        if total > 0:
            converge += 1
        if total > 0:
            for i in range(2):
                if score[i] > current_best_score:
                    current_best_score = score[i]
                    converged_tree = trained[i]
    tree_dict = {
        'PROPOSE':converged_tree[0],
        'VOTE':converged_tree[1],
        'BETRAY':converged_tree[2]
    }
    print("tree converged: {}/20 times".format(converge))
    return converge, current_best_score, tree_dict


def generate_end_tree():
    total_converge = 0
    high_score = 0
    final_tree = None
    rnds = 10
    for i in range(rnds):
        converge, score, tree = check_converge()
        if score > high_score:
            final_tree = tree
            high_score = score
        total_converge += converge
    average_converge = total_converge/rnds
    print("tree converged: {}/20 times on average".format(average_converge))
    print("the best tree generated: ")
    print("|-------------------------------------------------------------------------------------------------")
    print(final_tree)
    print("|-------------------------------------------------------------------------------------------------")

generate_end_tree()