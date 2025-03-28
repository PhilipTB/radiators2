import time
import pandas as pd
import itertools
from radiator import Radiator

class Room:
    def __init__(self, room, location_constraints, radiator_database):
        self.room = room
        self.location_constraints = location_constraints
        self.radiator_database = radiator_database

    def minimal_cost_radiators(self, flow_temperature):
        t0 = time.time()
        self.pre_calculate_radiator_wattage_at_flow(flow_temperature)
        combos = self.all_combinations(flow_temperature)
        cost, rads = self.minimum_radiator_cost_combination(combos, self.location_constraints, self.room['Heat Loss'])

        if rads == None: # not enough capacity wthin constraints, just find max capacity whatever the cost
            cost, rads = self.maximal_radiator_wattage_combination(combos, self.location_constraints)

        print("Time taken", round(time.time() - t0, 2), "s for", len(combos), "combinations")
        replaced_rads = self.replaced_radiators(self.room['Room Name'], rads, self.location_constraints)
        return {'cost': cost, 'locations': rads, 'replaced_radiators': replaced_rads}

    def pre_calculate_radiator_wattage_at_flow(self, flow_temperature):
        factor = (flow_temperature - 2.5 - self.room['Room Temperature']) / 50.0
        self.radiator_database['w'] = self.radiator_database['W @ dt 50'] * factor ** self.radiator_database['N']

    def all_combinations(self, flow_temperature):
        possible_rads_at_location = []
        for _, constraint in self.location_constraints.iterrows():
            rads = Radiator.radiator_choices_at_location(self.radiator_database, constraint)

            if len(rads) <= 0:
                print("="*60)
                print("No radiators in database for room", self.room['Room Name'])
                print("Constraint: L=", constraint['Length'], "H=", constraint['Height'], "D=", constraint['Depth'],"T=", constraint['Type'])
                print("="*60)
                return []

            # Fix: Use .loc to assign values
            rads.loc[:, 'Labour Cost'] = constraint['Labour Cost']
            rads.loc[:, 'Status'] = 'New'
            
            rads = self.add_existing_radiators_to_possible_radiators(rads, constraint, flow_temperature)
            rads = self.add_no_radiator_to_possible_radiators(rads, constraint)
            
            rads.loc[:, 'Total £'] = rads['£'] + rads['Labour Cost']
            possible_rads_at_location.append(rads.to_dict('records'))
        
        return list(itertools.product(*possible_rads_at_location))
    
    def add_existing_radiators_to_possible_radiators(self, possible_rads, constraint, flow_temperature):
        if 'Existing Radiator' in constraint and isinstance(constraint['Existing Radiator'], str):
            existing_rad = self.find_radiator(constraint['Existing Radiator'])
            factor = (flow_temperature - 2.5 - self.room['Room Temperature']) / 50.0
            watts_at_flow = existing_rad['W @ dt 50'] * factor ** existing_rad['N']
            return self.add_radiator(possible_rads, existing_rad['Radiator Key'], watts_at_flow, 0.0, 0.0, 'Original')
        return possible_rads

    def add_no_radiator_to_possible_radiators(self, possible_rads, constraint):
        return self.add_radiator(possible_rads, None, 0.0, 0.0, 0.0, 'No radiator')

    def add_radiator(self, rads, radiator_key, w, cost, labour_cost, existing):
        new_rad = {'Radiator Key': radiator_key, 'w': w, '£': cost, 'Labour Cost': labour_cost, 'Status': existing}
        return pd.concat([pd.DataFrame(new_rad, index=[0]), rads], ignore_index=True)

    def minimum_radiator_cost_combination(self, combos, constraints, min_wattage):
        min_cost = float('inf')
        min_rads = None
        location_names = constraints['Location'].tolist()
        labour_costs = constraints['Labour Cost'].tolist()

        # speed critical, optimised loop
        for rads in combos:
            cost, watts = self.cost_of_all_radiators(rads, labour_costs)
            if watts > min_wattage:
                if cost < min_cost:
                    min_cost = cost
                    min_rads = dict(zip(location_names, rads))

        return min_cost, min_rads
    
    # if not enough space to provide enough heat, find maxzimum combination without wattage constraint
    def maximal_radiator_wattage_combination(self, combos, constraints):
        max_watts = -1
        max_rads = None
        location_names = constraints['Location'].tolist()
        labour_costs = constraints['Labour Cost'].tolist()

        # speed critical, optimised loop
        for rads in combos:
            cost, watts = self.cost_of_all_radiators(rads, labour_costs)
            if watts > max_watts:
                cost_at_max = cost
                max_watts = watts
                max_rads = dict(zip(location_names, rads))

        return cost_at_max, max_rads
    
    # speed critical, optimised loop   
    def cost_of_all_radiators(self, rads, labour_costs):
        costs = 0.0
        watts = 0.0

        for rad in rads:
            costs += rad['Total £']
            watts += rad['w']

        return [costs, watts]

    def replaced_radiators(self, room_name, new_radiators, constraints):
        return [
            {'room_name': room_name, 'Location': loc['Location'], 'Radiator Key': loc['Existing Radiator']}
            for _, loc in constraints.iterrows()
            if 'Existing Radiator' in loc and self.radiator_changed(loc['Existing Radiator'], new_radiators[loc['Location']]['Radiator Key'])
        ]

    def radiator_changed(self, original, potential_new):
        return isinstance(original, str) and isinstance(potential_new, str) and original != potential_new
    
    def find_radiator(self, radiator_key):
        return self.radiator_database.loc[self.radiator_database['Radiator Key'] == radiator_key].iloc[0]
