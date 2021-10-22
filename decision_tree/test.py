from game import Game
from decision_tree_agent import DecisionTreeAgent
from random_agent import RandomAgent
agent_to_index = {
        'Agent alpha':0,
        'Agent beta':1, 
        'Agent gamma':2,
        'Agent delta':3, 
        'Agent epslion':4,
        'Agent zeta':5, 
        'Agent eta':6
    }

num_random = 7
num_decision = 0
for i in range(6):

    num_random -= 1
    num_decision += 1

    agname = ['alpha','beta','gamma','delta','epslion','zeta','eta']
    if num_random+num_decision != len(agname):
        print("incorrect number of agents, expected 7")
    agents = []
    i = 0
    while i < num_decision:
        agents.append(DecisionTreeAgent(name=agname[i]))
        i+=1
    while i < len(agname):
        agents.append(RandomAgent(name=agname[i]))
        i+=1

    spy_rounds_won = 0
    resistance_round_won = 0
    total_rounds = 5000
    game_as_resistance = 0
    game_as_spy = 0
    for i in range(total_rounds):
        game = Game(agents)
        game.play()
        agents = game.agents
        spies = game.spies
        id = None
        resistance = [i for i in range(len(agents)) if i not in spies ]
        for i in range(len(agents)):
            if str(agents[i]) == 'Agent alpha':
                id = i
        if id is not None:
            if i in resistance:
                game_as_resistance += 1
            elif i in spies:
                game_as_spy += 1
        winners = []
        winner = None
        if game.missions_lost>3:
            winner = "SPY"
            for spy in spies:
                winners.append(agent_to_index[str(agents[spy])])
                if "Agent alpha" == str(agents[spy]):
                    spy_rounds_won += 1
        else:
            for res in resistance:
                winners.append(agent_to_index[str(agents[res])])
                if "Agent alpha" == str(agents[res]):
                    resistance_round_won += 1
            winner = "RESISTANCE"
    print("Number of decision tree agents",num_decision)
    print("Number of random agents",num_random)
    print("win rate:{}%".format((spy_rounds_won+resistance_round_won)/total_rounds*100))
    print("win rate as resistance:{}%".format(resistance_round_won/game_as_resistance*100))
    print("win rate as spy:{}%".format(spy_rounds_won/game_as_spy*100))



