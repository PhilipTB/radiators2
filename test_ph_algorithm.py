import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
import numpy as np
from scipy.optimize import minimize
import time


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

def radiator_choices_at_location(rad_db_df, constraint):
    df_filt1 = rad_db_df.loc[rad_db_df['Length'] <= constraint['Length']]
    df_filt2 = df_filt1.loc[df_filt1['Height'] <= constraint['Height']]
    return df_filt2

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


# Example usage
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

location_constraints = {
    'Loc1': {'Height': 600, 'Length': 1000, 'Depth': 'K2'},
    'Loc2': {'Height': 600, 'Length': 1200, 'Depth': 'K3'},
}

required_w_at_50c = 3500

possible_rads_at_location = {}
for name, constraints in location_constraints.items():
    possible_rads_at_location[name] = radiator_choices_at_location(rad_db, constraints)

location_names = list(possible_rads_at_location.keys())
loc1_rads = possible_rads_at_location[location_names[0]]
loc2_rads = possible_rads_at_location[location_names[1]]

x = 0
optimal_rads = None
cost = None

t0 = time.time()

for i1, rad1 in loc1_rads.iterrows():
    for i2, rad2 in loc2_rads.iterrows():
        x += 1
        optimal_rads, cost = evaluate_combination(x, optimal_rads, cost, rad1, rad2, required_w_at_50c)

t1 = time.time()

print("Combinations", x)
print(optimal_rads, cost, "in", t1 - t0)

