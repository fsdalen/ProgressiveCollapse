# ProgressiveCollapse

This project contains python and matlab files for running and post proccesing various progressive collapse analysis in Abaqus.
Some analysis also combine blast loading.

This project was created as part of a master's thesis at SIMLab, NTNU.


### How to run
* Analysis is ran from one of the .py files in the main folder
* Settings for each analyis is located at the top of each file
* Folders lib and inputData must be located in the Abaqus working directory
* Plot results: Run plot_xyData.m in the same dir as the xyData_____.txt files to plot them together

## Project structure
* **Main directory:** Various .py files used to run different analysis, README and "Snurre" to run an analysis on Snurre (cluster at SIMLab, NTNU)
* **Input data:** Data files used in the analysis
* **lib:** python files containing functions used by the scripts in the main dir. beam.py and shell.py conatin functions related to respectivly a beam- and shell model. func.py contains functions common to both models.
* **matlab:** Matlab scripts to generate input data or plot results

## Git branches
* **master:** Main branch
* **dev:** Develop new things
* **fix:** Bug fixes and smaller improvments
* **all other branches** Old branches kept just in case, just ignore them


<!--
## Beam model

#### Static Analysis

#### Alternate Path Analyses

#### Blast Analyses

#### Simple model



## Shell model

#### Static Analysis

#### Alternate Path Analyses

#### Blast Analysis
-->