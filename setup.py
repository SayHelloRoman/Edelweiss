from setuptools import setup
from Cython.Build import cythonize
import os

def find_py_files(directory):
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                full_path = os.path.join(root, file)
                py_files.append(full_path)
    return py_files


source_files = find_py_files("edelweiss/")

setup(
    ext_modules=cythonize(source_files + ['main.py'], language_level="3"),
)
