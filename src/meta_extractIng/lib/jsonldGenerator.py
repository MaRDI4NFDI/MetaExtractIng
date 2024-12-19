from .util import save_json, load_json
import os

class JSONLDGenerator:
    def __init__(self, metadata_file_path: str, extract_file_path: str):
        self.metadata_file_path = metadata_file_path
        self.extract_file_path = extract_file_path
        self.parent_folder = os.path.dirname(self.metadata_file_path)
        self.context_file_path = f'{self.parent_folder}/context.json'
        self.jsonld_file_path = self.metadata_file_path.replace('.json','.jsonld')

    def start(self):
        latest_context = load_json(self.context_file_path )
        metadata = load_json(self.metadata_file_path)
        extract = load_json(self.extract_file_path)
        jsonld = {}
        if "csv_dict" in extract:
            jsonld = self.process_csv_metadata(metadata, extract, latest_context)
        else:
            jsonld = self.process_metadata(metadata, latest_context)
        save_json(jsonld, self.jsonld_file_path)
    
    def process_metadata(self, metadata, latest_context):
        jsonld = {
            "@context": latest_context['@context'],
            "@graph": []
        }

        # Adding 'local' to '@context'
        jsonld['@context']['local'] = "https://local-domain.org/"

        type_counters = {}  # Dictionary to track the counts of each @type

        id_list = []

        for key, value in metadata.items():
            variable_name, variable_type = key.split(":", 1)
            variable_name = variable_name.strip().lower()
            variable_type = variable_type.strip().lower()

            # Increment the counter for this @type or set it to 1 if it's the first occurrence
            type_counters[variable_type] = type_counters.get(variable_type, 0) + 1

            id = f"local:{variable_type}_{variable_name}_{type_counters[variable_type]}"

            id_list.append(id)

        index = 0

        for key, value in metadata.items():
            variable_name, variable_type = key.split(":", 1)
            variable_name = variable_name.strip().lower()
            variable_type = variable_type.strip().lower()

            item = {
                "@id": id_list[index],
                "@type": variable_type,
                "label": variable_name
            }

            for prop_key, prop_val in value.items():
                if prop_val.startswith("@"):
                    id_index = int(prop_val[1:])
                    prop_val = id_list[id_index]
                item[prop_key] = prop_val

            jsonld["@graph"].append(item)

            index += 1

        return jsonld
    
    def process_csv_metadata(self, metadata, extract, latest_context):
        jsonld = {
            "@context": latest_context['@context'],
            "@graph": []
        }
        # Adding 'local' to '@context'
        jsonld['@context']['local'] = "https://local-domain.org/"
        for id, row_values in extract['csv_dict']['rows'].items():
            data = []
            header_item = {
                "@id": f"local:{id}",
                "@type": "record",
                "data": []
            }
            for key, value in metadata.items():
                variable_name_original, variable_type = key.split(":", 1)
                variable_name = variable_name_original.strip().lower()
                variable_type = variable_type.strip().lower()
                row_item = {
                    "@id": f"local:{variable_name}_{id}",
                    "@type": variable_type,
                    "label": variable_name
                }
                if variable_name_original in row_values:
                    for prop_key, prop_val in value.items():
                        if prop_val.startswith("#"):
                            prop_val = row_values[variable_name_original]
                        row_item[prop_key] = prop_val
                    data.append(row_item)  
            header_item["data"] = data
            jsonld["@graph"].append(header_item)
        return jsonld