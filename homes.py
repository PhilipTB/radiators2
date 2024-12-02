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

      