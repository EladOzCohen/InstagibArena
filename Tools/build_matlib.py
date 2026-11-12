"""Builds (or rebuilds) the whole world material library: textures, M_IAWorld, MI_W_*, glass, water, lava.

  UnrealEditor-Cmd.exe <uproject> -ExecutePythonScript=<proj>\\Tools\\build_matlib.py -unattended -nullrhi -nosplash -nopause
Set the environment variable IA_MATLIB_FORCE=1 to rebuild the master materials from scratch (instances are always updated).
"""
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import matlib  # noqa: E402

matlib.build_all(force_master=os.environ.get("IA_MATLIB_FORCE") == "1")
