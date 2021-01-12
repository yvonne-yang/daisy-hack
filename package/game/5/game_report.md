# Game Report
## Game configuration
allocation_function: attractiveness_allocation

map_size: (400, 400)

population: 1000000.0

n_rounds: 10

starting_cash: 70000

profit_per_customer: 0.5

max_stores_per_round: 2

place_stores_time_s: 10

ignore_player_exceptions: False

store_config: {'small': {'capital_cost': 10000.0, 'operating_cost': 1000.0, 'attractiveness': 25.0, 'attractiveness_constant': 1.0}, 'medium': {'capital_cost': 50000.0, 'operating_cost': 2000.0, 'attractiveness': 50.0, 'attractiveness_constant': 1.0}, 'large': {'capital_cost': 100000.0, 'operating_cost': 3000.0, 'attractiveness': 100.0, 'attractiveness_constant': 1.0}}

## Players
- AllocSamplePlayer-0
- OverthinkingPlayer-1
- MaxDensityPlayer-2
- AllocSamplePlayer-3
- AllocSamplePlayer-4
## Final Scores
AllocSamplePlayer-0: 337943.03116986755

OverthinkingPlayer-1: 361318.7161167882

MaxDensityPlayer-2: 39981.50127624099

AllocSamplePlayer-3: 130088.62614129926

AllocSamplePlayer-4: 326915.90723138815

# Winner!
OverthinkingPlayer-1
