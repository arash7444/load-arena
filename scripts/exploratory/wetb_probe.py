
import wetb
import inspect


# console.print(dir(wetb))

# print(dir(wetb))
# print('done')

# print(inspect.getmembers(wetb.test))

# functions = inspect.getmembers(wetb, inspect.isfunction)

# for name, func in functions:
#     print(name)

# help(wetb)
# print(dir(wetb.utils))


import wetb 
help(wetb)

import inspect
import wetb.hawc2

for name, obj in inspect.getmembers(wetb.hawc2):
    print(name, type(obj))

inspect.signature(wetb.hawc2.AEFile)
print("done")