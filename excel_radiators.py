rad_db=xl("RadiatorDatabase[#All]", headers=True)
rooms=xl("Rooms[#All]", headers=True)
max_sizes=xl("RoomEmittersMaxSizes", headers=True)

class Home:
    def __init__(self, rooms, radiators, rad_db):
        self.rooms = rooms
        self.rads = self.extract_radiators_to_rooms(rooms, radiators, rad_db)
    
    def extract_radiators_to_rooms(self, rooms, radiators, rad_db):
        room_to_rads = {}
        for index, room in rooms.iterrows():
            room_to_rads[room['Room Name']] = Room(room, radiators[room['Room Name'] == radiators['Room Name']], rad_db)

        room_to_rads

class Room:
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
assigned_rads = pd.DataFrame(columns=['Room Name', 'Length', 'Height', 'Existing', 'Rad@55FT', 'Rad@50FT', 'Rad@45FT', 'Rad@40FT', 'Rad@35FT'])

home = Home(rooms, max_sizes, rad_db)
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


