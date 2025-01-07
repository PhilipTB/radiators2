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
def radiator_choices_at_location(rad_db_df, constraint):
    df_filt1 = rad_db_df.loc[rad_db_df['Length'] <= constraint['Length']]
    df_filt2 = df_filt1.loc[df_filt1['Height'] <= constraint['Height']]
    return df_filt2

#============================================================================
def all_combinations(rad_db, constraints):
    possible_rads_at_location = []
    for name, constraint in constraints.items():
        rads = radiator_choices_at_location(rad_db, constraint)
        rads['Labour Cost'] = constraint['Labour Cost']
        rads['Potential Labour Cost'] = constraint['Labour Cost']
        rads['Exists'] = 'No'

        rads.loc[rads['Key'] == 'None','£'] = 0.0

        rads.loc[rads['Key'] == 'None','Labour Cost'] = 0.0

        if 'Existing Radiator' in constraint:
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'£'] = 0.0
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'Labour Cost'] = 0.0
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'Exists'] = 'Original'

        possible_rads_at_location.append(rads.to_dict('records'))

    return list(itertools.product(*possible_rads_at_location))

#============================================================================
def cost_of_all_radiators(rads, labour_costs, room_temperature, flow_temperature):
    costs = 0.0
    watts = 0.0
    for i, rad in enumerate(rads):
        rad_cost = rad["£"]
        labour_cost = labour_costs[i]

        if rad_cost > 0.0:
            costs += rad_cost + labour_cost

            if not 'Existing Radiator' in rad:
                rad['Existing'] = 'New'

        watts += wattage_at_flow_temperature(rad, room_temperature, flow_temperature)

    return [costs, watts]

#============================================================================
def wattage_at_flow_temperature(rad, room_temperature, flow_temperature):
    n = rad['N']
    watts_at_dt_50 = rad["W @ dt 50"]
    dt = flow_temperature - 2.5 - room_temperature
    w = watts_at_dt_50 * (dt / 50.0 ) ** n

    return w

#============================================================================
def find_radiator(rad_db, key):
    if key == None:
        return None

    return rad_db.loc[rad_db['Key'] == key].iloc[0]

#============================================================================
def find_existing_radiator(rad_db, key):
    existing_rad = find_radiator(rad_db, key)

    if existing_rad is None or existing_rad.shape[0] == 0: 
        return None

    return existing_rad

#============================================================================
def minimum_radiator_cost_combination(rad_db, combos, constraints, room_temperature, flow_temperature, min_wattage):
    min_cost = 100000
    min_rads = None
    location_names = constraints.keys()
    labour_costs = [rad_location["Labour Cost"] for rad_location in constraints.values()]

    for i, rads in enumerate(combos):
        cost, watts = cost_of_all_radiators(rads, labour_costs, room_temperature, flow_temperature)
        
        if watts > min_wattage:
            if cost < min_cost:
                min_cost = cost
                min_rads = dict(zip(location_names, rads)) 
    
    return [min_cost, min_rads]

#============================================================================
def replaced_radiators(room_name, new_radiators, constraints):
    replaced_rads = []

    for i, loc in enumerate(constraints['location_constraints'].values()):
        if 'Existing Radiator' in loc:
            if loc['Existing Radiator'] != list(new_radiators.values())[i]['Key']:
                replaced_rads.append(
                    {
                        'room_name': room_name,
                        'location': list(new_radiators.keys())[i],
                        'Key':  loc['Existing Radiator']
                    }
                )

    return replaced_rads

#============================================================================
def find_new_radiators(costs):
    new_radiators = []
    for room_name, room in costs.items():
        for location_name, room_radiator in room['rads'].items():
            if room_radiator.get('Existing') == 'New':
                new_radiators.append(
                    {
                        'room_name': room_name,
                        'location_name': location_name,
                        'radiator': room_radiator,
                        'room_temperature': room['room_temperature']
                    }
                )
    
    new_radiators.sort(reverse = True, key=lambda rad: rad['radiator']['£'])

    return new_radiators

