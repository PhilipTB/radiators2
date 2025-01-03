

#=======================================================================================================
def load_dataframes_from_excel():
    rad_db = xl("RadiatorDatabase[#All]", headers=True)
    rooms = xl("Rooms[#All]", headers=True)
    max_sizes = xl("RoomEmittersMaxSizes", headers=True)
    labour_costs = xl("LabourCosts", headers=True)
    flow_rate_scenario = xl("FlowRateScenario", headers=True)
    return rad_db, rooms, max_sizes, labour_costs, flow_rate_scenario

rad_db, rooms, max_sizes, labour_costs, flow_rate_scenario = load_dataframes_from_excel()

flow_rate_column_map = dict(zip(flow_rate_scenario.get("FlowRateDescription"), flow_rate_scenario.get("FlowRate")))

homex = Home.rooms_from_dataframe(rooms)

Radiator.database = rad_db

homex.add_radiator_locations_to_rooms(max_sizes)

homex.calculate_radiators(flow_rate_column_map)


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

# Constraints for size check (each radiator must fit in the given dimensions)
def size_constraints(x):
    """Ensure the selected radiators do not exceed size constraints"""
    return [
        (x[i] * height[i] <= location_constraints[df.loc[i, 'Location']]['Height']) for i in range(len(x))] + \
        [(x[i] * width[i] <= location_constraints[df.loc[i, 'Location']]['Width']) for i in range(len(x))] + \
        [(x[i] * depth[i] <= location_constraints[df.loc[i, 'Location']]['Depth']) for i in range(len(x))]
        
def optimization_func(x):
    """Objective function: minimize total cost (radiator cost + installation cost)"""
    return np.dot(cost + installation_cost, x)  # Total cost is sum of cost and installation cost for selected radiators


# Constraints to ensure total wattage is greater than 1200
def total_wattage_constraint(x):
    return np.dot(wattage, x) - 1200  # The total wattage must be greater than or equal to 1200

# Boundaries for each radiator to be selected or not (binary)
bounds = [(0, 1)] * len(wattage)

# Initial guess (no radiators selected)
initial_guess = np.zeros(len(wattage))

# Set up the constraints and bounds for the optimization
constraints = [
    {'type': 'ineq', 'fun': total_wattage_constraint},  # Total wattage constraint
    {'type': 'ineq', 'fun': lambda x: np.sum(x) >= 1}  # Ensure at least one radiator is selected
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


