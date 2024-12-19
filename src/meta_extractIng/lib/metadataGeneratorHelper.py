import os
from typing import Any
import re
from .util import save_json, load_json

class MetadataGeneratorHelper:
    """
    Structures the extracted metadata according to a predefined template 
    or interactively creates a new template containing the classes.

    Inputs:
        - 'extract.json' containing the extracted metadata.
        - 'classes.json' containing class definitions and properties.
        - Optionally, 'template.json' for predefined metadata mapping.

    Outputs:
        - 'metadata.json' containing the processed metadata.
        - 'template.json' (if created during the run) containing user-defined mappings for metadata.

    ...

    Attributes
    ----------
    directory : str
        Directory pointing to creating or reading template/metadata files

    self.target_keys : list
        A list of top-level keys that are listed in metadata.json files

    self.context : Any
        A dictionary of context data, loaded from specified URL 

    self.context_dict : Any
        A dictionary pointing to the 'context' key of loaded contenxt data 

    self.filtered_context : dict[Any, str]
        A dictionary of schemas, where key referes to the schema prefix and key corresponds to schema URI

    self.extract_data : Any
        A dictionary of extracted metadata

    self.classes : Any
        A dictionary of extracted classes from ontology, where key is class name and its key are their metadata

    self.template : Any
        A dictionary which holds the content of template data, which either created by the user or loaded from file

    self.metadata : Any
        A dictionary which holds the content of metadata, which is initinalized from metadata.json file and 
        then updated according to the template


    Methods
    -------
    __init__(directory: str, target_keys: list) -> None:
        Initializes the class attributes

    delete_metadata_files() -> None:  
        Checks and removes if metadata.json and metadata.jsonld files already exists 

    start() -> None:
        Starts the main metadata generating process     

    create_metadata_interactive() -> None:   
        Creates the metadata.json file in an interactive process from user

    ask_on_extracts() -> None    
        Handles the process where the user wants to specify which extracted metadata belong to which class

    ask_new_nodes() -> None:     
        Handles the process where the user wants to specify which new nodes to be added to the template

    ask_editing_nodes() -> None:  
        Handles the process where the user wants to specify which new properties to be added to each
        existing node in the template

    create_metadata_with_template() -> None 
        The process where template.json already exists to cross-matches the template.json and metadata.json          

    add_extra_properties(self) -> None:
        Handles the process where the user wants to add extra properties to already existing nodes

    add_new_item(key: str, values: Any, from_user: bool = False) -> None:
        Handles the process where the user wants to add a 'key' as the node key, along with 'values' as its attributes
        to the template file. 'from_user' when passed as 'True', specifies this new key has been entered by the user 
        and does not exists in the extracted metadata

    ask_for_node_selection(self) -> int:
        Handles the process in which a list of available nodes are shown to the user, and then user selects a valid
        index corresponding to that node 

    select_from_external_ontologies(self, with_property: bool = False) -> Tuple[str, str]:
        Handles the process in which a list of ontologies from contnxt file is shown to the user,
        and user selects the corresponding index. 

    get_full_iri_name(self, property_name: str, prop_type: str) -> str:
        Returns a concatenation between ontology prefix and property name

    get_valid_input(self, object_label: str) -> str:
        Validates whether the user has entered a valid name (for class name when selecting External Ontology option).
        Only a combination of Unicode characters (letters, numbers, and underscores) is valid.      
    """

    def __init__(self, extract_file_path: str, target_keys: list):
        self.extract_file_path = extract_file_path
        self.parent_folder = os.path.dirname(self.extract_file_path)
        self.target_keys = target_keys
        self.context = load_json(f'{self.parent_folder}/context.json')
        self.context_dict = self.context['@context']
        self.filtered_context = {k: v for k, v in self.context_dict.items() if isinstance(
            v, str) and (v.startswith("http://") or v.startswith("https://"))}
        self.extract_data = load_json(self.extract_file_path)
        self.classes = load_json(f'{self.parent_folder}/classes.json')
        self.template_file_path = os.path.join(self.parent_folder,'template.json')
        self.metadata_file_path = self.extract_file_path.replace('extract_','metadata_')
        self.jsonld_file_path = self.metadata_file_path.replace('.json','.jsonld')
        self.template = {}
        self.metadata = {}

    def delete_metadata_files(self):
        if os.path.exists(self.metadata_file_path):
            os.remove(self.metadata_file_path)
        if os.path.exists(self.jsonld_file_path):
            os.remove(self.jsonld_file_path)

    def start(self):
        self.delete_metadata_files()
        if not os.path.exists(self.template_file_path):
            self.create_metadata_interactive()
        self.create_metadata_with_template()
        save_json(self.metadata, self.metadata_file_path)

    def create_metadata_interactive(self):
        self.ask_on_extracts()
        self.ask_new_nodes()
        self.ask_editing_nodes()
        save_json(self.template, self.template_file_path)
        print("`template.json` has been created.")
        self.metadata = self.template

    def ask_on_extracts(self):
        if self.target_keys == ["csv_dict"]:
            for key in (k for k in self.extract_data["csv_dict"]['headers'] if k != 'id'):
                    self.add_new_item(key, None)
        else:    
            for top_level_key in self.target_keys:
                if top_level_key in self.extract_data:
                    for key, values in self.extract_data[top_level_key].items():
                        self.add_new_item(key, values)

    def ask_new_nodes(self):
        while True:
            extra_prop_confirm = input(
                "Do you want to create new node? (y/n): ").lower()
            if extra_prop_confirm == "y":
                key_label = self.get_valid_input(object_label="the new node")
                value_label = input(f"Enter the value of the new node: ")
                self.add_new_item(key_label, value_label, True)
            elif extra_prop_confirm == "n":
                break
            else:
                print("Invalid input. Please enter 'y' for Yes or 'n' for No.")

    def ask_editing_nodes(self):
        if not self.template:
            print("Invalid selections. No node to add to template, Program exiting ...")
            exit()
        while True:
            extra_prop_confirm = input(
                "Do you want to add extra peoperties to existing nodes? (y/n): ").lower()
            if extra_prop_confirm == "y":
                self.add_extra_properties()
            elif extra_prop_confirm == "n":
                break
            else:
                print("Invalid input. Please enter 'y' for Yes or 'n' for No.")

    def create_metadata_with_template(self):
        self.template = load_json(self.template_file_path)

        # Create metadata based on the template
        for template_key, template_props in self.template.items():
            key = template_key.split(":")[0].strip()
            for property_key, template_value in template_props.items():
                for top_level_key in self.target_keys:
                    if top_level_key in self.extract_data:
                        if key in self.extract_data[top_level_key]:
                            extracted_value = self.extract_data[top_level_key].get(
                                key)
                            property_value = extracted_value.get(
                                property_key) if isinstance(extracted_value, dict) else extracted_value

                            # Handle cases where the property value is a list of strings
                            if isinstance(property_value, list) and all(isinstance(item, str) for item in property_value):
                                property_value = ''.join(property_value)

                            if template_key not in self.metadata:
                                self.metadata[template_key] = {}

                            if property_value != None:
                                self.metadata[template_key][property_key] = property_value if template_value == '#Value' else template_value
            if template_key not in self.metadata:
                self.metadata[template_key] = template_props

    def add_extra_properties(self):
        while True:
            print("\nAvailable nodes:")
            for index, node_name in enumerate(self.template.keys(), 1):
                print(f"{index}. {node_name}")
            node_choice = input(
                f"Enter the node index: ")
            if node_choice.isdigit():
                node_index = int(node_choice) - 1
                if 0 <= node_index < len(self.template):
                    node_choice = list(self.template.keys())[
                        node_index]
                    break
                else:
                    print(
                        f"Invalid node choice. Please enter a number between 1 and {len(self.template)}.")
                    continue
            else:
                print(
                    f"Invalid node choice. Please enter a number between 1 and {len(self.template)}.")
                continue

        class_choice = node_choice.split(":")[1].strip()
        if class_choice in self.classes:
            properties = {**self.classes[class_choice].get(
                'is in domain of', {}), **self.classes[class_choice].get('is in range of', {})}
            if not properties:
                print(
                    f"No properties available for {class_choice}. Skipping...")
        else:
            properties = {}
        print(
            f"\nAvailable properties for {class_choice}:")
        for index, (prop_name, prop_type) in enumerate(properties.items(), 1):
            print(
                f"{index}. {prop_name} ({prop_type})")
        print(f"99. External Ontologies")

        selection_ended = False
        while not selection_ended:
            prop_choice = input(
                f"Enter the property index: ")
            if (int(prop_choice) == 99):
                # Case when the node is from external ontology
                if node_choice.count(':') > 1:
                    while True:
                        print(f"1. Object property")
                        print(f"2. Data property")
                        node_type_choice = input(
                            f"Please select the node type: ")
                        if node_type_choice.isdigit():
                            node_type_choice = int(node_type_choice)
                            if node_type_choice not in (1, 2):
                                print(f"Invalid choice. Please try again.")
                                continue
                            user_value = ''
                            property_name = self.get_valid_input(
                                object_label="the property name")
                            property_name = self.get_full_iri_name(
                                property_name, node_choice)
                            if node_type_choice == 1:
                                user_value = self.ask_for_node_selection()
                                user_value = f'@{user_value}'
                            else:
                                user_value = input(f"Please enter the value: ")
                                user_value = f'{user_value}'
                            current_key = self.template[f"{node_choice}"]
                            current_key[property_name] = user_value
                            self.template[f"{node_choice}"] = current_key
                            selection_ended = True
                            break
                        else:
                            print(f"Invalid choice. Please try again.")
                            continue
                else:
                    print(f"This class is not of an external ontology type.")
                    continue
            elif prop_choice.isdigit() and int(prop_choice) - 1 < len(properties):
                prop_choice = list(properties.keys())[
                    int(prop_choice) - 1]
                prop_type = properties[prop_choice]
                if prop_type == 'object property':
                    target_node_index = self.ask_for_node_selection()
                    current_key = self.template[f"{node_choice}"]
                    current_key[prop_choice] = f'@{target_node_index}'
                    self.template[f"{node_choice}"] = current_key
                else:
                    user_value = input(f"Enter the value for new property: ")
                    current_key = self.template[f"{node_choice}"]
                    current_key[prop_choice] = user_value
                    self.template[f"{node_choice}"] = current_key
                selection_ended = True
                break
            else:
                print(
                    f"Invalid property choice. Please try again.")

    def add_new_item(self, key: str, values: Any, from_user: bool = False):
        temp = None
        selection_confirmed = False
        external_ontology_choice = False
        while not selection_confirmed:
            print("\nAvailable classes:")
            print(f"0. Skip")
            for index, class_name in enumerate(self.classes.keys(), 1):
                print(f"{index}. {class_name}")
            print(f"99. External Ontologies")
            class_choice = input(
                f"Enter the class for {key}: ")
            if class_choice.isdigit():
                if int(class_choice) == 0:
                    selection_confirmed = True
                    continue
                elif int(class_choice) == 99:
                    class_choice, prop_choice = self.select_from_external_ontologies(
                        with_property=True)
                    external_ontology_choice = True
                    selected_properties = {}
                    selected_properties[prop_choice] = ''
                    self.template[f"{key}: {class_choice}"] = {
                        prop_choice: '#Value' if not from_user else values}
                else:
                    class_index = int(class_choice) - 1
                    if 0 <= class_index < len(self.classes):
                        class_choice = list(self.classes.keys())[class_index]
                        properties = {**self.classes[class_choice].get(
                            'is in domain of', {}), **self.classes[class_choice].get('is in range of', {})}
                        selected_properties = {}
                    else:
                        print(f"Invalid class choice for {key}.")
                        continue
            else:
                print(f"Invalid class choice")
                continue
            if not external_ontology_choice:
                if not isinstance(values, dict):
                    if not properties:
                        print(
                            f"No properties available for {class_choice}. Skipping...")
                        continue

                    print(
                        f"\nAvailable properties for {class_choice}:")
                    for index, (prop_name, prop_type) in enumerate(properties.items(), 1):
                        print(
                            f"{index}. {prop_name} ({prop_type})")
                    print(f"99. External Ontologies")

                    while True:
                        prop_choice = input(
                            f"Enter the property for {key}: ")
                        if prop_choice.isdigit():
                            if int(prop_choice) == 99:
                                prop_choice, _ = self.select_from_external_ontologies()
                                selected_properties[prop_choice] = ''
                                break
                            elif int(prop_choice) - 1 < len(properties):
                                prop_choice = list(properties.keys())[
                                    int(prop_choice) - 1]
                                selected_properties[prop_choice] = ''
                                break
                            else:
                                print(
                                    f"Invalid property choice for {key}. Please try again.")
                        else:
                            print(
                                f"Invalid property choice for {key}. Please try again.")

                    self.template[f"{key}: {class_choice}"] = {
                        prop_choice: '#Value' if not from_user else values}
                    temp = f"{key}: {class_choice}"
                else:
                    for property_key, _ in values.items():
                        if not properties:
                            print(
                                f"No properties available for {class_choice}. Skipping...")
                            continue

                        print(
                            f"\nAvailable properties for {class_choice}:")
                        for index, (prop_name, prop_type) in enumerate(properties.items(), 1):
                            print(
                                f"{index}. {prop_name} ({prop_type})")
                        print(f"99. External Ontologies")

                        while True:
                            prop_choice = input(
                                f"Enter the property for {property_key}: ")
                            if int(prop_choice) == 99:
                                ontology_choice, _ = self.select_from_external_ontologies()
                                selected_properties[property_key] = ontology_choice
                                break
                            elif prop_choice.isdigit() and int(prop_choice) - 1 < len(properties):
                                prop_choice = list(properties.keys())[
                                    int(prop_choice) - 1]
                                selected_properties[property_key] = prop_choice
                                break
                            else:
                                print(
                                    f"Invalid property choice for {property_key}. Please try again.")

                        template_key = f"{key}: {class_choice}"
                        temp = f"{key}: {class_choice}"
                        if template_key not in self.template:
                            self.template[template_key] = {}
                        self.template[template_key][property_key] = prop_choice
            # Print selected class and properties in structured format
            print(f"\nSelected for {key}:")
            print(f"\"{key}: {class_choice}\": {{")
            for prop, value in selected_properties.items():
                print(f"    \"{prop}\": \"{value}\",")
            print("},")

            # Ask for confirmation
            confirm = input(
                "Confirm selections? (y/n): ").lower()
            if confirm == "y":
                selection_confirmed = True
            elif confirm == "n":
                print(
                    "Discarding selection and restarting for this class.")
                del self.template[temp]
            else:
                print(
                    "Invalid input. Please enter 'y' for Yes or 'n' for No.")

    def ask_for_node_selection(self):
        selection_confirmed = False
        while not selection_confirmed:
            print("\nAvailable nodes:")
            for index, node_name in enumerate(self.template.keys(), 1):
                print(f"{index}. {node_name}")
            node_choice = input(f"Enter the node index: ")
            if node_choice.isdigit():
                node_index = int(node_choice) - 1
                if 0 <= node_index < len(self.template):
                    node_choice = list(self.template.keys())[
                        node_index]
                else:
                    print(
                        f"Invalid node choice. Please enter a number between 1 and {len(self.template)}.")
                    continue
            return node_index

    def select_from_external_ontologies(self, with_property: bool = False):
        ontology_choice = ''
        property_choice = ''

        print(f"\nAvailable Ontologies:")
        for index, (prefix_name, iri) in enumerate(self.filtered_context.items(), 1):
            print(f"{index}. {prefix_name} <{iri}>")
        while True:
            prop_choice = input(f"Enter the ontology index: ")
            if prop_choice.isdigit():
                ontology_index = int(prop_choice) - 1
                if 0 <= ontology_index < len(self.filtered_context):
                    ontology_choice = list(self.filtered_context.keys())[
                        ontology_index]
                    break
                else:
                    print(
                        f"Invalid ontology choice. Please enter a number between 1 and {len(self.filtered_context)}.")
                    continue
            else:
                print(
                    f"Invalid ontology choice. Please enter a number between 1 and {len(self.filtered_context)}.")
                continue

        class_choice = self.get_valid_input(object_label="the class name")
        if with_property == True:
            property_choice = input(f"Enter the property name: ")
            return f'{ontology_choice}:{class_choice}', f'{ontology_choice}:{property_choice}'
        else:
            return f'{ontology_choice}:{class_choice}', ''

    def get_full_iri_name(self, property_name: str, prop_type: str):
        ontology = prop_type.split(':')[1].lstrip()
        return f'{ontology}:{property_name}'

    def get_valid_input(self, object_label: str):
        while True:
            user_input = input(
                f"Enter a string with only letters and numbers for {object_label}: ")
            if re.match(r'^[\w\s]+$', user_input):
                return user_input
            else:
                print("Invalid input! Please enter only letters and numbers.")
