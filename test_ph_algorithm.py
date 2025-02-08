import pandas as pd
pd.options.mode.chained_assignment = None
from openpyxl import load_workbook
import numpy as np
from scipy.optimize import minimize
from radiator import Radiator
from home import Home
from room import Room
import time
import itertools
import pprint

#============================================================================
def load_table_into_dataframe(file_path, sheet_name, table_name):
    print("Loading", file_path)
    wb = load_workbook(file_path, data_only=True)
    ws = wb[sheet_name]
    data = ws.tables[table_name]
    
    # Load data directly into DataFrame
    data_rows = [[cell.value for cell in row] for row in ws[data.ref]]
    df = pd.DataFrame(data_rows[1:], columns=data_rows[0])
    
    print("Loaded", df.shape[0], "radiators")
    return df

#============================================================================
def create_test_rooms():
    test_rooms = [
        {'Room Name': 'lounge', 'Room Temperature': 21.5, 'min_wattage': 4000},
        {'Room Name': 'bed 1',  'Room Temperature': 21.5, 'min_wattage': 500},
        {'Room Name': 'bed 2',  'Room Temperature': 21.5, 'min_wattage': 1000},
        {'Room Name': 'bed 3',  'Room Temperature': 21.5, 'min_wattage': 800},
        {'Room Name': 'bed 4',  'Room Temperature': 21.5, 'min_wattage': 500},
    ]
    return pd.DataFrame(test_rooms)

#============================================================================
def create_test_constraints():
    test_constraints = [
        {'Room Name': 'lounge', 'Location': 'Loc 1', 'Type': 'Modern', 'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK2x1800x600'},
        {'Room Name': 'lounge', 'Location': 'Loc 2', 'Type': 'Modern', 'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0, 'Existing Radiator': None},
        {'Room Name': 'lounge', 'Location': 'Loc 3', 'Type': 'Modern', 'Height': 600, 'Length':  600, 'Depth': 'K2', 'Labour Cost': 350.0, 'Existing Radiator': None},
        {'Room Name': 'lounge', 'Location': 'Loc 4', 'Type': 'Modern', 'Height': 600, 'Length':  600, 'Depth': 'K3', 'Labour Cost': 350.0, 'Existing Radiator': None},
        {'Room Name': 'bed 1',  'Location': 'Loc 1', 'Type': 'Modern', 'Height': 600, 'Length': 2000, 'Depth': 'K2', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK1x1000x600'},
        {'Room Name': 'bed 1',  'Location': 'Loc 2', 'Type': 'Modern', 'Height': 600, 'Length': 2000, 'Depth': 'K3', 'Labour Cost': 350.0, 'Existing Radiator': None},
        {'Room Name': 'bed 2',  'Location': 'Loc 1', 'Type': 'Modern', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK2x1400x600'},
        {'Room Name': 'bed 3',  'Location': 'Loc 1', 'Type': 'Modern', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK1x1400x600'},
        {'Room Name': 'bed 4',  'Location': 'Loc 1', 'Type': 'Modern', 'Height': 900, 'Length': 2000, 'Depth': 'K3', 'Labour Cost':  95.0, 'Existing Radiator': 'ModernxK1x1800x600'}
    ]
    return pd.DataFrame(test_constraints)

#============================================================================
file_path = 'Radiator Database.xlsx'
sheet_name = 'RadiatorDatabase'
table_name = 'RadiatorDatabase'
flow_temperatures = [55.0, 52.5, 50.0, 47.5, 45.0, 42.5, 40.0, 37.5, 35.0]

rad_db = load_table_into_dataframe(file_path, sheet_name, table_name)
test_rooms = create_test_rooms()
test_constraints = create_test_constraints()

home = Home(test_rooms, test_constraints, rad_db)
for flow_temperature in [50.0, 40.0, 35.0]:
    t1 = time.time()
    print("Flow temperature", flow_temperature)
    results = home.minimal_cost_radiators(flow_temperature)
    print("=" * 100)
    print("Time taken", time.time() - t1)
    pprint.pprint(results)
    print("Totals:")
    pprint.pprint(results[['£', 'Labour Cost']].sum())