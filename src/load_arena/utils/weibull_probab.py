import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def weibull_probab(vel:np.array, A:float, k:float) -> pd.DataFrame:
    """
    
    Parameters:
    -----------
    vel : np.array
        wind speed array
    A : float
        scale parameter
    k : float
        shape parameter
        
    Returns:
    --------
    df : pd.DataFrame
        a dataframe containing windspeed and probability of wind speed in each bin

    Example
    -------
    >>> vel = np.arange(5,25,1)
    >>> A = 10
    >>> k = 2
    >>> df = weibull_probab(vel,A,k)
    >>> plt.plot(df['windspeed'], df['probability'])
    >>> plt.show()
    >>> print('done')


    """
    p = np.zeros(len(vel)-1)
    wsp = np.zeros(len(vel)-1)
    for i in range(0, len(vel)-1):
        p[i] = np.exp(-(vel[i]/A)**k) - np.exp(-(vel[i+1]/A)**k)
        wsp[i] = (vel[i] + vel[i+1])/2
    df = pd.DataFrame({'windspeed':wsp, 'probability':p})
    return df


if __name__=="__main__":
    vel = np.arange(5,25,1)
    A = 10
    k = 2
    df = weibull_probab(vel,A,k)
    plt.bar(df['windspeed'], df['probability'])
    plt.xlabel('windspeed')
    plt.ylabel('probability')
    plt.grid(True)
    plt.show()
    print('done')