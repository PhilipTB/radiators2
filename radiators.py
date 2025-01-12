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

    def __str__(self):
        return f"{self.length}x{self.height}:{self.type},{self.max_sub_type}:{self.status}=>{self.existing_radiator}"

#=======================================================================================================
class Radiator:
    database = None
    def __init__(self, name, type, sub_type, length, height, n, w_at_dt50, cost):
        self.name = name
        self.type = type
        self.sub_type = sub_type
        self.length = length
        self.height = height
        self.n = n
        self.w_at_dt50 = w_at_dt50
        self.cost = cost

    def __str__(self):
        return f"{self.name}x{self.type}x{self.sub_type}:{self.length}>{self.height}:{self.n}-{self.w_at_dt50}W:£{self.cost}"
        
    def wattage(self, flow_temperature, room_temperature):
        factor = Radiator.flow_temperature_adjustment_factor(flow_temperature, room_temperature, self.n)
        return factor * self.w_at_dt50
    
    @classmethod
    def flow_temperature_adjustment_factor(cls, flow_temperature, room_temperature, n):
        return pow((flow_temperature - room_temperature - 2.5)/50.0, n)
    
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
    def find_cost_effective_radiator(cls, type, max_sub_type, max_length, max_height, watts_at_dt50):
        print("        Looking for radiator at", type, max_sub_type, max_length, max_height, watts_at_dt50)

        cheapest_radiator = cls.database[
            (cls.database['W @ dt 50'] > watts_at_dt50) &
            (cls.database['Height'] <= max_height) &
            (cls.database['Length'] <= max_length)
        ].nsmallest(1,'£')

        print("        Cheapest radiators:", cheapest_radiator)

        if cheapest_radiator.empty:
            return None
        else:
            return cls.radiator_from_dataframe(cheapest_radiator)

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

