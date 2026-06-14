"""
KivyMD recipe for python-for-android
Use PyPI URL instead of GitHub to avoid download issues
"""
from pythonforandroid.recipe import PythonRecipe


class KivyMDRecipe(PythonRecipe):
    # Let pip handle the download via PythonRecipe's default behavior
    version = "2.0.1"
    url = "https://files.pythonhosted.org/packages/source/k/kivymd/kivymd-{version}.tar.gz"
    depends = ["python3", "kivy", "setuptools"]
    python_depends = ["kivy"]

    call_hostpython_via_targetpython = False
    install_in_hostpython = False


recipe = KivyMDRecipe()
