from itertools import combinations
from MCTS.node import Node, ActionMatrix
from MCTS.state import ResistanceState, ResistanceTree
from agent import Agent


def initialise_information_sets(player, player_is_spy, num_players):
    num_spies = Agent.spy_count[num_players]
    possible_spies = filter(lambda p: p != player, range(num_players))
    if player_is_spy:
        spy_configurations = combinations(possible_spies, num_spies - 1)
        [spies.append(player) for spies in spy_configurations]
    else:
        spy_configurations = combinations(possible_spies, num_spies)
    information_sets = {}
    for spies in spy_configurations:
        information_sets['team'] = [True if i in spies else False for i in range(num_players)]
        information_sets['probability'] = 1 / len(spy_configurations)          # Equal probability to choose a determination


def initialise_player_trees(num_players, root_player):
    monte_carlo_forest = {p:[] for p in range(num_players)}
    for p in range(num_players):  
        resistance_determinations = initialise_information_sets(p, False, num_players)
        monte_carlo_forest[p].append(resistance_determinations)
        if p != root_player:  
            spy_determinations = initialise_information_sets(p, True, num_players)
            monte_carlo_forest[p].append(spy_determinations)
    return monte_carlo_forest


def ISMCTS(rootstate, itermax, verbose=False):
    pass