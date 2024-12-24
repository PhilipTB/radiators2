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
def evaluate_combination(i, optimal_rads, minimum_cost, rad1, rad2, required_w_at_50c):
    if rad1["£"] == 0.0 or  rad2["£"] == 0.0:
        return [optimal_rads, minimum_cost]
    
    cost = rad1["£"] + rad2["£"]
    watts = rad1["W @ dt 50"] + rad2["W @ dt 50"]

    if watts > required_w_at_50c:
        if minimum_cost == None or cost < minimum_cost:
            minimum_cost = cost
            optimal_rads = [rad1, rad2]

    return [optimal_rads, minimum_cost]

#============================================================================
def all_combinations(rad_db, constraints):
    possible_rads_at_location = []
    for name, constraint in constraints.items():
        rads = radiator_choices_at_location(rad_db, constraint)
        possible_rads_at_location.append(rads.to_dict('records'))

    return list(itertools.product(*possible_rads_at_location))

#============================================================================
def cost_of_all_radiators(rads, room_temperature, flow_temperature):
    costs = [rad["£"] for rad in rads]
    watts = 0.0
    for rad in rads:
        watts += wattage_at_flow(rad, room_temperature, flow_temperature)

    return [sum(costs), watts]

#============================================================================
def wattage_at_flow(rad, room_temperature, flow_temperature):
    n = rad['N']
    watts_at_dt_50 = rad["W @ dt 50"]
    dt = flow_temperature - 2.5 - room_temperature
    w = watts_at_dt_50 * (dt / 50.0 ) ** n
    return w

#============================================================================
def minimum_radiator_cost_combination(combos, location_names, room_temperature, flow_temperature, min_wattage):
    min_cost = 100000
    min_rads = None

    for rads in combos:
        cost, watts = cost_of_all_radiators(rads, room_temperature, flow_temperature)
        
        if watts > minimum_wattage:
            if cost < min_cost:
                min_cost = cost
                min_rads = dict(zip(location_names, rads)) 
    
    return [min_cost, min_rads]

#============================================================================
def minimum_room_radiator_costs(rad_db, room_name, constraints):
    combos = all_combinations(rad_db, constraints['location_constraints'])
    min_watts = constraints['min_wattage']
    room_temp = constraints['room_temperature']
    location_names = constraints['location_constraints'].keys()

    cost, rads = minimum_radiator_cost_combination(combos, location_names, room_temp, flow_temperature, min_watts)

    return { 'cost': cost, 'rads': rads }
#============================================================================
# Example usage
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

rooms = {
    'lounge': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2'},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3'},
            'Loc3': {'Height': 600, 'Length': 600, 'Depth': 'K2'},
            'Loc4': {'Height': 600, 'Length': 300, 'Depth': 'K3'}
        },
        'room_temperature': 21.5,
        'min_wattage': 1500
    },
    'bed 1': {
        'location_constraints': {
            'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2'},
            'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3'},
        },
        'room_temperature': 18,
        'min_wattage': 500
    }
}  

location_constraints = {
    'Loc1': {'Height': 600, 'Length': 2000, 'Depth': 'K2'},
    'Loc2': {'Height': 600, 'Length': 2000, 'Depth': 'K3'},
    'Loc3': {'Height': 600, 'Length': 600, 'Depth': 'K2'},
    'Loc4': {'Height': 600, 'Length': 300, 'Depth': 'K3'},
}

minimum_wattage = 1500.0
flow_temperatures = [55.0, 50.0, 45.0, 40.0, 35.0]
room_temperature = 21.0

t0 = time.time()
costs =  {flow_temperature: {} for flow_temperature in flow_temperatures}
print(costs)

for flow_temperature in flow_temperatures:
    for room_name, constraints in rooms.items():
        costs[flow_temperature][room_name] = minimum_room_radiator_costs(rad_db, room_name, constraints)
        
t1 = time.time()

pprint.pp(costs)

print("Time taken", t1 - t0)

