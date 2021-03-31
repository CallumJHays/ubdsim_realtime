# used by micropython module freezing / compilation
# kinda disgusting imo but whatever.
# referenced by $FROZEN_MANIFEST in micropython Makefiles

import os

srcfiles = [
    f"{dirpath.replace('src/', '')}/{filename}"
    for dirpath, _, filenames in os.walk('src', followlinks=True)
    for filename in filenames
    if "test_" not in filename
]

print("SRCFILES", srcfiles)

freeze_as_mpy('src', srcfiles, opt=3)
freeze_as_mpy("firmware/micropython/tools", ("upip.py", "upip_utarfile.py"), opt=3)
freeze_as_mpy(".upip-deps", opt=3)