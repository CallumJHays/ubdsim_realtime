# used by micropython module freezing / compilation
# kinda disgusting imo but whatever.
# referenced by $FROZEN_MANIFEST in micropython Makefiles

freeze_as_mpy('ubdsim', opt=3)
freeze_as_mpy('ubdsim_realtime', opt=3)
freeze_as_mpy("firmware/micropython/tools", ("upip.py", "upip_utarfile.py"), opt=3)
freeze_as_mpy(".upip-deps", opt=3)