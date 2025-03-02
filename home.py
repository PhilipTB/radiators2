import pandas as pd
from radiator import Radiator
from room import Room

class Home:
    def __init__(self, rooms, radiator_constraints, radiator_database):
        self.rooms = self.clean_and_check_room_df(rooms)
        self.radiator_constraints = radiator_constraints
        self.radiator_database = radiator_database
        self.add_radiator_depth_mm()

    def minimal_cost_radiators(self, flow_temperature):
        room_results = [self.minimal_cost_radiators_in_room(room, flow_temperature) for _, room in self.rooms.iterrows()]
        
        total_cost = self.total_costs(room_results)
        print("Total cost before moves:", total_cost)

        self.move_replaced_radiators(flow_temperature, room_results)

        total_cost = self.total_costs(room_results)
        print("Total cost after moves:", total_cost)

        return self.convert_results_to_dataframe(room_results)
    
    def clean_and_check_room_df(self, rooms):
        return rooms.drop(rooms[rooms['Heat Loss'] == 0.0].index)

    def add_radiator_depth_mm(self):
        self.radiator_database['Depth_mm'] = self.radiator_database.apply(lambda row: Radiator.radiator_depth_mm(row.Depth), axis = 1)

    def convert_results_to_dataframe(self, room_results):
        formatted_results = []
        for room in room_results:
            for location_name, location in room['locations'].items():
                location_constraint = self.find_location_constraint(room['room_name'], location_name).iloc[0]
                existing_rad_name = location_constraint['Existing Radiator']
                rad_status = self.radiator_change_status(existing_rad_name, location['Radiator Key'], location)

                formatted_result = {
                    'Room Name': room['room_name'],
                    'Location name': location_name,
                    'Originally': existing_rad_name,
                    'Proposed Radiator': location['Radiator Key'],
                    '£': location['£'],
                    'Labour Cost': location['Labour Cost'],
                    'Status': rad_status,
                    'Watts': location['w']
                }
                formatted_results.append(formatted_result)
        
        return pd.DataFrame(formatted_results)

    def radiator_change_status(self, original_name, new_name, location):
        if 'Status' in location and location['Status'] == 'Moved':
            return f"Moved:{location['From']['room_name']}:{location['From']['Location']}"
        if new_name is None and original_name is not None:
            return 'Removed'
        if original_name == new_name:
            return 'Original' if original_name is not None else ''
        return 'Replaced'

    def find_location_constraint(self, room_name, location_name):
        return self.radiator_constraints[(self.radiator_constraints['Room Name'] == room_name) & 
                                         (self.radiator_constraints['Location'] == location_name)]

    def minimal_cost_radiators_in_room(self, room_df, flow_temperature):
        room_name = room_df['Room Name']
        location_constraints = self.radiator_constraints[self.radiator_constraints['Room Name'] == room_name]
        room = Room(room_df, location_constraints, self.radiator_database)
        room_result = room.minimal_cost_radiators(flow_temperature)
        room_result['room_name'] = room_name
        room_result['Room Temperature'] = room_df['Room Temperature']
        return room_result

    def total_costs(self, room_results):
        return sum(room_result['cost'] for room_result in room_results)

    def extract_replaced_radiators(self, room_results):
        replaced_rads = [rad for room_result in room_results for rad in room_result['replaced_radiators']]
        for rad in replaced_rads:
            rad['specification'] = self.find_radiator(self.radiator_database, rad['Radiator Key'])
        replaced_rads.sort(key=lambda rad: rad['specification']['£'])
        return replaced_rads

    def move_replaced_radiators(self, flow_temperature, room_results):
        replaced_rads = self.extract_replaced_radiators(room_results)
        new_radiators = self.find_new_radiators(room_results)

        for replacement_rad in replaced_rads:
            for new_radiator in new_radiators:
                location_constraint = self.find_constraint(new_radiator['room_name'], new_radiator['location_name'])
                result_location = self.find_location_in_room_results(room_results, location_constraint['Room Name'], location_constraint['Location'])

                if replacement_rad['specification']['w'] >= new_radiator['radiator']['w'] and \
                   Radiator.radiator_fits(location_constraint, replacement_rad['specification']) and \
                   result_location.get('Status') != 'Moved':
                    result_location['Status'] = 'Moved'
                    result_location['From'] = replacement_rad
                    result_location.update(self.find_radiator(self.radiator_database, replacement_rad['Radiator Key']))
                    result_location['£'] = 0.0
                    break

    def find_constraint(self, room_name, location_name):
        return self.radiator_constraints[(self.radiator_constraints['Room Name'] == room_name) & 
                                         (self.radiator_constraints['Location'] == location_name)].iloc[0]

    def find_location_in_room_results(self, room_results, room_name, location_name):
        return self.find_room_in_room_results(room_results, room_name)['locations'][location_name]

    def find_room_in_room_results(self, room_results, room_name):
        return next(room_result for room_result in room_results if room_result['room_name'] == room_name)

    def find_radiator(self, rad_db, key):
        return rad_db[rad_db['Radiator Key'] == key].iloc[0] if key is not None else None

    def find_new_radiators(self, room_results):
        new_radiators = []
        for room in room_results:
            for location_name, location in room['locations'].items():
                if location.get('Status') == 'New':
                    new_radiators.append({
                        'room_name': room['room_name'],
                        'location_name': location_name,
                        'radiator': location,
                        'Room Temperature': room['Room Temperature']
                    })
        new_radiators.sort(reverse=True, key=lambda rad: rad['radiator']['£'])
        return new_radiators
