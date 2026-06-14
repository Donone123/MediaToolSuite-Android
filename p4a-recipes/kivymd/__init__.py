"""
KivyMD recipe for python-for-android
KivyMD is a pure Python package, no native compilation needed.
"""
from pythonforandroid.recipe import PythonRecipe


class KivyMDRecipe(PythonRecipe):
    version = "2.0.1"
    url = "https://github.com/kivymd/KivyMD/archive/{version}.tar.gz"
    depends = ["python3", "kivy", "setuptools"]
    python_depends = []

    # Bypass auto-resolver — treat as pure Python
    call_hostpython_via_targetpython = False
    install_in_hostpython = False


recipe = KivyMDRecipe()
