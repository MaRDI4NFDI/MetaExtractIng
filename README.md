[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14925139.svg)](https://doi.org/10.5281/zenodo.14925139)

# metaExtractIng

metaExtractIng is a tool for extracting important metadata from CSV, NetCDF, OpenDiHu and GROMACS files and storing it into a JSON-LD file, according to **[Metadata4Ing](https://nfdi4ing.pages.rwth-aachen.de/metadata4ing/metadata4ing/)** ontology. This README provides instructions on how to run metaExtractIng and generate the desired JSON-LD file.

## Installing metaExtractIng via package manager
Currently, you can download the package `meta_extractIng` via PyPI Test repository:

    pip install -i https://test.pypi.org/simple/ meta-extractIng

After successful installation, you can import `meta_extractIng` and use your desired software.  

    from meta_extractIng import csv_extractor, gromacs_extractor, open_dihu_extractor, netcdf_extractor
    
    csv_extractor.extract()
    open_dihu_extractor.extract()
    netcdf_extractor.extract()
    gromacs_extractor.extract()

After running each one of the `extract()` methods, you will be asked to give the path of your simulations folder. Only for the GROMACS simulations, the files should be given in separate folders inside the given path. The program uses given template file already in `__output__` folder. If this file is not given, the program asks the user to create a template interactively. Final Json-LD files will be saved at the `__output__` folder as well.

The program uses **[Metadata4Ing](https://nfdi4ing.pages.rwth-aachen.de/metadata4ing/metadata4ing/ontology.xml)** ontology as default. If you want to switch to another ontology, you can change the `URL` and `context_URL` values in the `config.json` file in `lib` folder, where your package is installed on your computer.

## Running metaExtractIng via source code

Navigate to `src/meta_extractIng` folder and run in terminal:

    python main.py

## Requirements

The following Python libraries are required to run the program:
- requests
- rdflib

To install the required libraries, run the following command:
```
pip install -r requirements.txt
```
## Source code folder structure

Main repository consists of four main folders:

 -  `meta_extractIng/src`: Contains source code,  and shared libraries in `lib` folder
	 - `lib`: Contains shared libraries
	 - `simulations`: Simulation examples for each software
 -  `tests`: Contains a unit test for checking the correctness of all simulations softwares.

 -  `docs`: Helpful documents to understand the flow of the program, for example, the interactive-template-generation step.
 
## Expected files

- **CSV**: It extracts all the data in header and rows. It expects the csv file has a header row, with one or more rows of data, and one column with `id`.
- **NetCDF**: It extracts dimensions, variables, and global attributes from a CDL content file.
- **OpenDiHu**: It processes an OpenDiHu log file, extracting metadata between specific markers.
- **GROMACS**: It processes a folder containing GROMACS output files, including `job`, `log`, `usermd` and `mdp` files, extracting metadata from them.

## Authors

The code was developed by Mahdi Jafarkhani, based on a prior development by Mohammed Asjadulla. The development was supervised by Björn Schembera.

## Acknowledgements 
The work has been funded by the DFG (German Research Foundation), project number 460135501, NFDI 29/1 “MaRDI – Mathematische Forschungsdateninitiative”.