#============================================================================
def move_replaced_radiators(flow_temperature, costs, replaced_rads):
    print("-"*100)
    print("Moving Radiators")

    for replaced_rad in replaced_rads:
        rad = find_radiator(rad_db, replaced_rad['Key'])
        replaced_rad['specification'] = rad

    # replacement least valuable radiators first, leaving most for last
    replaced_rads.sort(key=lambda rad: rad['specification']['£'])

    # look to replace new radiators starting with most valuable first
    new_radiators = find_new_radiators(costs)
    # print("Costs", costs)

    for replacement_rad in replaced_rads:
        for new_radiator in new_radiators:
            print("=" * 50)
            room_temperature = new_radiator['room_temperature']
            replacement_watts = wattage_at_flow_temperature(replacement_rad['specification'], room_temperature, flow_temperature)
            new_watts = wattage_at_flow_temperature(new_radiator['radiator'], room_temperature, flow_temperature)
            if replacement_watts > new_watts:
                location_constraint_x = costs[new_radiator['room_name']]['rads'][new_radiator['location_name']]
                location_constraint = roomsx[new_radiator['room_name']]['location_constraints'][new_radiator['location_name']]
                # print("Potential replacement with enough watts")
                # print("Replacement:", replacement_rad)
                # print("New:", new_radiator)
                print("in", new_radiator['room_name'],  new_radiator['location_name'])
                print("Location constraint:", location_constraint)
                print("Locaiton constraint x", location_constraint_x)
                if radiator_fits(location_constraint, replacement_rad['specification']):
                    print("LLLLL: Fits: Saving", new_radiator['radiator']['£'])
                    print("Replacement = ", replacement_rad['specification'])
                    costs[new_radiator['room_name']]['rads'][new_radiator['location_name']] = dict(costs[new_radiator['room_name']]['rads'][new_radiator['location_name']], **replacement_rad['specification'])
                    costs[new_radiator['room_name']]['rads'][new_radiator['location_name']]['£'] = 0
                    break
                else:
                    print("LLLLL: Doesnt fit")
                    print("Zog:", roomsx[new_radiator['room_name']]['location_constraints'][new_radiator['location_name']])

#============================================================================
def radiator_fits(location, radiator):
    height_ok = radiator['Height'] <= location['Height']
    length_ok = radiator['Length'] <= location['Length']
    print("    GGGG: height_ok", height_ok, "length_ok", length_ok)
    return height_ok and length_ok

#============================================================================
def minimum_room_radiator_costs(rad_db, room_name, constraints):
    combos = all_combinations(rad_db, constraints['location_constraints'])
    min_watts = constraints['min_wattage']
    room_temp = constraints['room_temperature']

    cost, rads = minimum_radiator_cost_combination(rad_db, combos, constraints['location_constraints'], room_temp, flow_temperature, min_watts)

    replaced_rads = replaced_radiators(room_name, rads, constraints)

    return { 'cost': cost, 'rads': rads, 'replaced_rads':  replaced_rads,
            'room_name': room_name, 'watts': min_watts, 'room_temperature': room_temp}

