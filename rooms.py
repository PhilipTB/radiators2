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
        radiators_by_flow_temperature_formatted = {}

        for flow_temperature in flow_temperatures:
            radiators_by_flow_temperature_formatted[flow_temperature] = self.calculate_at_flow_temperature_formatted_result(flow_temperature)
            radiators_by_flow_temperature[flow_temperature] = self.calculate_at_flow_temperature(flow_temperature)
            print(self.name, flow_temperature, radiators_by_flow_temperature[flow_temperature])

        res =  self.flatten_results_by_flow_temperature(radiators_by_flow_temperature_formatted)
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
        room_watts = self.total_watts_at_flow_temperature(flow_temperature)
        if self.heat_loss_w > room_watts:
            self.upgrade_radiators(flow_temperature)

        formatted_results_by_radiator_locations = []
        for loc in self.radiator_locations:
            watts = 0.0
            if loc.existing_radiator != None:
                w = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                watts += w

            formatted_results_by_radiator_locations.append(watts)

        return formatted_results_by_radiator_locations

    
    def upgrade_radiators(self, flow_temperature):
        print("Rads need upgrading at", self.heat_loss_w, flow_temperature)
        for loc in self.radiator_locations:
            if loc.existing_radiator != None:
                print("Trying to upgrade", loc)
    
    def total_watts_at_flow_temperature(self, flow_temperature):
        room_watts = 0.0
        for loc in self.radiator_locations:
            watts = 0.0
            if loc.existing_radiator != None:
                radiator_watts = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                room_watts += radiator_watts


        return room_watts
    
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
