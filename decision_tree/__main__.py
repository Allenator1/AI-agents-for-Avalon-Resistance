from random_agent import RandomAgent
from game import Game
from myagent import MyAgent

agents = [MyAgent(name='me'), 
        RandomAgent(name='r2'),  
        RandomAgent(name='r3'),  
        RandomAgent(name='r4'),  
        RandomAgent(name='r5'),  
        RandomAgent(name='r6'),  
        RandomAgent(name='r7')]

game = Game(agents)
game.play()
print(game)





