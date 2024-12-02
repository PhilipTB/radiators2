#=======================================================================================================
# Home - a collection of Rooms
class Home:
    # rooms = { 'Room Name': Room(name. temp, heat_loss) }
    def __init__(self, room_to_rads):
        self.rooms = room_to_rads

    @classmethod
    def rooms_from_dataframe(cls, rooms_df):
        room_to_rads = {}
        for index, room in rooms_df.iterrows():
            name = room['Room Name']
            if name != None:
                room_to_rads[room['Room Name']] = Room(
                    room['Room Name'],
                    room['Temperature'],
                    room['Heat Loss']
                )

        return Home(room_to_rads)

    def room(self, name):
        return self.rooms[name]
    
    def calculate_radiators(self, flow_rate_columns):
        col_names = ['Room Name', 'Length', 'Height'] + list(flow_rate_columns.keys())
        assigned_rads = pd.DataFrame(columns=col_names)
        for room_name, room in self.rooms.items():
            w = room.calculate(flow_rate_columns.values())
            for ww in w:
                assigned_rads.loc[len(assigned_rads)] = [room_name] + ww

        return assigned_rads
    
    def add_radiator_locations_to_rooms(self, radiator_locations_df):
    
        for index, row in radiator_locations_df.iterrows():
            room_name = row['Room Name']
            room = self.room(room_name)
            existing_rad = Radiator.find(row['Existing Radiator'])
            room.add_potential_radiator_location(row['Length'], row['Height'], row['Type'], row['Max Subtype'], row['Status'], existing_rad)

      
#=======================================================================================================
# Room - A named room with set point temperature and a heat loss
#      - name needs to be unique
class Room:
    def __init__(self, name, temperature, heat_loss_w):
        self.name = name
        self.temperature = temperature
        self.heat_loss_w = heat_loss_w
        self.radiator_locations = []

    # length,width in mm, type='Modern'|'ModernGreen'|'Column'|'TowelRail',
    # max_sub_type='K1'|'K2'|3 etc. status='Replace&Remove'|'Available Space'|'Retain'
    def add_potential_radiator_location(self, length, height, type, max_sub_type, status, existing_radiator=None):
        location = RadiatorLocation(length, height, type, max_sub_type, status, existing_radiator)
        self.radiator_locations.append(location)

    def calculate(self, flow_temperatures):
        radiators_by_flow_temperature = {}

        for flow_temperature in flow_temperatures:
            radiators_by_flow_temperature[flow_temperature] = self.calculate_at_flow_temperature_formatted_result(flow_temperature)

        res =  self.flatten_results_by_flow_temperature(radiators_by_flow_temperature)
        return res
    
    # flatten multiple radiator locations x multiple flow temperatures for excel presentation
    def flatten_results_by_flow_temperature(self, radiators_by_flow_temperature):
        results = []
        rad_locs_by_ft = list(radiators_by_flow_temperature.values())

        for index, loc in enumerate(self.radiator_locations):
            r = [loc.length, loc.height]
            r.extend([el[index] for el in rad_locs_by_ft])
            results.append(r)

        return results

    # array of wattages for each radiator location
    def calculate_at_flow_temperature(self, flow_temperature):
        formatted_results_by_radiator_locations = []
        for loc in self.radiator_locations:
            watts = 0.0
            if loc.existing_radiator != None:
                w = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                watts = Room.formatted_result(loc.existing_radiator, "NA",50, w)

            formatted_results_by_radiator_locations.append(watts)

        return formatted_results_by_radiator_locations
    
    # array of wattages for each radiator location
    def calculate_at_flow_temperature_formatted_result(self, flow_temperature):
        formatted_results_by_radiator_locations = []
        for loc in self.radiator_locations:
            watts = 0.0
            if loc.existing_radiator != None:
                w = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                watts = Room.formatted_result(loc.existing_radiator, "NA",50, w)

            formatted_results_by_radiator_locations.append(watts)

        return formatted_results_by_radiator_locations
    
    def calculate_deprecated(self, flow_temperatures):
        loc_results = []
        for loc in self.radiator_locations:
            watts = []
            if loc.existing_radiator != None:
                for flow_temperature in flow_temperatures:
                    w = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                    f_w = Room.formatted_result(loc.existing_radiator, "NA",50, w)
                    watts.append(f_w)
        
            else:
                watts = [0.0] * len(flow_temperatures)

            loc_results.append([loc.length, loc.height] + watts)

        return loc_results
    
    @classmethod
    def formatted_result(cls, radiator, status, labour_cost, watts_at_flow_temperature):
        res  =  f"{radiator.name}:{status}-£{radiator.cost}-£{labour_cost}-{watts_at_flow_temperature:.0f}W"
        return res

#=======================================================================================================
# RadiatorLocation - space for radiators on wall, including potentially an existing radiator
#                  - multiple locations per room
class RadiatorLocation:
    def __init__(self, length, height, type, max_sub_type, status, existing_radiator):
        self.length = length
        self.height = height
        self.type = type
        self.max_sub_type = max_sub_type
        self.status = status
        self.existing_radiator = existing_radiator

#=======================================================================================================
class Radiator:
    database = None
    def __init__(self, name, type, sub_type, length, height, n, w_at_dt50, cost):
        self.name = name
        self.type = type
        self.sub_type = type
        self. length = length
        self.height = height
        self.n = n
        self.w_at_dt50 = w_at_dt50
        self.cost = cost

    def wattage(self, flow_temperature, room_temperature):
        factor = pow((flow_temperature - room_temperature - 2.5)/50, self.n)
        return factor * self.w_at_dt50
    
    @classmethod
    def find(cls, description):
        if not description:
            return None

        radiator_df = cls.database[description == cls.database['Key']].head(1)
        
        if radiator_df.empty:
            return None
        else:
            return cls.radiator_from_dataframe(radiator_df)

    @classmethod
    def radiator_from_dataframe(cls, rad_df):
        radiator_df = rad_df.squeeze()

        return Radiator(
            radiator_df['Key'],
            radiator_df['Type'],
            radiator_df['Subtype'],
            radiator_df['Length'],
            radiator_df['Height'],
            radiator_df['N'],
            radiator_df['W @ dt 50'],
            radiator_df['£'],
        )


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

