import random
import numpy as np
from typing import List, Dict, Optional, Tuple
import copy
from rl_solution import SmartAgent
from site_location import SiteLocationPlayer, Store, SiteLocationMap, euclidian_distances, attractiveness_allocation, \
    SiteLocationGame

SCORES = []
DEFAULT_MIN_DIST = 141
class DummyGame(SiteLocationGame):
    def __init__(self, config: Dict, player_classes: List[type], 
                 allocation_func):
        self.scores = [{}]
        
class NothingPlayer(SiteLocationPlayer):
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        self.stores_to_place = []
        pass


class OverthinkingPlayer(SiteLocationPlayer):
    '''
        Named to reflect how much I overthought about this.
        Learn to intentionally avoid players.
    '''
    def __init__(self, player_id, config):
        SiteLocationPlayer.__init__(self, player_id, config)
        self.roundNumber = 0
        self.encouragedPrice = int(config["store_config"]["large"]["capital_cost"] * 1.4)
        self.min_dist = 141
        self.stores_to_place = []
        


    def place_stores(self, slmap: SiteLocationMap, 
    store_locations: Dict[int, List[Store]], current_funds: float, agent):
        self.roundNumber = (self.roundNumber % self.config["n_rounds"]) + 1
        action = agent.agent_step(self.roundNumber) ## Default Starting State. You're on Round 0,
        store_conf = list(self.config["store_config"].keys())
        store_type = ""
        if action == 0:    
            ## Find dense points with no regard for competition
            self.most_dense(slmap, store_locations, current_funds, agent, two_buys=False, avoid_competition=False)
        elif action == 1:
            ## Find two dense points with no regard for competition
            self.most_dense(slmap, store_locations, current_funds, agent, two_buys=True, avoid_competition=False)
        elif action == 2:
            ## Throttle 2nd most important competition purposefully
            self.copy_cat(slmap, store_locations, current_funds)
        elif action == 3:
            ## Avoid competition while buying only one
            self.most_dense(slmap, store_locations, current_funds, agent, two_buys=False, avoid_competition=True)
        elif action == 4:
            ## Avoid competition while buying two
            self.most_dense(slmap, store_locations, current_funds, agent, two_buys=True, avoid_competition=True)
        self.roundNumber += 1
        self.encouragedPrice = agent.discount_factor * current_funds
        ## and you aint richer than anyone

    def moving_density_calculator(self, slmap: SiteLocationMap,
    store_locations: Dict[int, List[Store]], current_funds: float, SM_GRID=(60,60)):
        '''
            Description: Moving_UnagiDonCity_Calckers
            Move in 60x60 grid and sum of every possible 60x60 grid (The sum is stored in product array of 240x240)
            @Returns:  The product array of 240x240
        '''
        noise = slmap.population_distribution
        area = np.zeros(shape=(slmap.size[0] - SM_GRID[0], slmap.size[1] - SM_GRID[1])) ## all the area values we will store
        for i in range(slmap.size[0] - SM_GRID[0]):
            for j in range(slmap.size[1] - SM_GRID[1]):
                area[i, j] = np.sum(noise[i:i+SM_GRID[0], j:j+SM_GRID[1]]) ## element-wise

        return area
    
    def most_dense(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float, agent, two_buys=False, avoid_competition=False):
        store_conf = self.config['store_config']
        '''
            Select the most dense grids in the world, based on a subgrid.
            The subgrid gets smaller and smaller over time, as there becomes less space available
            and finding optimal points of profit becomes harder. This function does not avoid competition by default.
        '''

        # Configurable minimum distance away to place store
        min_dist = 141 
        self.min_dist = max(self.min_dist - 141/self.config["n_rounds"], 1)
        # Check if it can buy any store at all
        if current_funds < store_conf['small']['capital_cost']:
            return
        
        ## Validate that two buys is possible
        if two_buys:
            if self.encouragedPrice >= store_conf["large"]["capital_cost"]*2 and current_funds >= store_conf["large"]["capital_cost"]*2:
                store_type = ['large', 'large']
            elif self.encouragedPrice >= store_conf["large"]["capital_cost"]*2 and current_funds >= store_conf["medium"]["capital_cost"]*2:
                store_type = ['large', 'medium']
            elif self.encouragedPrice >= store_conf["large"]["capital_cost"]*2 and current_funds >= store_conf["small"]["capital_cost"]*2:
                store_type = ['large', 'small'] 
            elif self.encouragedPrice >= store_conf["medium"]["capital_cost"]*2 and current_funds >= store_conf["medium"]["capital_cost"]*2:
                store_type = ['medium', 'medium']
            elif self.encouragedPrice >= store_conf["medium"]["capital_cost"]*2 and current_funds >= store_conf["small"]["capital_cost"]*2:
                store_type = ['medium', 'small'] 
            elif self.encouragedPrice >= store_conf["small"]["capital_cost"]*2 and current_funds >= store_conf["small"]["capital_cost"]*2:
                store_type = ['small', 'small'] 
            else:
                two_buys = False
                agent.visited_sa_pair.append((agent.curr_state, 0)) ## 0 is action for buying one single store at a dense area
        
        ## On first round, choose one small store and one medium store
        if current_funds >= store_conf['small']['capital_cost'] + store_conf["medium"]["capital_cost"] and self.roundNumber == 1:
            store_type = ['medium', "small"]
        # Choose largest store type possible
        elif self.encouragedPrice >= store_conf["large"]["capital_cost"] and current_funds >= store_conf["large"]["capital_cost"]:
            store_type = 'large'
        elif self.encouragedPrice >= store_conf["medium"]["capital_cost"] and current_funds >= store_conf["medium"]["capital_cost"]:
            store_type = 'medium'
        elif self.encouragedPrice >= store_conf["small"]["capital_cost"] and current_funds >= store_conf["small"]["capital_cost"]:
            store_type = 'small'
            if self.roundNumber <= 6:
                return
        else:
            return
    

        ## To avoid competition, we place our new store as faraway as possible from anyone
        all_stores_pos = None
        opp_store_locations = {k:v for (k,v) in store_locations.items() if k != self.player_id}
        if avoid_competition == True:
                ## get longest element in dictionary
            longestIndex = list(opp_store_locations.keys())[0]
            longestValue = 0
            for player, player_stores in opp_store_locations.items():
                if len(player_stores) >= longestValue:
                    longestValue = len(player_stores)
                    longestIndex = player
            
            all_stores_pos = [player_store.pos for player_store in opp_store_locations[longestIndex]]
        else:
            all_stores_pos = [player_store.pos for player_store in store_locations[self.player_id]]
        
        counter = 0
        SM_GRID = (90, 90) ## decreases with roundNumber
        area = self.moving_density_calculator(slmap, store_locations, current_funds, SM_GRID)
        area_indices = tuple(map(tuple, np.dstack(np.unravel_index(np.argsort(area.ravel()), area.shape))[0][::-1]))
        for max_pos in area_indices:
            too_close = False
            actual_pos = (max_pos[0] + int(SM_GRID[0]/2) - 1, max_pos[1] + int(SM_GRID[1]/2) - 1)
            for pos in all_stores_pos:
                dist = np.sqrt(np.square(actual_pos[0]-pos[0]) + np.square(actual_pos[1]-pos[1]))
                if dist < self.min_dist:
                    too_close = True
                    break
            if not too_close:
                if isinstance(store_type, list):
                    self.stores_to_place.append(Store(actual_pos, store_type[counter]))
                    all_stores_pos.append(actual_pos)
                    ## what if we never get len of 2?
                    if len(self.stores_to_place) == 2:
                        return
                    counter += 1
                else: 
                    self.stores_to_place.append(Store(actual_pos, store_type))
                    return
        
        ## If everything is too close (lazy method, just pick thickest density point. This is either action 0 and action 1.
        if len(self.stores_to_place) == 0:
            agent.visited_sa_pair.pop()
            if two_buys:
                self.stores_to_place.extend([Store(area_indices[0], store_type[0]), Store(area_indices[1], store_type[1])])
                agent.visited_sa_pair.append((agent.curr_state, 1))
            else:
                self.stores_to_place.append(Store(area_indices[0], store_type[0]))
                agent.visited_sa_pair.append((agent.curr_state, 0))

        print(self.stores_to_place)

    def do_nothing(self):
        pass

    def copy_cat(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        '''
            Copy the opponent who has the most number of stores among your opponents.
        '''
        store_conf = self.config['store_config']
        store_type = 'small'
        pickOne = random.choice([True, False])
        if self.encouragedPrice >= store_conf["large"]["capital_cost"] and current_funds >= store_conf["large"]["capital_cost"]:
            store_type = 'large'
            if self.roundNumber >= 9:
                return
        elif self.encouragedPrice >= store_conf["medium"]["capital_cost"] and current_funds >= store_conf["medium"]["capital_cost"]:
            store_type = 'medium'
        elif self.encouragedPrice >= store_conf["small"]["capital_cost"] and current_funds >= store_conf["small"]["capital_cost"]:
            store_type = 'small'
        else:
            return

        self_stores_pos = []
        for store in store_locations[self.player_id]:
            self_stores_pos.append(store.pos)

        opp_store_locations = {k:v for (k,v) in store_locations.items() if k != self.player_id}
        opp_all_stores = []
        
        ## get longest element in dictionary
        longestIndex = list(opp_store_locations.keys())[0]
        longestValue = 0
        for player, player_stores in opp_store_locations.items():
            if len(player_stores) >= longestValue:
                longestValue = len(player_stores)
                longestIndex = player
        
        for player_store in opp_store_locations[longestIndex]:
            opp_all_stores.append(player_store)
        
        if not opp_all_stores:
            self.stores_to_place =  []
            return
        else:
            if pickOne:
                self.stores_to_place = [Store(random.choice(opp_all_stores).pos, store_type)]
            else:
                first_item = random.choice(opp_all_stores)
                opp_all_stores.pop(opp_all_stores.index(first_item))
                second_item = random.choice(opp_all_stores)
                ## Only pick the possible choice
                if store_conf[first_item.store_type]["capital_cost"] + store_conf[second_item.store_type]["capital_cost"] <= self.encouragedPrice:
                    self.stores_to_place = [first_item, second_item]    
                elif store_conf[first_item.store_type]["capital_cost"] <= self.encouragedPrice:
                    self.stores_to_place = [first_item]
                elif store_conf[second_item.store_type]["capital_cost"] <= self.encouragedPrice:
                    self.stores_to_place = [second_item]
                
        
    def valid_action(self, current_funds, config, action):
        pass


    def grid_search(self, test_params=[0.001, 0.005, 0.01, 0.015, 0.03, 0.1]):
        pass