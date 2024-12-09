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
        print("    calculate_at_flow_temperature", flow_temperature)
        rad_watts_at_flow_t = self.total_watts_at_flow_temperature(flow_temperature)
        print("    upgrade rad?", self.heat_loss_w,rad_watts_at_flow_t, self.heat_loss_w > rad_watts_at_flow_t)
        if self.heat_loss_w > rad_watts_at_flow_t:
            self.upgrade_radiators(flow_temperature)

        formatted_results_by_radiator_locations = []
        for loc in self.radiator_locations:
            watts = 0.0
            if loc.existing_radiator != None:
                w = loc.existing_radiator.wattage(flow_temperature, self.temperature)
                watts += w

            formatted_results_by_radiator_locations.append(watts)

        return formatted_results_by_radiator_locations
    
    # https://stackoverflow.com/questions/14040260/how-to-iterate-over-n-dimensions
    # https://stackoverflow.com/questions/45737880/how-to-iterate-over-this-n-dimensional-dataset
    def nd_range(start, stop, dims):
        print("nd_range", start, stop, dims)
        if not dims:
            print("    YYY", dims)
            yield ()
            return
        for outer in Room.nd_range(start, stop, dims - 1):
            for inner in range(start, stop):
                print("    GGG", outer, " => ", inner, "Dims:", dims)
                yield outer + (inner,)

    def upgrade_radiators(self, flow_temperature):
        arr = np.random.random([4,5,2,6])
        print("RRR<<<", arr)
        print("    Rads need upgrading at", self.heat_loss_w, flow_temperature)
        factor = 1.0 / Radiator.flow_temperature_adjustment_factor(flow_temperature, self.temperature, 1.3)
        print("    Factor", factor, "flow t", flow_temperature, "room t", self.temperature)
        required_watts_at_dt50 = self.heat_loss_w * factor
        for loc in self.radiator_locations:
            if loc.existing_radiator != None:
                print("        existing rad upgrade", flow_temperature, loc.height, loc.length)
                print("        needs @ dt50", required_watts_at_dt50, "w, existing", loc.existing_radiator.w_at_dt50)

                if loc.existing_radiator.w_at_dt50 < required_watts_at_dt50:
                    new_rad = Radiator.find_cost_effective_radiator(loc.type, loc.max_sub_type, loc.length, loc.height, required_watts_at_dt50)
                    print("    Upgraded radiator", new_rad)
                    print(list(Room.nd_range(1, 3, 3)))


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
