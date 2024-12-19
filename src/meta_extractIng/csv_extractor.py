import os
try:
    from lib.ontologyScraper import OntologyScraper
    from lib.metadataGeneratorHelper import MetadataGeneratorHelper
    from lib.jsonldGenerator import JSONLDGenerator
    from lib.util import save_json, extract_csv
except ImportError:
    from .lib.ontologyScraper import OntologyScraper
    from .lib.metadataGeneratorHelper import MetadataGeneratorHelper
    from .lib.jsonldGenerator import JSONLDGenerator
    from .lib.util import save_json, extract_csv

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

    folder_path = input("Enter the folder path containing CSV simulation files, and each simulation in separate folders inside: ").strip()
    
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

            metadata_extract = extract_metadata(filepath)
            save_json(metadata_extract, extract_file_path)

            metadata_generator = MetadataGeneratorHelper(extract_file_path, ["csv_dict"])
            metadata_generator.start()  
            
            jsonLDGenerator = JSONLDGenerator(metadata_file_path, extract_file_path)
            jsonLDGenerator.start()

            print(f"File {metadata_file_path.replace('.json','.jsonld')} successfully created.")

def extract_metadata(filepath: str):
    extension = os.path.splitext(filepath)[1]
    if extension == '.csv':
        return extract_csv(filepath)
    else:
        return None   
    
if __name__ == "__main__":
    extract()