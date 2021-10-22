from tqdm import tqdm
from random_agent import RandomAgent
from high_bfactor_with_annealing import Monte as Hbwa
from high_bfactor_no_annealing import Monte as Hbna
from low_bfactor_with_annealing import Monte as Lbwa
from low_bfactor_no_annealing import Monte as Lbna
from game import Game

agents = [Hbwa('hbwa'), 
        Hbna('hbna'),  
        Lbwa('lbwa'),  
        Lbna('lbna'),  
        RandomAgent(name='r5'),  
        RandomAgent(name='r6'),  
        RandomAgent(name='r7')]

tournament_stats = [{'spy_wins':0, 'spy_games':0, 'resistance_wins':0, 'resistance_games':0} for _ in range(len(agents))]

total_rounds = 500
game_as_resistance = 0
game_as_spy = 0
for i in tqdm(range(total_rounds)):
        game = Game(agents)
        game.play()
        #print(game)
        agents = game.agents
        spies = game.spies
        resistance = [i for i in range(len(agents)) if i not in spies]
        spies_won = False
        if game.missions_lost > 3:
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