#============================================================================
def summarise_costs_by_flow_temperature(costs):
    costs_by_flow_temperature = {}
    for flow_temperature, rooms in costs.items():
        total_cost = 0.0
        for room_name, data in rooms.items():
            total_cost += data['cost']

        costs_by_flow_temperature[flow_temperature] = total_cost

    return costs_by_flow_temperature

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
        { 'name': 'lounge', 'location': 'Loc 1', 'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK3x1800x600'},
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
        for room_name in self.room_names():
            room_results.append(self.minimal_cost_radiators_in_room(room_name, flow_temperature))
        
        total_cost = self.total_costs(room_results)

        print("Total cost:", total_cost)

        return room_results

    def minimal_cost_radiators_in_room(self, room_name, flow_temperature):
        print("Finding mininum radiator cost for room", room_name, flow_temperature)
        room_choice = self.rooms.loc[self.rooms['name'].eq(room_name)].iloc[0]
        location_choices = self.radiator_constraints.loc[self.radiator_constraints['name'].eq(room_name)]
        room = Room(room_choice, location_choices, self.radiator_database)
        room_result = room.minimal_cost_radiators(flow_temperature)
        room_result['room_name'] = room_name
        print("T"*100)
        pprint.pp(room_result)
        return room_result
    
    def total_costs(self, room_results):
        return sum(room_result['cost'] for room_result in room_results)
    
    def move_replaced_radiators(self, flow_temperature, costs, replaced_rads):
        print("-"*100)
        print("Moving Radiators")

        for replaced_rad in replaced_rads:
            rad = find_radiator(rad_db, replaced_rad['Key'])
            replaced_rad['specification'] = rad

            # replacement least valuable radiators first, leaving most for last
            replaced_rads.sort(key=lambda rad: rad['specification']['£'])

            # look to replace new radiators starting with most valuable first
            new_radiators = find_new_radiators(costs)
            # print("Costs", costs)

            for replacement_rad in replaced_rads:
                for new_radiator in new_radiators:
                    print("=" * 50)
                    room_temperature = new_radiator['room_temperature']
                    replacement_watts = wattage_at_flow_temperature(replacement_rad['specification'], room_temperature, flow_temperature)
                    new_watts = wattage_at_flow_temperature(new_radiator['radiator'], room_temperature, flow_temperature)
                    if replacement_watts > new_watts:
                        location_constraint_x = costs[new_radiator['room_name']]['rads'][new_radiator['location_name']]
                        location_constraint = roomsx[new_radiator['room_name']]['location_constraints'][new_radiator['location_name']]
                        # print("Potential replacement with enough watts")
                        # print("Replacement:", replacement_rad)
                        # print("New:", new_radiator)
                        print("in", new_radiator['room_name'],  new_radiator['location_name'])
                        print("Location constraint:", location_constraint)
                        print("Locaiton constraint x", location_constraint_x)
                        if radiator_fits(location_constraint, replacement_rad['specification']):
                            print("LLLLL: Fits: Saving", new_radiator['radiator']['£'])
                            print("Replacement = ", replacement_rad['specification'])
                            costs[new_radiator['room_name']]['rads'][new_radiator['location_name']] = dict(costs[new_radiator['room_name']]['rads'][new_radiator['location_name']], **replacement_rad['specification'])
                            costs[new_radiator['room_name']]['rads'][new_radiator['location_name']]['£'] = 0
                            break
                        else:
                            print("LLLLL: Doesnt fit")
                            print("Zog:", roomsx[new_radiator['room_name']]['location_constraints'][new_radiator['location_name']])

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

    def minimal_cost_radiators(self, flow_temperature):
        combos = self.all_combinations()

        cost, rads = self.minimum_radiator_cost_combination(
                        combos, self.location_constraints,
                        self.room_temperature(), flow_temperature, self.min_wattage())
        
        replaced_rads = self.replaced_radiators(self.name(), rads, self.location_constraints)
        
        pprint.pp(cost)
        pprint.pp(rads)
        return {'cost': cost, 'locations': rads}

    def minimum_radiator_cost_combination(self, combos, constraints, room_temperature, flow_temperature, min_wattage):
        min_cost = 100000
        min_rads = None
        print("£"*100)
        pprint.pp(constraints)
        location_names = constraints['location'].tolist()

        labour_costs = constraints['Labour Cost'].tolist()

        for i, rads in enumerate(combos):
            cost, watts = cost_of_all_radiators(rads, labour_costs, room_temperature, flow_temperature)
            
            if watts > min_wattage:
                if cost < min_cost:
                    min_cost = cost
                    min_rads = dict(zip(location_names, rads)) 
        
        return [min_cost, min_rads]

    def all_combinations(self):
        possible_rads_at_location = []

        for name, constraint in self.location_constraints.iterrows():
            rads = self.radiator_choices_at_location(constraint)
            print("Got", rads.shape[0], "potential radiators at this location")
            rads['Labour Cost'] = constraint['Labour Cost']
            rads['Potential Labour Cost'] = constraint['Labour Cost']
            rads['Exists'] = 'No'

            rads.loc[rads['Key'] == 'None','£'] = 0.0

            rads.loc[rads['Key'] == 'None','Labour Cost'] = 0.0

            if 'Existing Radiator' in constraint:
                rads.loc[rads['Key'] == constraint['Existing Radiator'],'£'] = 0.0
                rads.loc[rads['Key'] == constraint['Existing Radiator'],'Labour Cost'] = 0.0
                rads.loc[rads['Key'] == constraint['Existing Radiator'],'Exists'] = 'Original'

            possible_rads_at_location.append(rads.to_dict('records'))

        return list(itertools.product(*possible_rads_at_location))
    
    def radiator_choices_at_location(self, constraint):
        df_filt1 = self.radiator_database.loc[self.radiator_database['Length'] <= constraint['Length']]
        df_filt2 = df_filt1.loc[df_filt1['Height'] <= constraint['Height']]
        return df_filt2
    
    def cost_of_all_radiators(self, rads, labour_costs, room_temperature, flow_temperature):
        costs = 0.0
        watts = 0.0
        for i, rad in enumerate(rads):
            rad_cost = rad["£"]
            labour_cost = labour_costs[i]

            if rad_cost > 0.0:
                costs += rad_cost + labour_cost

                if not 'Existing Radiator' in rad:
                    rad['Existing'] = 'New'

            watts += wattage_at_flow_temperature(rad, room_temperature, flow_temperature)

        return [costs, watts]
    
    def replaced_radiators(self, room_name, new_radiators, constraints):
        print("_"*100, "replaced_radiators")
        pprint.pp(room_name)
        pprint.pp(new_radiators)
        pprint.pp(constraints)
        replaced_rads = []

        for i, loc in enumerate(constraints.values()):
            print(">", loc)
            if 'Existing Radiator' in loc:
                if loc['Existing Radiator'] != list(new_radiators.values())[i]['Key']:
                    replaced_rads.append(
                        {
                            'room_name': room_name,
                            'location': list(new_radiators.keys())[i],
                            'Key':  loc['Existing Radiator']
                        }
                    )

        print("_"*100, "End: replaced_radiators")
        return replaced_rads

