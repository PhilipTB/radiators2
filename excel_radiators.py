
def load_dataframes_from_excel():
    rad_db = xl("RadiatorDatabase[#All]", headers=True)
    rooms = xl("Rooms[#All]", headers=True)
    max_sizes = xl("RoomEmittersMaxSizes", headers=True)
    return rad_db, rooms, max_sizes

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
                print("Adding room>>>>>>>>>>>>>>>>>>", room)
                room_to_rads[room['Room Name']] = Room(
                    room['Room Name'],
                    room['Temperature'],
                    room['Heat Loss']
                )

        return Home(room_to_rads)

    def room(self, name):
        print("Searching for", name)
        return self.rooms[name]
      

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
    def radiator_from_dataframe(cls, radiator_df):
        Radiator(
            radiator_df['Key'],
            radiator_df['Type'],
            radiator_df['Subtype'],
            radiator_df['Length'],
            radiator_df['Height'],
            radiator_df['N'],
            radiator_df['W @ dt 50'],
            radiator_df['£'],
        )

def add_radiator_locations_to_rooms(home, radiator_locations_df):
    
    for index, row in radiator_locations_df.iterrows():
        room_name = row['Room Name']
        room = home.room(room_name)
        print(room)
        existing_rad = Radiator.find(row['Existing Radiator'])
        room.add_potential_radiator_location(row['Length'], row['Height'], row['Type'], row['Max Subtype'], row['Status'], existing_rad)

class Home1:
    def __init__(self, rooms, radiators, rad_db):
        self.rooms = rooms
        self.rads = self.extract_radiators_to_rooms(rooms, radiators, rad_db)
    
    def extract_radiators_to_rooms(self, rooms, radiators, rad_db):
        room_to_rads = {}
        for index, room in rooms.iterrows():
            room_to_rads[room['Room Name']] = Room1(room, radiators[room['Room Name'] == radiators['Room Name']], rad_db)

        room_to_rads

class Room1:
    def __init__(self, room, radiators_spaces, rad_db):
        self.room = room
        self.radiators_spaces = radiators_spaces
        self.rad_db = rad_db
        self.find_existing_radiators_in_database()

    def find_existing_radiators_in_database(self):
        print(self.room['Room Name'])
        for index, radiators_space in self.radiators_spaces.iterrows():
            print('=========================================================')
            print(radiators_space)
            existing_rad_description = radiators_space['Existing Radiator']
            if existing_rad_description != 'None':
                rad = self.rad_db[existing_rad_description == rad_db['Key']].head(1)
                print("    rad lookup:", existing_rad_description)
                if not rad.empty:
                    flow_rate_column_map = {
                        'Existing': 65,
                        'Rad@55FT': 55,
                        'Rad@50FT': 50,
                        'Rad@45FT': 45,
                        'Rad@40FT': 40,
                        'Rad@35FT': 35
                    }

                    for col_name, flow_temp in flow_rate_column_map.items():
                        rad_ft_w = self.calculate_rad_wattage(flow_temp, self.room['Temperature'], rad)
                        print(col_name, flow_temp, rad_ft_w)
                    rad_40_w = self.calculate_rad_wattage(40.0, self.room['Temperature'], rad)
                    print('rad_40_w', rad_40_w)

    def calculate_rad_wattage(self, flow_t, room_t, radiator):
        radiator_w_at_50c = radiator['W @ dt 50']
        n = radiator['N']
        factor = pow((flow_t - room_t - 2.5)/50, 1.3)
        w = factor * radiator_w_at_50c
        return w.iloc[0]

#create output table
def create_results():
    assigned_rads = pd.DataFrame(columns=['Room Name', 'Length', 'Height', 'Existing', 'Rad@55FT', 'Rad@50FT', 'Rad@45FT', 'Rad@40FT', 'Rad@35FT'])

if False:

    home = Home1(rooms, max_sizes, rad_db)
    print('Created homes')
    # copy max_sizes input to assigned_rads output
    for index, row in max_sizes.iterrows():
        new_row = {'Room Name': row['Room Name'], 'Length': row['Length'],'Height': row['Height'], 'Existing': row['Existing Radiator']}
        assigned_rads = assigned_rads._append(new_row, ignore_index=True)

    for index, row in assigned_rads.iterrows():
        assigned_rads.at[index, 'Rad@55FT'] = index * 6

    rooms['Heat Loss'].sum()
    num_row= max_sizes.shape[0]
    num_row= assigned_rads.shape[0]

    assigned_rads

rad_db, rooms, max_sizes = load_dataframes_from_excel()

homex = Home.rooms_from_dataframe(rooms)

Radiator.database = rad_db

add_radiator_locations_to_rooms(homex, max_sizes)

create_results()

