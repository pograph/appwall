from distutils.core import setup
import py2exe

setup(name="appwall",
    console = ["appwall.py"],
    data_files = ["template.png"])
