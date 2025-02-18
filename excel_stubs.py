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

if (xl("CalculateRadiatorChoicesFlag")):
    homex = home.minimal_cost_radiators(xl("A9"))
    print("Calculations turned on")
    homex
else:
    print("Calculations turned off")
homex



