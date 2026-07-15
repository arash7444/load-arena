import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from load_arena.utils import weibull_probab

def calc_occurrence(probability, wsp, sim_length, Lifetime_years=20):
    """
    Calculate the number of occurrences of each wind speed bin in a given lifetime.

    Parameters:
    ------------
    probability : array_like
        Array of probabilities for each wind speed bin.
    wsp : array_like
        Array of wind speeds.
    sim_length : float
        Length of each simulation in seconds.
    Lifetime_years : int, optional
        Lifetime in years. Defaults to 20.

    Returns:
    -------
    df: Pandas DataFrame
        DataFrame with columns: 'windspeed', 'probability', 'occurrence'

    Example:
    >>> import numpy as np
    >>> import pandas as pd
    >>> from load_arena.utils import weibull_probab
    >>> vel = np.arange(5,25,1)
    >>> A = 10
    >>> k = 2
    >>> df = weibull_probab(vel,A,k)
    >>> df_occ = calc_occurrence(df['probability'], df['windspeed'], sim_length=600)
    >>> print(df_occ)
    
    """



    # Lifetime_years = 20

    lifetime_hr = Lifetime_years * 365 * 24     # This is 20 years as life time [hours]
    probability_wind = probability*lifetime_hr # this is the amount of hours for each wind speed bin in 20 years 
    sim_length_hr = sim_length / (60*60)          # this is the amount of hours for each simulation. I divided it by 3600 because the sim_length is in seconds
    OccurrencesPerLifetime = probability_wind /sim_length_hr   # this is the amount of occurrences for each wind speed bin in 20 years
    
    df_out = pd.DataFrame({"windspeed": wsp, "probability": probability, "occurrence": OccurrencesPerLifetime})

    return df_out




if __name__ == "__main__":
        
    vel = np.arange(5,25,1)
    A = 10
    k = 2
    df = weibull_probab(vel,A,k)
    plt.bar(df['windspeed'], df['probability'])
    plt.xlabel('windspeed')
    plt.ylabel('probability')
    plt.grid(True)
    plt.show()


    df_occ = calc_occurrence(df['probability'], df['windspeed'], sim_length=600)
    plt.bar(df_occ['windspeed'], df_occ['occurrence'])
    plt.xlabel('windspeed')
    plt.ylabel('occurrence')
    plt.grid(True)
    plt.show()

    print('done')


