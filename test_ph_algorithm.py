import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries
import numpy as np
from scipy.optimize import minimize

# Sample data for the DataFrame with installation cost
data = {
    'Location': ['Loc1', 'Loc2', 'Loc3', 'Loc4'],
    'Wattage': [500, 800, 600, 700],  # Example wattages for each radiator
    'Cost': [200, 350, 250, 300],  # Example costs for each radiator
    'Installation_Cost': [100, 150, 120, 130],  # Installation cost at each location
    'Height': [1.5, 1.2, 1.0, 1.3],  # Example heights in meters
    'Width': [0.5, 0.6, 0.4, 0.5],  # Example widths in meters
    'Depth': [0.3, 0.4, 0.35, 0.3]  # Example depths in meters
}

df = pd.DataFrame(data)

# Define the maximum size constraints for each location (Height, Width, Depth)
location_constraints = {
    'Loc1': {'Height': 1.5, 'Width': 0.6, 'Depth': 0.4},
    'Loc2': {'Height': 1.3, 'Width': 0.5, 'Depth': 0.4},
    'Loc3': {'Height': 1.2, 'Width': 0.5, 'Depth': 0.3},
    'Loc4': {'Height': 1.4, 'Width': 0.6, 'Depth': 0.4}
}

# Convert the dataframe and constraints into arrays
wattage = df['Wattage'].values
cost = df['Cost'].values
installation_cost = df['Installation_Cost'].values
height = df['Height'].values
width = df['Width'].values
depth = df['Depth'].values

print("wattage", wattage)
print("cost", cost)
print("installation_cost", installation_cost)
print("height", height)
print("width", width)
print("depth", depth)

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
    print("=" * 180)
    print(df)
    print("=" * 180)
    print("Filtered")
    print(df[df['Length'] > 2000])
    print("-" * 180)

    return df

def radiator_choices_at_location(rad_db_df, constraint):
    df_filt1 = rad_db_df.loc[rad_db_df['Length'] <= constraint['Length']]
    df_filt2 = df_filt1.loc[df_filt1['Height'] <= constraint['Height']]
    print("x"*125)
    print(df_filt2)
    print("y"*125)
    return df_filt2

def evaluate_combination(i, rad1, rad2):
    if i == 4:
        print("o"*175)
        print(rad1, type(rad1))
        print(rad2)


# Example usage
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)

location_constraints = {
    'Loc1': {'Height': 340, 'Length': 1000, 'Depth': 'K2'},
    'Loc2': {'Height': 600, 'Length': 1200, 'Depth': 'K3'},
}

possible_rads_at_location = {}
for name, constraints in location_constraints.items():
    print("SSSSSSSSSSSSSSSSSS", name)
    z = radiator_choices_at_location(rad_db, constraints)
    print("Got items", type(z), z.shape[0])
    possible_rads_at_location[name] = z

for name, possible_radiators in possible_rads_at_location.items():
    print(">" * 150)
    print(name, possible_radiators.shape[0])
    print(possible_radiators)

location_names = list(possible_rads_at_location.keys())
print("Zog Zog", location_names[0])
loc1_rads = possible_rads_at_location[location_names[0]]
loc2_rads = possible_rads_at_location[location_names[1]]

print("E"*150)
print(loc1_rads)
print("QQQQ", type(possible_rads_at_location))

x = 0
for i1, rad1 in loc1_rads.iterrows():
    for i2, rad2 in loc2_rads.iterrows():
        x += 1
        evaluate_combination(x, rad1, rad2)

print("Combinations", x)
exit()
# Display the first few rows of the DataFrame
if df is not None:
    print(df.head())


# Constraints for size check (each radiator must fit in the given dimensions)
def size_constraints(x):
    """Ensure the selected radiators do not exceed size constraints"""
    z = [
        (x[i] * height[i] <= location_constraints[df.loc[i, 'Location']]['Height']) for i in range(len(x))] + \
        [(x[i] * width[i] <= location_constraints[df.loc[i, 'Location']]['Width']) for i in range(len(x))] + \
        [(x[i] * depth[i] <= location_constraints[df.loc[i, 'Location']]['Depth']) for i in range(len(x))]
    print("size_constraints", z, "input", x)
    return z
        
def optimization_func(x):
    """Objective function: minimize total cost (radiator cost + installation cost)"""
    z = np.dot(cost + installation_cost, x) 
    print("optimization_func", z, "input", x, "cost", cost, "installation_cost", installation_cost)
    return z # Total cost is sum of cost and installation cost for selected radiators


# Constraints to ensure total wattage is greater than 1200
def total_wattage_constraint(x):
    z = np.dot(wattage, x) - 1200
    print("total_wattage_constraint", z, type(z), "input", x)
    return z  # The total wattage must be greater than or equal to 1200

def more_than_one_constraint(x):
    z = np.sum(x) >= 1
    print("more_than_one_constraint", z, type(x), "input", x)
    if np.sum(x) > 1:
        return 1.0
    else:
        return -1.0


# Boundaries for each radiator to be selected or not (binary)
bounds = [(0, 1)] * len(wattage)

# Initial guess (no radiators selected)
initial_guess = np.zeros(len(wattage))

# Set up the constraints and bounds for the optimization
constraints = [
    {'type': 'ineq', 'fun': total_wattage_constraint},  # Total wattage constraint
# {'type': 'ineq', 'fun': lambda x: np.sum(x) >= 1}  # Ensure at least one radiator is selected
    {'type': 'ineq', 'fun': more_than_one_constraint},
    {'type': 'ineq', 'fun': size_constraints}
]

# Minimize the total cost with constraints
result = minimize(optimization_func, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)

# Check if the optimization was successful
if result.success:
    selected_radiators = [i for i in range(len(result.x)) if result.x[i] > 0.5]  # Radiators selected are those with x > 0.5
    total_cost = result.fun
    selected_locations = df.loc[selected_radiators, 'Location'].values
    print("Selected Radiators:", selected_locations)
    print(f"Total Cost: ${total_cost:.2f}")
else:
    print("Optimization failed:", result.message)

