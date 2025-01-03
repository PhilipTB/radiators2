import pandas as pd
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

