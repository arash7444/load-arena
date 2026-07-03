# Load Arena Tool Design

## Goal
Load Arena is a Python tool for post-processing wind turbine aeroelastic simulation results based on IEC 61400 workflows.

## Main workflow

Input simulation results → data reader → processing → visualization/reporting.


```mermaid
flowchart LR

    A[HAWC2 result files] --> B[Simulation reader - ex: HAWC2 reader]
    B --> C[Convert it a standard Dataframe for all simulation softwares]
    C --> D[Statistics]
    C --> E[Family averaging]
    C --> F[DEL calculation]
    D --> G[Plots and reports]
    E --> G
    F --> G
```


## First supported simulation software
- HAWC2

## Later supported software

- Bladed
- OpenFAST
- QBlade

## First processing features

- Simple statistics
- Family averaging
- Extreme load calculation among all Load Cases
- Damage equivalent load using Rainflow counting


## Later features

- Ranking plots
- Report generation
- Machine learning based prediction/forecasting
- Blade Load rose
- Blade Load Duration Damage (LDD)
- 

## Internal data model

The reader should convert raw simulation output into a common data structure used by the rest of the tool.

## Flowchart of the tool:
![Load_Arena_flochart](image/Load_Arena.png)

