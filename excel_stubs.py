#=======================================================================================================
# Libraries

import pandas as pd
pd.options.mode.chained_assignment = None
from openpyxl import load_workbook
import numpy as np
from scipy.optimize import minimize
import time
import itertools
import pprint
import traceback


#=======================================================================================================
# Load Tables

def load_dataframes_from_excel():
    rad_db = xl("RadiatorDatabase[#All]", headers=True)
    rooms = xl("Rooms[#All]", headers=True)
    max_sizes = xl("RoomEmittersMaxSizes", headers=True)
    # labour_costs = xl("LabourCosts", headers=True)
    # flow_rate_scenario = xl("FlowRateScenario", headers=True)
    return rad_db, rooms, max_sizes

if (xl("CalculateRadiatorChoicesFlag")):
    rad_db, rooms, max_sizes = load_dataframes_from_excel()

    home = Home(rooms, max_sizes, rad_db)
else:
    print("Calculations turned off")


#=======================================================================================================
# Calculate Results Flow Temperature => Dataframe

radiator_choice = None

if (xl("CalculateRadiatorChoicesFlag")):
    try:
        flow_temperature = xl("A9")
        print("Starting minimum radiator calculation at flow temperature:", flow_temperature)
        radiator_choice = home.minimal_cost_radiators(flow_temperature)
    except Exception as e:
        print(traceback.format_exc())
    print("Calculations turned on")
    radiator_choice
else:
    print("Calculations turned off")
radiator_choice



