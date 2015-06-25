"""
Module for converting between different time standards.
"""

def str_to_seconds(s):
    """
    Converts (hh:mm:ss) to seconds.
    """
    s = s.split(':')
    h = 0
    if len(s) == 3:
        h = int(s.pop(0))
    if len(s) > 2: # Pop already happened if going in here
        print('There is probably something wrong with input string:', s)
    m = int(s[0])
    s = int(s[1])
    return s + m*60 + h*60**2

def seconds_to_tuple(s):
    """
    Converts seconds to (d, h, m, s) tuple
    """
    sekunde = s%60
    s //= 60
    minute = s%60
    s //= 60
    ure = s%24
    s //= 24
    dnevi = s
    return (dnevi, ure, minute, sekunde)

def duration_to_seconds(duration):
    ''' Converts duration from ISO 8601 to seconds '''
    d, h, m, s = 0, 0, 0, 0
    duration = duration.strip('P')
    if 'D' in duration:
        d = int(duration.split('D')[0])
        duration = duration.split('D')[1]
    duration = duration.strip('T')
    if 'H' in duration:
        h = int(duration.split('H')[0])
        duration = duration.split('H')[1]
    if 'M' in duration:
        m = int(duration.split('M')[0])
        duration = duration.split('M')[1]
    if 'S' in duration:
        s = int(duration.strip('S'))
    return (((24*d) + h)*60 + m)*60 + s 