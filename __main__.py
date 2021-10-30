from tqdm import tqdm
from random_agent import RandomAgent
from decision_tree.decision_tree_agent import DecisionTreeAgent
from game import Game


agents =       []

tournament_stats = [{'spy_wins':0, 'spy_games':0, 'resistance_wins':0, 'resistance_games':0} for _ in range(len(agents))]


def print_results():
        print('--------RESULTS----------')
        for a in range(len(agents)):
                s = str(agents[a]) + ':\n'
                if tournament_stats[a]["spy_games"]:
                        s += f'SPY WIN RATE = {tournament_stats[a]["spy_wins"] / tournament_stats[a]["spy_games"]} | ' 
                if tournament_stats[a]["resistance_games"]:
                        s += f'RESISTANCE WIN RATE = {tournament_stats[a]["resistance_wins"] / tournament_stats[a]["resistance_games"]} | ' 
                s += f'OVERALL WIN RATE = {(tournament_stats[a]["resistance_wins"] + tournament_stats[a]["spy_wins"]) / total_rounds}'
                s += '\n' + '-' * 100
                print(s)


total_rounds = 2000

for i in tqdm(range(total_rounds)):
        game = Game(agents)
        game.play()
        agents = game.agents
        spies = game.spies
        resistance = [i for i in range(len(agents)) if i not in spies]
        spies_won = False
        if game.missions_lost >= 3:
                spies_won = True
        for a in range(len(agents)):
                if a in spies:
                        tournament_stats[a]['spy_games'] += 1 
                if a in resistance:
                        tournament_stats[a]['resistance_games'] += 1
                if a in spies and spies_won:
                        tournament_stats[a]['spy_wins'] += 1 
                if a in resistance and not spies_won:
                        tournament_stats[a]['resistance_wins'] += 1 

print_results()



