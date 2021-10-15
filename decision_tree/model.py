

class States():
    def __init__(self, spy:bool,my_id:int, num_player:int, spys:list):
        self.valid_stages = ['VOTE','PROPOSE','BETRAY']
        self.is_spy = spy
        self.spys = spys
        self.id = my_id
        #number of past succeed missions
        self.no_success = 0
        #number of past failed missions
        self.no_fail = 0
        #number of time vote have been rejected
        self.no_reject = 0
        #fail required matrix
        self.fails_required = {
            5:[1,1,1,1,1], \
            6:[1,1,1,1,1], \
            7:[1,1,1,2,1], \
            8:[1,1,1,2,1], \
            9:[1,1,1,2,1], \
            10:[1,1,1,2,1]
            }
        
        ## same index
        #what are the past proposed mission
        self.past_missions = []
        #who voted what for each mission
        self.past_votes = []
        #who is the proposer of that mission
        self.past_proposer = []
        #whether if that vote have succeed
        self.vote_succeed = []

        '''
        Expose rating of spy
        if is a spy the likely hood of each spy already exposed 
        if a player voted for a failed mission
        if a player participated in a failed mission
        if a player down voted a failed mission
        if a player proposed a failed mission
        if a player proposed a successufull mission
        '''
        self.expose = [0.5] * num_player
        '''
        set of values indicates the trust value towards a certain player
        if a player voted for a failed mission
        if a player participated in a failed mission
        if a player down voted a failed mission
        if a player proposed a failed mission
        if a player proposed a successufull mission
        '''
        self.distrust = [0.5] * num_player
        #current stage
        self.stage = None
        self.current_mission = None
        self.num_player = num_player
        self.next_proposer = 1
        self.this_proposer = 0
        self.current_required_fails = self.fails_required[self.num_player][len(self.past_missions)]
    
    #called at each call to agent 
    def update_stage(self,sta:str):
        if sta in self.valid_stages:
            self.stage = sta
        else:
            print("invalid stage")
            return None
    
    def update_current_mission(self,current_mission, proposer):
        self.current_mission = current_mission
        self.update_proposer(proposer)
    
    def update_proposer(self,proposer):
        self.this_proposer = proposer
        self.next_proposer = (proposer+1) % self.num_player

    def update_mission(self, mission, proposer, betryals, success):
        
        if betryals != 0:
            betryal_factor = betryals/len(mission)*2
        else:
            betryal_factor = 0.1
        if success:
            if self.is_spy:
                for player in mission:
                    if player in self.spys:
                        self.expose[player]-=0.1
            else:
                for player in mission:
                    self.distrust[player]-=0.1
            self.no_success +=1
        else:
            if self.is_spy:
                for player in mission:
                    if player in self.spys:
                        self.expose[player]+=betryal_factor
                if proposer in self.spys:
                    self.expose[proposer]+=betryal_factor
            else:
                for player in mission:
                    self.distrust[player]+=betryal_factor
                    self.distrust[proposer]+=betryal_factor
            self.no_fail +=1
        self.update_fail_required()
    
    def update_vote(self, mission, proposer,votes):
        self.past_proposer.append(proposer)
        self.past_missions.append(mission)
        self.past_votes.append(votes)
        self.update_proposer(proposer)
        if len(votes)*2 > self.num_player:
            self.vote_succeed.append(True)
            self.no_reject = 0
        else:
            self.vote_succeed.append(False)
            self.no_reject +=1
    
    def update_fail_required(self):
        if len(self.past_missions) <5:
            self.current_required_fails = self.fails_required[self.num_player][len(self.past_missions)]