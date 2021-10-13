
from tree import Tree
import pprint
a = Tree()
# tst = a.generate_tree("VOTE")
# pprint.pprint(tst)
# new = a.generate_mutated_tree(tst,"VOTE",0.8)
# pprint.pprint(new)

tree1 = {
    'fail_required': {
        '2sdf': False,
        'num_mission_fail': {
            '2asdf': False,
            '3ddd': True,
            'num_mission_success': {
                '2www': False,
                '3ff': False,
                'next_proposer': {
                    '1asdf': True,
                    '2ss': False
                }
            }
        }
    }
}


tree2 = {
        'this_proposer':{
            'fail_required':{
                'num_mission_fail':{
                    'leaf_a':True,
                    'leaf_b':True,
                    'rejected_votes':{
                        'leaf_a':True,
                        'leaf_b':False
                    }
                },
                'mission':{
                    'leaf_a':True,
                    'leaf_b':False
                }
            },
            'num_mission_success':{
                'leaf_a':True,
                'leaf_b':False,
                'next_proposer':{
                    'leaf_a':True,
                    'leaf_b':False,
                }
            }
        }
    }

x = a.generate_child_tree(tree1,tree2,0.0,[])
pprint.pprint(x)

# def mutate_tree(tree,mutate_rate):
#     for key in tree:
#         if random.random()<mutate_rate and type(tree[key])!= dict:
#             tree[key] = "changed"
#         elif  type(tree[key]) == dict:
#             tree[key] = mutate_tree(tree[key])
#     return tree


        # script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        # rel_path = "tree.json"
        # abs_file_path = os.path.join(script_dir, rel_path)
        # with open(abs_file_path) as json_file:
        #     self.data = json.load(json_file)
        #     self.thistree = self.tree.tree_from_json(self.data)
        # if self.is_spy():
        #     team = []
        #     for i in range(betrayals_required):
        #         team.append(self.spy_list[random.randrange(len(self.spy_list))])
        #     while len(team)<team_size:
        #         agent = random.randrange(team_size)
        #         if agent not in team:
        #             team.append(agent)
        #     return team
        # else:
        #     team = []
        #     while len(team)<team_size:
        #         agent = random.randrange(team_size)
        #         if agent not in team:
        #             team.append(agent)
        #     return team    
        # if self.is_spy:
        #     if np.intersect1d(self.spy_list,mission) != []:
        #         return True
        #     else:
        #         return False
        # else:
        #     return random.ramdom()<0.5