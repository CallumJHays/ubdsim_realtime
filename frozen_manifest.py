# used by micropython module freezing / compilation
# kinda disgusting imo but whatever.
# referenced by $FROZEN_MANIFEST in micropython Makefiles

import os

print('freezing modules as as mpy')

dont_freeze = os.getenv('DONT_FREEZE_MPY').split(':')
print("~~~~~~~ DONT_FREEZE_MPY =", dont_freeze)

to_freeze_src = []
for dirpath, _, filenames in os.walk('src', followlinks=True):
    if dirpath in dont_freeze:
        continue
    for filename in filenames:
        filepath = f"{dirpath.replace('src/', '')}/{filename}"
        if "test_" not in filename and (dirpath + filepath) not in dont_freeze:
            to_freeze_src.append(filepath)

freeze_as_mpy('src', to_freeze_src, opt=3)
freeze_as_mpy("firmware/micropython/tools", ("upip.py", "upip_utarfile.py"), opt=3)
freeze_as_mpy(".upip-deps", opt=3)

include_paths = os.getenv('FROZEN_MANIFEST_INCLUDE')
print("~~~~~~~ FROZEN_MANIFEST_INCLUDE =", include_paths)
if include_paths:
    for path in include_paths.split(':'):
        print('including ' + path)
        include(path)

print('module freezing complete')