### Decision tree agent
## Structure
```
decision_tree_agent.py                   ---gamplay---
myagent.py                               ---training---
model.py                                 ---state---
train.py                                 ---training---          
tree.py                                  ---tree_representation---
```
**Tree.py**
- Class used for representing, generating and traversing decision trees for game agent of "the resisitance"
---------------------------------------------
**tree generation**
- ***generate_vote_betray_tree***, ***generate_propose_tree***
    - generates random decision tree of the two types
- ***generate_mutated_tree***
    - generate mutated version of the argument 
- ***generate_child_tree***
    - generate offspring of the two arguments
---------------------------------------------
**tree traversal**
- returns an action with respect to the given tree and state
- ***this proposer***
    - checks if this proposer is a spy or not
    - resistance judge by trust value 
- ***next proposer***
    - checks if next proposer is a spy or not
    - resistance judge by trust value 
- ***mission***
    - checks if there is enough spy to sabotage the mission.
    - resistance judge by trust value 
- ***rejected_votes***
    - check if there is 4 rejeted proposals before this round
- ***fail_required***
    - check if the number of file required is greater than 1
- ***num_mission_fail***
    - the number of mission failed in the past
- ***num_mission_success***
    - the number of mission succeed in the past

//
**myagent.py**
- Used for training purpose 
- Have decision tree as __init__ parameter 
---------------------------------------------
- ***new_game***
    - initialises game state object
    - initialises tree object
- ***propose_mission***
    - updates proposer and stage in the state object
    - selects a principle based on the given decision tree and the current state object
    **spy actions**
    - *enough spy exposed* selects enough spy on the proposed team and prioritises spies that are most suspicious in the current state
    - *enough spy not exposed* selects enough spy on the proposed team and prioritises spies that are least suspicious in the current state
    - *no_spy* do not select spy 
    **resistance actions**
    - select team with the least suspicious players 
- ***vote***
    - updates mission and stage in the state object
    - return decision based on the given decision tree and the current state object
- ***vote_outcome***
    - updates vote outcome in the state object
- ***betray***
    - updates mission and stage in the state object
    - if self is a spy, return decision based on the given decision tree and the current state object
- ***mission_outcome***
    - updates mission in the state object

//
**model.py**
- Object representation of the game state
- involves simple heuristic of player identity/likelyhood of exposure(spy)
---------------------------------------------
- ***update_stage***
    - updates stage in the state object
- ***update_current_mission***
    - updates current mission in the state object
- ***update_proposer***
    - updates proposer in the state object
- ***update_mission***
    - updates archived mission in the state object
- ***update_vote***
    - updates vote outcome in the state object
- ***update_fail_required***
    - updates the number of fail required for this round in the state object

//
**train.py**
- Validates the effectiveness of the evolutionary decision tree approach 
- generats a relatively strong decision tree for tournament play
---------------------------------------------
- ***train***
    - Host finite iteration of evolution 
    - A new population will be generated at each iteration with propotion indicated by *exploit_explore* 
    - Each iteration will consist of finite rounds of 7 player resistance game.
    - Each round will have two set of 7 players and players will cross over between the two games at each round
    - samples form the winning generation and initial generation are returned
- ***play_game***
    - Self-play between 7 agents 