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
        rads['Exists'] = False


        if 'Existing Radiator' in constraint:
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'£'] = 0.0
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'Labour Cost'] = 0.0
            rads.loc[rads['Key'] == constraint['Existing Radiator'],'Exists'] = True

        print("t" * 100)
        pprint.pp(rads.loc[rads['£'] < 50.0])

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
    pprint.pp(constraints)
    existing_radiators = [find_existing_radiator(rad_db, rad_location.get("Existing Radiator")) for rad_location in constraints.values()]

    for i, rads in enumerate(combos):
        cost, watts = cost_of_all_radiators(rads, labour_costs, room_temperature, flow_temperature)
        
        if watts > min_wattage:
            if cost < min_cost:
                min_cost = cost
                min_rads = dict(zip(location_names, rads)) 
    
    return [min_cost, min_rads]

#============================================================================
def minimum_room_radiator_costs(rad_db, room_name, constraints):
    combos = all_combinations(rad_db, constraints['location_constraints'])
    min_watts = constraints['min_wattage']
    room_temp = constraints['room_temperature']

    cost, rads = minimum_radiator_cost_combination(rad_db, combos, constraints['location_constraints'], room_temp, flow_temperature, min_watts)

    return { 'cost': cost, 'rads': rads }

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
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

rooms = {
    'lounge': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost': 95.0, 'Existing Radiator': 'ModernxK3x1800x600'},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0},
            'Loc3': {'Height': 600, 'Length': 600, 'Depth': 'K2', 'Labour Cost': 350.0},
            'Loc4': {'Height': 600, 'Length': 300, 'Depth': 'K3', 'Labour Cost': 350.0}
        },
        'room_temperature': 21.5,
        'min_wattage': 1500
    },
    'bed 1': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost': 95.0},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 95.0}
        },
        'room_temperature': 18,
        'min_wattage': 500
    },
    'bed 2': {
        'location_constraints': {
            'Loc1': {'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 95.0}
        },
        'room_temperature': 16,
        'min_wattage': 1000
    },
}  

flow_temperatures = [55.0, 52.5, 50.0, 47.5, 45.0, 42.5, 40.0, 37.5, 35.0]

t0 = time.time()
costs =  {flow_temperature: {} for flow_temperature in flow_temperatures}
print(costs)

for flow_temperature in flow_temperatures:
    for room_name, constraints in rooms.items():
        costs[flow_temperature][room_name] = minimum_room_radiator_costs(rad_db, room_name, constraints)

t1 = time.time()

pprint.pp(costs)

pprint.pp(summarise_costs_by_flow_temperature(costs))

print("Time taken", t1 - t0)
