"""
Modul for working with files.
Currently this is only for playing with datetime stamps.
"""


import os
import datetime

pot = 'Q:/Mega/Ruj - Video'
print(os.path.exists(pot))
for root, dirs, files in os.walk(pot):
    #print (root, dirs, files)

    try:
        rootDT = root.split('\\')[-1].split(' ')[0].split('.')
        rootDT = list(map(int, rootDT))
        rootDT = datetime.datetime(2000 + rootDT[0], rootDT[1], rootDT[2])
    except:
        rootDT = datetime.datetime(2000, 1, 1)
    for datoteka in files:
        stats = os.stat(root + '/' + datoteka)
        atime, mtime, ctime = stats.st_atime, stats.st_mtime, stats.st_ctime
        atime = datetime.datetime.fromtimestamp(atime)
        mtime = datetime.datetime.fromtimestamp(mtime)
        ctime = datetime.datetime.fromtimestamp(ctime)

        if rootDT.day != mtime.day:
            print(root, rootDT, atime, mtime, ctime, sep='\t')
            print(stats)
        #if not mtime <= ctime:
        #    print(root, atime, mtime, ctime, mtime - ctime)
        #if mtime == ctime:
        #    print(root, atime, mtime, ctime, mtime - ctime)
        #print(, end='\t')
print()


"""
Mostly:
    access time is bullshit
    modified time is mostly the time when video recording ended (On GoPro. Unknown on Nikon)
    created time is sometimes:
        file created date on this partition
        start of recording (Happens only on my GoPro)
        end of recording (Happens only on my Nikon)
"""