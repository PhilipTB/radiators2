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
    return rad_db, rooms, max_sizes

rad_db, rooms, max_sizes = load_dataframes_from_excel()

home = Home(rooms, max_sizes, rad_db)

#=======================================================================================================
# Calculate Results Flow Temperature => Dataframe

home.minimal_cost_radiators(xl("A32"))

