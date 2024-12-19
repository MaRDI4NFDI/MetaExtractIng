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

    folder_path = input("Enter the folder path containing GROMACS simulation files, and each simulation in separate folders inside: ").strip()

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

    for root, dirs, _ in os.walk(folder_path):
        for dir_name in dirs:
            if dir_name in ['__output__','__expected__']:
                continue
            current_folder_path = os.path.join(root, dir_name)
            extract_file_path = f'{output_folder}/extract_{dir_name}.json'
            metadata_file_path = f'{output_folder}/metadata_{dir_name}.json'

            metadataExtractor = GromacsMetadataExtractor(current_folder_path, extract_file_path)
            metadataExtractor.start()

            metadata_generator = MetadataGeneratorHelper(extract_file_path, ["variables", "global_attributes", "log_data", "job_data"])
            metadata_generator.start()  
            
            jsonLDGenerator = JSONLDGenerator(metadata_file_path, extract_file_path)
            jsonLDGenerator.start()

            print(f"File {metadata_file_path.replace('.json','.jsonld')} successfully created.")
    
class GromacsMetadataExtractor:
    """
    Extracts dimensions, variables, and global attributes from a GROMACS files in a folder.

    Input:
        - A folder containing GROMACS files specified by the user at runtime
        - 'classes.json' file containing necessary class information

    Output:
        - 'extract.json' (or another specified filename) containing the extracted metadata in JSON format.

    ...

    Attributes
    ----------
    variables : dict
        A dictionary which holds the 'variables' metadata

    global_attributes : dict
        A dictionary which holds the 'global_attributes' metadata

    log_data : dict
        A dictionary which holds the 'log_data' metadata

    job_data : dict
        A dictionary which holds the 'job_data' metadata


    Methods
    -------
    __init__(self, current_folder_path: str, extract_file_path: str) -> None:
        Initilaizes the 'current_folder_path' and 'extract_file_path' variables

    start(self) -> None:
        Starts the main extracting process, and then saving the extracted data in json format
        
    extract_metadata(self, read_folder: str) -> dict[str, Any]:
        Reads the content of the files in the 'read_folder' and looks into files with these extensions:
            - .mdp
            - .usermd
            - .log
            - .job
        And maps extracted metadata from these files into the a dictionary with these top-level keys:
            - variables
            - global_attributes
            - log_data
            - job_data
    
    extract_from_mdp(content: str) -> None:
        Extracts metadata from .mdp file and populates 'variables' dictionary
    
    extract_from_usermd(content: str) -> None:
        Extracts metadata from .usermd file and populates 'global_attributes' dictionary       

    extract_from_log(content: str) -> None:
        Extracts metadata from .log file and populates 'log_data' dictionary

    extract_from_job(content: str) -> None:
        Extracts metadata from .job file and populates 'job_data' dictionary     

    remap_variables_names() -> None:   
        Replaces the alias variables with their actual names, as following:
            - 'var1.name' -> Value of 'ref_t' in 'global_attributes'
            - 'var2.name' -> Value of 'tcoupl' in 'global_attributes'
            - 'var3.name' -> Value of 'ref_p' in 'global_attributes'
            - 'var4.name' -> Value of 'pcoupl' in 'global_attributes'         
    
    find_string_index(lines: list[str], search_string: str) -> int:  
        In a list of strings passed as 'lines', it searchs for the first occurance of 'search_string' 
        and returns the index, -1 if not found
    """

    def __init__(self, current_folder_path: str, extract_file_path: str):
        self.current_folder_path = current_folder_path
        self.extract_file_path = extract_file_path
        self.variables = dict()
        self.global_attributes = dict()
        self.log_data = dict()
        self.job_data = dict()

    def start(self):
        extracted_metadata = self.extract_metadata(self.current_folder_path)
        save_json(extracted_metadata, self.extract_file_path)

    def extract_metadata(self, read_folder: str):
        """Main function to extract metadata from a GROMACS folder."""
        for file_name in os.listdir(read_folder):
            if file_name == '.DS_Store':
                continue
            with open(f"{read_folder}/{file_name}", "r") as file:
                extention = os.path.splitext(file_name)[1]
                content = file.read()
                if extention == '.mdp':
                    self.extract_from_mdp(content)
                elif extention == '.usermd':
                    self.extract_from_usermd(content)
                elif extention == '.log':
                    self.extract_from_log(content)
                elif extention == '.job':
                    self.extract_from_job(content)
        self.remap_variables_names()
        return {
            "variables": self.variables,
            "global_attributes": self.global_attributes,
            "log_data": self.log_data,
            "job_data": self.job_data
        }

    def extract_from_mdp(self, content: str):
        lines = content.strip().split('\n')
        at_date_pattern = 'At date: (.+)'
        found_date = False
        for line in lines:
            if not found_date:
                match = re.search(at_date_pattern, line)
                if match:
                    self.variables['At Date'] = match.group(1)
                    found_date = True
                    continue
            if '=' in line and not line.startswith(';'):
                key, value = line.split('=', 1)
                self.variables[key.strip()] = value.strip()

    def extract_from_usermd(self, content: str):
        lines = content.strip().split('\n')
        for line in lines:
            if '=' in line:
                key, value = line.split('=', 1)
                self.global_attributes[key.strip()] = value.strip()

    def extract_from_log(self, content: str):
        lines = content.strip().split('\n')
        start_index = self.find_string_index(lines, "GROMACS:")
        end_index = self.find_string_index(lines, "C++ compiler flags:")
        for index, line in enumerate(lines[start_index:end_index + 1]):
            if len(line.strip()) == 0 or ':' not in line:
                continue
            key, value = line.split(':', 1)
            if key.strip() == 'Command line' and len(value) == 0:
                value = lines[start_index + index + 1]
            self.log_data[key.strip()] = value.strip()

    def extract_from_job(self, content: str):
        pattern = r'#MSUB -l (.+)'
        match = re.search(pattern, content)
        if match:
            key_value_string = match.group(1)
            pairs = re.findall(r'(\w+)=(\w+)', key_value_string)
            self.job_data = {key: value for key, value in pairs}

    def remap_variables_names(self):
        variables = ['ref_t', 'tcoupl', 'ref_p', 'pcoupl']
        alias_names = ['var1.name', 'var2.name', 'var3.name', 'var4.name']
        for variable, alias_name in zip(variables, alias_names):
            if alias_name in self.global_attributes:
                var_name = self.global_attributes[alias_name]
                value = self.variables.pop(variable)
                self.variables[var_name] = value

    def find_string_index(self, lines: list[str], search_string: str):
        return next((i for i, line in enumerate(lines) if search_string in line), -1)
    
if __name__ == "__main__":
    extract()