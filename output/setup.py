from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': []}

import sys
base = 'Win32Service' if sys.platform=='win32' else None

executables = [
    Executable('Kira.py', base=base, target_name = 'Kira.exe')
]

setup(name='Kira',
      version = '1.2',
      description = '',
      options = {'build_exe': build_options},
      executables = executables)
