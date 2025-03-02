class Radiator:
    radiator_depth_mm_data = {
        'K0':  70, # 1 panel
        '10':  70, # 1 panel 0 fins
        'P1':  70,
        'K1':  80, # 1 panel 1 fin
        '11':  80,
        'P+': 100, # 2 panels 1 fin
        '21': 100,
        'K2': 125, # 2 panels 2 fins
        '22': 125,
        'K3': 160, # 3 panels 3 fins
        '33': 160,
        '2 Col':  90,
        '3 Col': 115,
        '4 Col': 140,
        '5 Col': 175,
        '6 Col': 210,
        '7 Col': 245,
        None:   None,
    }

    @classmethod
    def radiator_depth_mm(cls, depth):
        return cls.radiator_depth_mm_data[depth]
        
    @classmethod
    def radiator_fits(cls, location, radiator):
        return (radiator['Type']   == location['Type'] and
                radiator['Height'] <= location['Height'] and
                radiator['Length'] <= location['Length'] and
                cls.radiator_depth_mm(radiator['Depth']) <= cls.radiator_depth_mm(location['Depth']))
    
    @classmethod
    def radiator_choices_at_location(cls, radiator_database, constraint):
        constraint_radiator_depth_mm = cls.radiator_depth_mm(constraint['Depth'])

        return radiator_database[(radiator_database['Type']   == constraint['Type']) &
                                 (radiator_database['Length']   <= constraint['Length']) & 
                                 (radiator_database['Height']   <= constraint['Height']) &
                                 (radiator_database['Depth_mm'] <= constraint_radiator_depth_mm)]