#============================================================================
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

roomsx = {
    'lounge': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost': 95.0, 'Existing Radiator': 'ModernxK3x1800x600'},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0},
            'Loc3': {'Height': 600, 'Length': 600, 'Depth': 'K2', 'Labour Cost': 350.0},
            'Loc4': {'Height': 600, 'Length': 600, 'Depth': 'K3', 'Labour Cost': 350.0}
        },
        'room_temperature': 21.5,
        'min_wattage': 1500
    },
    'bed 1': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost': 95.0,  'Existing Radiator': 'ModernxK1x800x600'},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0}
        },
        'room_temperature': 18,
        'min_wattage': 500
    },
    'bed 2': {
        'location_constraints': {
            'Loc1': {'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 95.0,  'Existing Radiator': 'ModernxK2x1400x600'}
        },
        'room_temperature': 16,
        'min_wattage': 1000
    },
    'bed 3': {
        'location_constraints': {
            'Loc1': {'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 95.0,  'Existing Radiator': 'ModernxK1x1400x600'}
        },
        'room_temperature': 16,
        'min_wattage': 800
    },
    'bed 4': {
        'location_constraints': {
            'Loc1': {'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 95.0,  'Existing Radiator': 'ModernxK1x1800x600'}
        },
        'room_temperature': 16,
        'min_wattage': 1000
    },
}  

test_rooms = create_test_rooms()
test_constraints = create_test_constraints()
home = Home(test_rooms, test_constraints, rad_db)
pprint.pp(home)
pprint.pp(home.room_names())
print(type(home.room_names()))
x = home.minimal_cost_radiators(50.0)
pprint.pp(x)
exit()
flow_temperatures = [55.0, 52.5, 50.0, 47.5, 45.0, 42.5, 40.0, 37.5, 35.0]
flow_temperatures = list(range(55, 32, -2))
flow_temperatures = [55.0, 50.0, 45.0, 40.0]
flow_temperatures = [50.0]

t0 = time.time()
costs =  {flow_temperature: {} for flow_temperature in flow_temperatures}
print(costs)


for flow_temperature in flow_temperatures:
    replaced_rads = []

    for room_name, constraints in roomsx.items():
        min_rads = minimum_room_radiator_costs(rad_db, room_name, constraints)
        costs[flow_temperature][room_name] = min_rads
        replaced_rads += min_rads['replaced_rads']

    move_replaced_radiators(flow_temperature, costs[flow_temperature], replaced_rads)

t1 = time.time()

pprint.pp(costs)

pprint.pp(summarise_costs_by_flow_temperature(costs))

print("Time taken", t1 - t0)


