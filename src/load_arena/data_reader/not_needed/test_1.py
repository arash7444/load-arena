import importlib
import inspect
import pkgutil
import re

# import wetb


def explore_package(package_name):
    package = importlib.import_module(package_name)

    print(f"\nPACKAGE: {package_name}")
    print(f"FILE: {inspect.getfile(package)}")

    for item in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        if re.search(r"hawc", item.name, re.IGNORECASE):
        # if "hawc" in item.name.lower():

            module_name = item.name

            try:
                module = importlib.import_module(module_name)
            except Exception as e:
                print(f"\nCould not import {module_name}: {e}")
                continue

            functions = inspect.getmembers(module, inspect.isfunction)
            classes = inspect.getmembers(module, inspect.isclass)

            if functions or classes:
                print(f"\nMODULE: {module_name}")

                for name, func in functions:
                    if func.__module__ == module.__name__:
                        print(f"  function: {name}{inspect.signature(func)}")

                for name, cls in classes:
                    if cls.__module__ == module.__name__:
                        print(f"  class: {name}")


explore_package("wetb")
    # explore_package("weio")