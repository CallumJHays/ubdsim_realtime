# used by micropython module freezing / compilation
# kinda disgusting imo but whatever.
# referenced by $FROZEN_MANIFEST in micropython Makefiles

import os

print('freezing modules as as mpy')

srcfiles = [
    f"{dirpath.replace('src/', '')}/{filename}"
    for dirpath, _, filenames in os.walk('src', followlinks=True)
    for filename in filenames
    if "test_" not in filename
]
freeze_as_mpy('src', srcfiles, opt=3)

freeze_as_mpy("firmware/micropython/tools", ("upip.py", "upip_utarfile.py"), opt=3)
freeze_as_mpy(".upip-deps", opt=3)

include_paths = os.getenv('FROZEN_MANIFEST_INCLUDE')
if include_paths:
    for path in include_paths.split(':'):
        print('including ' + path)
        include(path)

print('module freezing complete')