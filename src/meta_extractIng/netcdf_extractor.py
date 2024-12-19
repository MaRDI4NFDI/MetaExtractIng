import os
import re
try:
    from lib.ontologyScraper import OntologyScraper
    from lib.metadataGeneratorHelper import MetadataGeneratorHelper
    from lib.jsonldGenerator import JSONLDGenerator
    from lib.util import save_json
except ImportError:
    from .lib.ontologyScraper import OntologyScraper
    from .lib.metadataGeneratorHelper import MetadataGeneratorHelper
    from .lib.jsonldGenerator import JSONLDGenerator
    from .lib.util import save_json

def extract():
    """
    This method serves as the main orchestrator for a multi-step metadata processing workflow. 																					
    Sets up the environment by modifying the system path.																											
														
    Parameters
    ----------
    None
    """
    
    # Determine the absolute path of the parent directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)

    folder_path = input("Enter the folder path containing NetCDF simulation files, and each simulation in separate folders inside: ").strip()

    if not os.path.exists(f'{folder_path}/__output__/classes.json') \
        or not os.path.exists(f'{folder_path}/__output__/context.json'):
        scraper = OntologyScraper(folder_path)
        scraper.scrape()

    
    # Check if the folder path is absolute. If not, resolve it relative to both 
    # the script directory and parent directory
    if not os.path.isabs(folder_path):
        folder_path_script_dir = os.path.join(script_dir, folder_path)
        folder_path_parent_dir = os.path.join(parent_dir, folder_path)

        if os.path.exists(folder_path_script_dir):
            folder_path = folder_path_script_dir
        elif os.path.exists(folder_path_parent_dir):
            folder_path = folder_path_parent_dir
        else:
            print(f"Folder not found: {folder_path}")
            return

    output_folder = os.path.join(folder_path + '/__output__')

    for file_name in os.listdir(folder_path):
        if os.path.isfile(os.path.join(folder_path, file_name)):
            if file_name == '.DS_Store':
                continue
            filename = file_name.split('.')[0]
            filepath = f'{folder_path}/{file_name}'
            extract_file_path = f'{output_folder}/extract_{filename}.json'
            metadata_file_path = f'{output_folder}/metadata_{filename}.json'

            metadataExtractor = NetCDFMetadataExtractor(filepath, extract_file_path)
            metadataExtractor.start()

            metadata_generator = MetadataGeneratorHelper(extract_file_path, ["dimensions", "variables", "global_attributes"])
            metadata_generator.start()  
            
            jsonLDGenerator = JSONLDGenerator(metadata_file_path, extract_file_path)
            jsonLDGenerator.start()

            print(f"File {metadata_file_path.replace('.json','.jsonld')} successfully created.")
    
class NetCDFMetadataExtractor:
    """
    Extracts dimensions, variables, and global attributes from a CDL content file.																				

    Input: 																																							
        - CDL file specified by the user at runtime																														#
        - 'classes.json' file containing necessary class information
        																								
    Output:																																							
        - 'extract.json' (or another specified filename) containing the extracted metadata in JSON format.																#

    ...

    Attributes
    ----------
    classes : dict
        A dictionary which holds the 'classes' metadata, loaded from 'classes.json' file


    Methods
    -------
    __init__(self, filepath: str, extract_file_path: str) -> None:
        Initilaizes the 'current_folder_path' and 'extract_file_path' variables

    start(self) -> None:
        Starts the main extracting process, and then saving the extracted data in json format

    extract_dimensions(self, content: str) -> dict[Any, str]:    
        Extract dimensions from the CDL content

    extract_variables(self, content: str) -> dict:
        Extract variables and their attributes from the CDL content

    extract_global_attributes(self, content: str) -> dict[Any, str]:
        Extract global attributes from the CDL content

    extract_metadata(self, read_file: str) -> dict[str, Any]:
        Reads the content of the file 'read_file' and extracts metadata 
        from it into the a dictionary with these top-level keys:
            - dimensions
            - variables
            - global_attributes
    """

    def __init__(self, filepath: str, extract_file_path: str):
        self.filepath = filepath
        self.extract_file_path = extract_file_path
    
    def start(self):
        extracted_metadata = self.extract_metadata()
        save_json(extracted_metadata, self.extract_file_path)

    def extract_dimensions(self, content: str):
        dimensions = re.findall(r"(\w+)\s*=\s*(\d+)\s*;", content)
        return {dim_name: str(dim_value) for dim_name, dim_value in dimensions}

    def extract_variables(self, content: str):
        attributes_dict = {}
        variables_section = re.search(r'variables:\s*(.*?)\s*global attributes:', content, re.DOTALL)

        if variables_section:
            variables_content = variables_section.group(1)
            variable_blocks = re.split(r'\s*float\s+|\s*double\s+|\s*short\s+', variables_content.strip())

            for block in variable_blocks:
                if not block.strip():
                    continue
                lines = block.strip().splitlines()
                var_name = lines[0].strip().split('(')[0].strip()
                for line in lines[1:]:
                    match = re.match(r'\s*(\w+:\w+)\s*=\s*"(.*?)"\s*;', line)
                    if match:
                        key = f"{var_name}_{match.group(1).split(':')[1]}"
                        value = match.group(2).strip()
                        attributes_dict[key] = value
        return attributes_dict

    def extract_global_attributes(self, content: str):
        global_attributes_section = content.split("global attributes:\n")[-1]
        global_vars = re.findall(
            r":(\w+)\s*=\s*(.*?);", global_attributes_section, re.DOTALL)
        return {global_var_name.strip(): ' '.join(global_var_value.split()) 
                for global_var_name, global_var_value in global_vars}

    def extract_metadata(self):
        with open(self.filepath, 'r') as file:
            cdl_content = file.read()

        dimensions_dict = self.extract_dimensions(cdl_content)
        variables_dict = self.extract_variables(cdl_content)
        global_vars_dict = self.extract_global_attributes(cdl_content)

        # Combine all metadata into a single dictionary
        return {
            "dimensions": dimensions_dict,
            "variables": variables_dict,
            "global_attributes": global_vars_dict
        }
     
if __name__ == "__main__":
    extract()