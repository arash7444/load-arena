# load-arena
A Python toolkit for comparing and post-processing IEC 61400 wind turbine aeroelastic simulation results.


## Installation

```bash
# install requirements
pip install -r requirements.txt
```

## Input File Format

nput File Format
The package utilizes a CSV configuration input (such as input_file.csv) to coordinate post-processing. The CSV requires the following columns:

* **Folder**:  Directory path where the timeseries is located.
* **Timeseries**: Filename prefix (excluding extension) of the HAWC2 results.
* **Family**: Numeric or string identifier grouping similar simulations together.æ
* **PLF**: Partial Load Factor to apply (multiplied with the calculated statistics).
* **Averaging_method**: Method used to average the family. Supported methods:
    - mean: Average value across all files in the family.
    - max: Maximum value across all files in the family.
mean_max: Sorts the values descending and computes the mean of the top 50% (worst-case half).


## Features

* **Simple_stats**: Calculate standard statistics (mean, standard deviation, minimum, maximum)
* **Family_avg**: Calculate average values of the relvant time-series for each family


## Note:
The code is not done, and it's under development. 