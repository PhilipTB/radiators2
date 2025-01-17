import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
import numpy as np
from scipy.optimize import minimize
import time
import itertools
import pprint

#============================================================================
def load_table_into_dataframe(file_path, sheet_name, table_name):
    # Load the workbook using openpyxl
    print("Loading", file_path)
    wb = load_workbook(file_path, data_only=True)

    ws = wb[sheet_name]

    data = ws.tables[table_name]
    
    data_rows = []
    for row in ws[data.ref]:
        data_cols = []
        for cell in row:
            data_cols.append(cell.value)
        data_rows.append(data_cols)

    df = pd.DataFrame(data_rows[1:], columns=data_rows[0])

    print("Loaded", df.shape[0], "radiators")

    return df

#============================================================================
def create_test_rooms():
    test_rooms = [
        { 'name': 'lounge', 'room_temperature': 21.5, 'min_wattage': 4000 }, # was 1500
        { 'name': 'bed 1',  'room_temperature': 21.5, 'min_wattage':  500 },
        { 'name': 'bed 2',  'room_temperature': 21.5, 'min_wattage': 1000 },
        { 'name': 'bed 3',  'room_temperature': 21.5, 'min_wattage':  800 },
        { 'name': 'bed 4',  'room_temperature': 21.5, 'min_wattage': 1000 },
    ]

    return pd.DataFrame(test_rooms)

