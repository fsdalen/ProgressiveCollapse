# ProgressiveCollapse

This project contains python and matlab files for running and post proccesing various progressive collapse analysis in Abaqus.
Some analysis also combine blast loading.

Both the project and this README is very much a working project right now.

### How to run
* Change parameters in the 'Control' section of run.py
* Have the working directory in Abaqus one level above the Progressive collapse folder
* Run run.py from cmd or from within Abaqus CAE
* Run plot_xyData.m in the same dir as the xyData_____.txt files that are creates to plot them together

## Overview of files
* **run.py:** This file is where parameters are changed, the model is build, analyzed and post procesed.
By post proccesing I mean reading results from the odb file.
I've tried to keep this file kind of short and all custum functions are in the myFuncs.py file
* **myFuncs.py:** Here you find all custum functions this file containts the majority of the code
* **plot_xyData.m:** Matlab script for plotting the xyData_____.txt files that is created from the post proccesing. 
* **model_steel_abaqus.m** and **mat_1.imp:** Just a Matlab file that creates the .imp file that cointaints parameters for a steel material.
* Other files are of no or minor importance.

## Major branches
* **master:** Simple beam model with a static analysis
* **beam_exp:** Explicit alternate path analysis and blast analysis using and incident wave interaction for the blast load.
* **beam_imp:** Implicit (Abaqus Standard) alternate path analysis

## Main parameters in run.py
* Number of bays and floors in building
* Global seed
* Step times
* Magnitude of Live load
* Turn on/off various analysis and post proccesing
* Number of CPUs to use in analysis

## Models
### Beam model
### Shell model

## Analysis

## More comments on individual files
