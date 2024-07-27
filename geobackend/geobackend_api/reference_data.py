vaf_mapping = {
    '100qa': 'Quaternary Alluvium (100)',
    '101utb': 'Upper Tertiary/Quaternary Basalt (101)',
    '102utqa': 'Upper Tertiary-Quaternary Aquifer (102)',
    '103utqd': 'Upper Tertiary-Quaternary Aquitard (103)',
    '104utam': 'Upper Tertiary Aquifer (marine) (104)',
    '105utaf': 'Upper Tertiary Aquifer (fluvial) (105)',
    '106utd': 'Upper Tertiary Aquitard (106)',
    '107umta': 'Upper-Mid Tertiary Aquifer (107)',
    '108umtd': 'Upper-Mid Tertiary Aquitard (108)',
    '109lmta': 'Lower-Mid Tertiary Aquifer (109)',
    '110lmtd': 'Lower-Mid Tertiary Aquitard (110)',
    '111lta': 'Lower Tertiary Aquifer (111)',
    '112ltba': 'Lower Tertiary Basalt A stage (112)',
    '112ltbb': 'Lower Tertiary Basalt B stage (112)',
    '112ltb': 'Lower Tertiary Basalt (112)',
    '113cps': 'Cretaceous & Permian Sediments (113)',
    '114bse': 'Cretaceous & Palaeozoic Basement (114)'
}
#aquifers = {key.upper():value for key,value in aquifers.items()}

surface_terms = {
    'Aqdepth' : 'Depth to',
    'Elevtop' :    'Top Elevation',
    'Thickness' : 'Thickness',
    'Elevbottom' : 'Bottom Elevation'
}

is_aquifer = {
    '100qa': True,
    '101utb': False,
    '102utqa': True,
    '103utqd': False,
    '104utam': True,
    '105utaf': True,
    '106utd': False,
    '107umta': True,
    '108umtd': False,
    '109lmta': True,
    '110lmtd': False,
    '111lta': True,
    '112ltb': False,
    '113cps': False,
    '114bse': False
}

num_to_code_mapping = {
    '100': '100qa',
    '101': '101utb',
    '102': '102utqa',
    '103': '103utqd',
    '104': '104utam',
    '105': '105utaf',
    '106': '106utd',
    '107': '107umta',
    '108': '108umtd',
    '109': '109lmta',
    '110': '110lmtd',
    '111': '111lta',
    '112': '112ltb',
    '113': '113cps',
    '114': '114bse'
}