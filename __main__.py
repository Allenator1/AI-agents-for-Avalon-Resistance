from random_agent import RandomAgent
from MCTS.monte import Monte
from game import Game

agents = [Monte('monte'), 
        RandomAgent(name='r2'),  
        RandomAgent(name='r3'),  
        RandomAgent(name='r4'),  
        RandomAgent(name='r5')]


while True:
        game = Game(agents)
        game.play()
        print(game)


