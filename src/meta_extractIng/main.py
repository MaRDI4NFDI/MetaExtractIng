import csv_extractor
import gromacs_extractor 
import netcdf_extractor 
import open_dihu_extractor 

def extract():
    """
    This method offers a user interface to select between different file types for processing (CSV, NetCDF, OpenDiHu and GROMACS). 															
    Based on the user's choice, it extracts metadata from specified sofwtare.

    Parameters
    ----------
    None
    """
    
    print("Choose a file type to process:")
    print("0. CSV")
    print("1. NetCDF")
    print("2. OpenDiHu")
    print("3. GROMACS")

    choice = input("Enter your choice (0, 1, 2 or 3): ")

    if choice == "0":
        csv_extractor.extract()
    elif choice == "1":
        netcdf_extractor.extract()
    elif choice == "2":
        open_dihu_extractor.extract()
    elif choice == "3":
        gromacs_extractor.extract()

    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    extract()

