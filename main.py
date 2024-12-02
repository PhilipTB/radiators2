

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