#============================================================================
def create_test_constraints():
    test_constraints = [
        { 'name': 'lounge', 'location': 'Loc 1', 'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK2x1000x600'},
        { 'name': 'lounge', 'location': 'Loc 2', 'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0},
        { 'name': 'lounge', 'location': 'Loc 3', 'Height': 600, 'Length':  600, 'Depth': 'K2', 'Labour Cost': 350.0},
        { 'name': 'lounge', 'location': 'Loc 4', 'Height': 600, 'Length':  600, 'Depth': 'K3', 'Labour Cost': 350.0},
        { 'name': 'bed 1',  'location': 'Loc 1', 'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost':  95.0,  'Existing Radiator': 'ModernxK1x800x600'},
        { 'name': 'bed 1',  'location': 'Loc 2', 'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0},
        { 'name': 'bed 2',  'location': 'Loc 1', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0,  'Existing Radiator': 'ModernxK2x1400x600'},
        { 'name': 'bed 3',  'location': 'Loc 1', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0,  'Existing Radiator': 'ModernxK1x1400x600'},
        { 'name': 'bed 4',  'location': 'Loc 1', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0,  'Existing Radiator': 'ModernxK1x1800x600'}
    ]

    return pd.DataFrame(test_constraints)

#=======================================================================================================
# Home
class Home:
    def __init__(self, rooms, radiator_constraints, radiator_database):
        self.rooms = rooms
        self.radiator_constraints = radiator_constraints
        self.radiator_database = radiator_database

    def room_names(self):
        return self.rooms['name'].tolist()
    
    def minimal_cost_radiators(self, flow_temperature):
        room_results = []

        for index, room_df in self.rooms.iterrows():
            room_results.append(self.minimal_cost_radiators_in_room(room_df, flow_temperature))
        
        total_cost = self.total_costs(room_results)

        print("Total cost before moves:", total_cost)

        self.move_replaced_radiators(flow_temperature, room_results)

        total_cost = self.total_costs(room_results)

        print("Total cost after moves:", total_cost)

        formatted_Results = self.convert_results_to_datafame(room_results)

        return formatted_Results

    def convert_results_to_datafame(self, room_results):
        formatted_results = []

        for room in room_results:
            for location_name, location in room['locations'].items():
                rad_status = None
                from_loc_desc = None
                print("Got here:", 'Existing' in location)
                pprint.pp(room['locations'])
                print(location)
                exit()
                if 'Existing' in location:
                    rad_status = location['Existing']
                    print("Blobby", rad_status)
                    if rad_status == 'Moved':
                        from_loc = location['From']
                        from_loc_desc = f"{from_loc['room_name']} {from_loc['location']}"

                formatted_result = {
                    'room_name': room['room_name'],
                    'location_name': location_name,
                    'radiator_name': location['Key'],
                    '£': location['£'],
                    'Labour Cost': location['Labour Cost'],
                    'Status': rad_status,
                    'From': from_loc_desc,
                }
                formatted_results.append(formatted_result)
        
        return pd.DataFrame(formatted_results)

    def minimal_cost_radiators_in_room(self, room_df, flow_temperature):
        room_name = room_df['name']
        location_constraints = self.radiator_constraints.loc[self.radiator_constraints['name'].eq(room_name)]
        room = Room(room_df, location_constraints, self.radiator_database)
        room_result = room.minimal_cost_radiators(flow_temperature)
        room_result['room_name'] = room_name
        room_result['room_temperature'] = room_df['room_temperature']
        return room_result
    
    def total_costs(self, room_results):
        return sum(room_result['cost'] for room_result in room_results)

    def extract_replaced_radiators(self, room_results):
        replaced_rads = []

        for room_result in room_results:
            if room_result['replaced_radiators']:
                replaced_rads += room_result['replaced_radiators']

        for replaced_rad in replaced_rads:
            rad = self.find_radiator(rad_db, replaced_rad['Key'])
            replaced_rad['specification'] = rad

        # replacement least valuable radiators first, leaving most for last
        replaced_rads.sort(key=lambda rad: rad['specification']['£'])

        return replaced_rads
    
    def move_replaced_radiators(self, flow_temperature, room_results):
        replaced_rads = self.extract_replaced_radiators(room_results)

        # look to replace new radiators starting with most valuable first
        new_radiators = self.find_new_radiators(room_results)

        for replacement_rad in replaced_rads:
            for new_radiator in new_radiators:
                room_temperature = new_radiator['room_temperature']
                replacement_watts = Home.wattage_at_flow_temperature(replacement_rad['specification'], room_temperature, flow_temperature)
                new_watts = Home.wattage_at_flow_temperature(new_radiator['radiator'], room_temperature, flow_temperature)
                if replacement_watts > new_watts:
                    location_constraint = self.find_constraint(new_radiator['room_name'], new_radiator['location_name'])
                    if self.radiator_fits(location_constraint, replacement_rad['specification']):
                        result_location = self.find_location_in_room_results(room_results, new_radiator['room_name'], new_radiator['location_name'])
                        result_location['Existing'] = 'Moved'
                        moved_key = replacement_rad['Key']
                        moved_rad_spec= self.find_radiator(self.radiator_database, moved_key)
                        result_location['From'] = replacement_rad 
                        result_location  |= moved_rad_spec
                        result_location['£'] = 0.0
                        result_location = self.find_location_in_room_results(room_results, new_radiator['room_name'], new_radiator['location_name'])
                        break

    def radiator_fits(self, location, radiator):
        height_ok = radiator['Height'] <= location['Height']
        length_ok = radiator['Length'] <= location['Length']
        return height_ok and length_ok
    
    @classmethod
    def wattage_at_flow_temperature(cls, rad, room_temperature, flow_temperature):
        return rad["W @ dt 50"]
        n = rad['N']
        watts_at_dt_50 = rad["W @ dt 50"]
        dt = flow_temperature - 2.5 - room_temperature
        w = watts_at_dt_50 * (dt / 50.0 ) ** n

        return w

    def find_constraint(self, room_name, location_name):
        rc = self.radiator_constraints
        return rc[(rc['name']==room_name) & (rc['location'] == location_name)].iloc[0]

    def find_location_in_room_results(self, room_results, room_name, location_name):
        return self.find_room_in_room_results(room_results, room_name)['locations'][location_name]
    
    def find_room_in_room_results(self, room_results, room_name):
        for room_result in room_results:
            if room_result['room_name'] == room_name:
                return room_result
    
    def find_radiator(self, rad_db, key):
        if key == None:
            return None

        return rad_db.loc[rad_db['Key'] == key].iloc[0]

    def find_existing_radiator(self, rad_db, key):
        existing_rad = self.find_radiator(rad_db, key)

        if existing_rad is None or existing_rad.shape[0] == 0: 
            return None

        return existing_rad
    
    def find_new_radiators(self, room_results):
        new_radiators = []
        for room in room_results:
            for location_name, location in room['locations'].items():
                pprint.pp(room)
                print("$"*100)
                exit()
                if location.get('Existing') == 'New':
                    room_name = room['room_name']
                    new_radiators.append(
                        {
                            'room_name': room_name,
                            'location_name': location_name,
                            'radiator': location,
                            'room_temperature': room['room_temperature']
                        }
                    )
        
        new_radiators.sort(reverse = True, key=lambda rad: rad['radiator']['£'])

        return new_radiators
#=======================================================================================================
# Room
class Room:
    def __init__(self, room, location_constraints, radiator_database):
        self.room = room
        self.location_constraints = location_constraints
        self.radiator_database = radiator_database
        
    def room_temperature(self): return self.attribute('room_temperature')
    def name(self):             return self.attribute('name')
    def min_wattage(self):      return self.attribute('min_wattage')
    
    def attribute(self, key):
        return self.room.to_dict()[key]
    
    # for speed, avoid repetition
    def pre_calculate_radiator_wattage_at_flow(self, flow_temperature):
        factor = (flow_temperature - 2.5 - self.room_temperature()) / 50.0
        self.radiator_database['w'] = self.radiator_database['W @ dt 50'] * factor ** self.radiator_database['N']    

    def minimal_cost_radiators(self, flow_temperature):
        t0 = time.time()

        self.pre_calculate_radiator_wattage_at_flow(flow_temperature)

        combos = self.all_combinations(flow_temperature)

        cost, rads = self.minimum_radiator_cost_combination(combos, self.location_constraints, self.min_wattage())
        
        print("Time taken", round(time.time() - t0, 2), "s for", len(combos), "combinations")

        replaced_rads = self.replaced_radiators(self.name(), rads, self.location_constraints)

        return {'cost': cost, 'locations': rads, 'replaced_radiators': replaced_rads}

    def minimum_radiator_cost_combination(self, combos, constraints, min_wattage):
        min_cost = 100000
        min_rads = None

        location_names = constraints['location'].tolist()

        labour_costs = constraints['Labour Cost'].tolist()

        for i, rads in enumerate(combos):
            cost, watts = self.cost_of_all_radiators(rads, labour_costs)
            
            if watts > min_wattage:
                if cost < min_cost:
                    min_cost = cost
                    min_rads = dict(zip(location_names, rads)) 
        
        return [min_cost, min_rads]

    def add_existing_radiators_to_possible_radiators(self, possible_rads, constraint, flow_temperature):
        if self.existing_radiator(constraint):
            existing_rad = self.find_radiator(constraint['Existing Radiator'])
            factor = (flow_temperature - 2.5 - self.room_temperature()) / 50.0
            watts_at_flow = existing_rad['W @ dt 50'] * factor ** existing_rad['N']
            return self.add_radiator(possible_rads, existing_rad['Key'], watts_at_flow, 0.0, 0.0)

        return possible_rads

    def find_radiator(self, key):
        return self.radiator_database.loc[self.radiator_database['Key'] == key].iloc[0]

    def existing_radiator(self, constraint):
        return 'Existing Radiator' in constraint and isinstance(constraint['Existing Radiator'], str)

    def add_radiator(self, rads, key, w, cost, labour_cost):
        new_rad = {
            'Key':          key,
            'w':            w,
            '£':            cost,
            'Labour Cost': labour_cost
        }
        new_rad_df = pd.DataFrame(new_rad, index=[0])

        return pd.concat([new_rad_df, rads], ignore_index=True)

    def add_no_radiator_to_possible_radiators(self, possible_rads, constraint):
        return self.add_radiator(possible_rads, None, 0.0, 0.0, 0.0)

    def all_combinations(self, flow_temperature):
        possible_rads_at_location = []

        for name, constraint in self.location_constraints.iterrows():
            rads = self.radiator_choices_at_location(constraint)

            rads['Labour Cost'] = 95.0
            
            rads = self.add_existing_radiators_to_possible_radiators(rads, constraint, flow_temperature)
            rads = self.add_no_radiator_to_possible_radiators(rads, constraint)

            rads['Total £'] = rads['£'] + rads['Labour Cost']
  
            possible_rads_at_location.append(rads.to_dict('records'))

        return list(itertools.product(*possible_rads_at_location))
    
    def radiator_choices_at_location(self, constraint):
        df_filt1 = self.radiator_database.loc[self.radiator_database['Length'] <= constraint['Length']]
        df_filt2 = df_filt1.loc[df_filt1['Height'] <= constraint['Height']]
        return df_filt2
    
    def cost_of_all_radiators(self, rads, labour_costs):
        costs = 0.0
        watts = 0.0
        for i, rad in enumerate(rads):
            costs += rad['Total £']
            watts += rad['w']

        return [costs, watts]

    def deprecated():
        rad_cost = rad["£"]
        labour_cost = labour_costs[i]

        if rad_cost > 0.0:
            costs += rad_cost + labour_cost

        if rad_cost != rad["Total £"]:
            print(rad_cost)
            pprint.pp(rad)
            exit()
        if not 'Existing Radiator' in rad:
            rad['Existing'] = 'New'

    def replaced_radiators(self, room_name, new_radiators, constraints):
        replaced_rads = []

        for i, location in constraints.iterrows():
            if 'Existing Radiator' in location:
                
                new_rad_key = new_radiators[location['location']]['Key']
                if self.radiator_changed(location['Existing Radiator'], new_rad_key):
                    replaced_rads.append(
                        {
                            'room_name': room_name,
                            'location': location['location'],
                            'Key':  location['Existing Radiator']
                        }
                    )

        return replaced_rads

    def radiator_changed(self, original, potential_new):
        if not isinstance(potential_new, str):
            return False

        if not isinstance(original, str):
            return False

        return original != potential_new

#============================================================================
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'
flow_temperatures = [55.0, 52.5, 50.0, 47.5, 45.0, 42.5, 40.0, 37.5, 35.0]

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

test_rooms = create_test_rooms()
test_constraints = create_test_constraints()
t1 = time.time()
home = Home(test_rooms, test_constraints, rad_db)
print("Flow temperature", 50.0)
results = home.minimal_cost_radiators(50.0)
print("="*100)

print("Time taken", time.time() - t1)
pprint.pp(results)
print("Totals:")
pprint.pp(results[['£', 'Labour Cost']].sum())
exit()
print("Flow temperature", 45.0)
results = home.minimal_cost_radiators(45.0)
print("="*100)
print("Time taken", time.time() - t1)
pprint.pp(results)
print("Totals:")
pprint.pp(results[['£', 'Labour Cost']].sum())

