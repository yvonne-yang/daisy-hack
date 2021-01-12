import random
import numpy as np
from typing import List, Dict, Optional, Tuple
import copy

from site_location import SiteLocationPlayer, Store, SiteLocationMap, euclidian_distances, attractiveness_allocation

class RandomPlayer(SiteLocationPlayer):
    """
    Player attempts to place the maximum stores, with each store type and
    position chosen randomly.
    """
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        stores = []
        for _ in range(self.config["max_stores_per_round"]):
            store_types = list(self.config["store_config"].keys())
            store = Store((random.randrange(0, slmap.size[0]),
                           random.randrange(0, slmap.size[1])),
                          random.choice(store_types))
            stores.append(store)
        self.stores_to_place = stores

class NothingPlayer(SiteLocationPlayer):
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        self.stores_to_place = []
        pass
        return

class MaxDensityPlayer(SiteLocationPlayer):

    def moving_density_calculator(self, slmap: SiteLocationMap,
    store_locations: Dict[int, List[Store]], current_funds: float, SM_GRID=(60,60)):
        '''
            Move in 60x60 grid and find element-wise sum of every 60x60 possible
        '''
        noise = slmap.population_distribution
        area = np.zeros(shape=(slmap.size[0] - SM_GRID[0], slmap.size[1] - SM_GRID[1])) ## all the area values we will store
        for i in range(slmap.size[0] - SM_GRID[0]):
            for j in range(slmap.size[1] - SM_GRID[1]):
                area[i, j] = np.sum(noise[i:i+SM_GRID[0], j:j+SM_GRID[1]]) ## element-wise

        return area
    
    """ 
    Player always selects the highest density location at least 50 units
    away from the nearest store. 


    Store type will always be the largest one it can afford.
    """
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        # Configurable minimum distance away to place store
        min_dist = 100
        # Check if it can buy any store at all
        if current_funds < store_conf['small']['capital_cost']:
            self.stores_to_place = []
            return
        # Choose largest store type possible
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'
        # Find highest population location that's at least 100m away from your location. Else, do nothing.
        all_stores_pos = []
        for player_store in store_locations[self.player_id]:
                all_stores_pos.append(player_store.pos)
        
        SM_GRID = (110,110)
        area = self.moving_density_calculator(slmap, store_locations, current_funds, SM_GRID)
        area_indices = tuple(map(tuple, np.dstack(np.unravel_index(np.argsort(area.ravel()), area.shape))[0][::-1]))
        for max_pos in area_indices:
            too_close = False
            actual_pos = (max_pos[0] + SM_GRID[0]/2 - 1, max_pos[1] + SM_GRID[1]/2 - 1)
            for pos in all_stores_pos:
                dist = np.sqrt(np.square(actual_pos[0]-pos[0]) + np.square(actual_pos[1]-pos[1]))
                if dist < min_dist:
                    too_close = True
            if not too_close:
                self.stores_to_place = [Store(actual_pos, store_type)]
                return

class CopycatPlayer(SiteLocationPlayer):
    """ 
    Player places an identical store at the location of a random opponent's store.
    """
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):

        self_stores_pos = []
        for store in store_locations[self.player_id]:
            self_stores_pos.append(store.pos)

        opp_store_locations = {k:v for (k,v) in store_locations.items() if k != self.player_id}
        opp_all_stores = []
        for player, player_stores in opp_store_locations.items():
            for player_store in player_stores:
                if player_store.pos not in self_stores_pos:
                    opp_all_stores.append(player_store)
        if not opp_all_stores:
            self.stores_to_place =  []
            return
        else:
            self.stores_to_place = [random.choice(opp_all_stores)]
            return
        
class AllocSamplePlayer(SiteLocationPlayer):
    """
    Agent samples locations and selects the highest allocating one using
    the allocation function. 
    """
    def place_stores(self, slmap: SiteLocationMap, 
                     store_locations: Dict[int, List[Store]],
                     current_funds: float):
        store_conf = self.config['store_config']
        num_rand = 150

        sample_pos = []
        for i in range(num_rand):
            x = random.randint(0, slmap.size[0])
            y = random.randint(0, slmap.size[1])
            sample_pos.append((x,y))
        # Choose largest store type possible:
        if current_funds >= store_conf['large']['capital_cost']:
            store_type = 'large'
        elif current_funds >= store_conf['medium']['capital_cost']:
            store_type = 'medium'
        else:
            store_type = 'small'

        best_score = 0
        best_pos = []
        for pos in sample_pos:
            sample_store = Store(pos, store_type)
            temp_store_locations = copy.deepcopy(store_locations)
            temp_store_locations[self.player_id].append(sample_store)
            sample_alloc = attractiveness_allocation(slmap, temp_store_locations, store_conf)
            sample_score = (sample_alloc[self.player_id] * slmap.population_distribution).sum()
            if sample_score > best_score:
                best_score = sample_score
                best_pos = [pos]
            elif sample_score == best_score:
                best_pos.append(pos)

        # max_alloc_positons = np.argwhere(alloc[self.player_id] == np.amax(alloc[self.player_id]))
        # pos = random.choice(max_alloc_positons)
        self.stores_to_place = [Store(random.choice(best_pos), store_type)]
        return
