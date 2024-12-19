import os
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

    folder_path = input("Enter the folder path containing OpenDihu simulation files, and each simulation in separate folders inside: ").strip()

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

            metadataExtractor = OpenDihuMetadataExtractor(filepath, extract_file_path)
            metadataExtractor.start()

            metadata_generator = MetadataGeneratorHelper(extract_file_path, ["variables"])
            metadata_generator.start()  
            
            jsonLDGenerator = JSONLDGenerator(metadata_file_path, extract_file_path)
            jsonLDGenerator.start()

            print(f"File {metadata_file_path.replace('.json','.jsonld')} successfully created.")
    
class OpenDihuMetadataExtractor:
    """
    Processes an OpenDiHu log file, extracting metadata between specific markers.

    Input: 
        - OpenDiHU file specified by the user at runtime
        - 'classes.json' file containing necessary class information	
    Output:													
        - 'extract.json' (or another specified filename) containing the extracted metadata in JSON format.
    ...

    Attributes
    ----------
    None


    Methods
    -------
    __init__(self, filepath: str, extract_file_path: str) -> None:
        Initilaizes the 'current_folder_path' and 'extract_file_path' variables

    start(self) -> None:
        Starts the main extracting process, and then saving the extracted data in json format

    find_marker(line: str, keyword: str) -> bool:
        Check if the keyword exists in a line

    save_metadata(data: Any, filename: str = "extract.json") -> None:
        Saves the content of dictionary 'data' into a file with name 'filename'

    process_line(line: str) -> dict:
        Extract key-value pairs from a line and return as a dictionary
    """

    def __init__(self, filepath: str, extract_file_path: str):
        self.filepath = filepath
        self.extract_file_path = extract_file_path
    
    def start(self):
        extracted_metadata = self.extract_metadata()
        save_json(extracted_metadata, self.extract_file_path)

    def find_marker(self, line: str, keyword: str):
        return keyword in line

    def process_line(self, line: str):
        parts = [part.strip() for part in line.split(",")]

        pairs = {}
        for part in parts:
            if ":" in part:
                key, value = [item.strip() for item in part.split(":", 1)]
                pairs[key] = value

        return pairs

    def extract_metadata(self):
        extension = os.path.splitext(self.filepath)[1]
        if extension == '.log':
            return self.extract_log()
        else:
            return None
        
    def extract_log(self):
        begin_keyword = "begin python output"
        end_keyword = "end python output"

        begin_index, end_index = None, None

        with open(self.filepath, 'r') as f:
            lines = f.readlines()

            # Find the lines containing the keywords
            for i, line in enumerate(lines):
                if self.find_marker(line, begin_keyword) and begin_index is None:
                    begin_index = i
                elif self.find_marker(line, end_keyword) and begin_index is not None:
                    end_index = i
                    break

        # Check if both markers were found
        if begin_index is None or end_index is None:
            print("Error: Couldn't find the begin or end markers in the log file.")
            return {}

        # Extract the section and join it as a single string
        extracted_data = ''.join(lines[begin_index + 1:end_index]).strip()

        data_dict = {"variables": {}}

        # Split the extracted data into lines and process each line
        for line in extracted_data.split('\n'):
            line_data = self.process_line(line)
            data_dict["variables"].update(line_data)

        return data_dict
     
if __name__ == "__main__":
    extract()