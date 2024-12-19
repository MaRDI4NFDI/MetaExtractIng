import requests
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, OWL, RDFS, SKOS
import os
from .util import save_json, load_json

class OntologyScraper:
    """
    Extracts class metadata from a specified webpage and saves it to a JSON file. 
    It focuses on class relationships like super-classes, sub-classes and properties.	

    Input:
        - URL defined in '../lib/config.json'
    Output:
        - 'classes.json' containing scraped class metadata.

    ...

    Attributes
    ----------
    context_url : str
        URL pointing to 'Contenxt_URL' key in config.json file
    
    url : str
        URL pointing to 'URL' key in config.json file
    
    classes_dict : dict
        Dictionary to store the scraped classes and their properties

    OWL : Namespace
        Namespace pointing to "http://www.w3.org/2002/07/owl'

    Methods
    -------
    __init__(self) -> None:

    gather_super_data_properties(self, class_name: str) -> dict:
        Recursive function to collect data properties of super-classes.

    scrape(self) -> None:
        Main scraping function to parse an ontlogy and create classes_dict.
        If the URL ends with 'Owl' or 'XML' we scrape it and extract classes and their properties

    scrapOntlogy(self) -> None:
        Main scraping function for OWL or XML format. Fetches the raw content, 
        then with SPARQL queries to populates the classes_dict.
        
    populateClassDictionary(self, classLabel: str, classRelations: dict = None) -> None:
        Updating classes_dict with their properties

    queryClasses(self, graph: Graph) -> dict:
        Handles the query process for fetching classes from a Graph with SPARQL

    queryClassDomainOrRange(self, graph: Graph, classIRI: str, onDomain: bool = True, onObjectProperty: bool = True) -> list:
        Handles the query process for those classes which are in domain or in range from a Graph with SPARQL

    queryDisjointClasses(self, graph: Graph, classIRI: str) -> list:
        Handles the query process for those classes which are disjoint in a Graph with SPARQL

    querySuperClasses(self, graph: Graph, classIRI: str) -> list:
        Handles the query process for those classes which are super-classes in a Graph with SPARQL

    querySubClasses(self, graph: Graph, classIRI: str) -> list:
        Handles the query process for those classes which are sub-classes in a Graph with SPARQL

    queryMembers(self, graph: Graph, classIRI: str) -> list:
        Handles the query process for those classes which have members in a Graph with SPARQL

    updateDataPropertiesFromSuperClasses(self) -> None:
        Recursively searching in classes_dict to find class hierarchies

    fetch_and_save_context(self) -> None:
        Downloads context url metadata into a json file
    """
     
    def __init__(self, folder_path: str):
        config = load_json(os.path.join(os.path.dirname(os.path.abspath(__file__)),'config.json'))
        self.context_url = config["context_URL"]
        self.url = config["URL"]
        self.classes_dict = {}
        self.OWL = Namespace("http://www.w3.org/2002/07/owl#")
        self.folder_path = folder_path
        self.output_folder = os.path.join(self.folder_path + '/__output__')
        self.fetch_and_save_context()

    def gather_super_data_properties(self, class_name: str):
        """
        Recursive function to collect data properties of super-classes.

        Parameters
        ----------
        class_name :str
            The name of the class for which super properties are needed.

        Returns:
        ----------
        dict
            A dictionary of super data properties.
        """
        # If the class is not in our dictionary or doesn't have super-classes, return an empty dictionary
        if class_name not in self.classes_dict or "has super-classes" not in self.classes_dict[class_name]:
            return {}

        data_properties = {}
        # Iterating through super-classes to collect their data properties
        for super_class in self.classes_dict[class_name]["has super-classes"]:
            if super_class in self.classes_dict and "is in domain of" in self.classes_dict[super_class]:
                data_properties.update(
                    {k: v for k, v in self.classes_dict[super_class]["is in domain of"].items() if v == 'data property'})
            data_properties.update(
                self.gather_super_data_properties(super_class))
        return data_properties

    def scrape(self):
        if self.url.endswith('.owl') or self.url.endswith('.xml'):
            self.scrapOntology()
        else:
            print('The ontoloy URL format is not supported')
            exit()

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder, exist_ok=True)

        save_json(self.classes_dict, os.path.join(self.output_folder,'classes.json'))

    def scrapOntology(self):
        graph = Graph()
        graph.parse(self.url, format="xml")
        classes = self.queryClasses(graph)

        for classIRI, classLabel in classes.items():
            classRelations = {
                'super-classes': self.querySuperClasses(graph, classIRI),
                'sub-classes': self.querySubClasses(graph, classIRI),
                'members': self.queryMembers(graph, classIRI),
                'is disjoint with': self.queryDisjointClasses(graph, classIRI),
                'domainObjectProperties': self.queryClassDomainOrRange(graph, classIRI, True, True),
                'domainDataProperties': self.queryClassDomainOrRange(graph, classIRI, True, False),
                'rangeObjectProperties': self.queryClassDomainOrRange(graph, classIRI, False, True),
                'rangeDataProperties': self.queryClassDomainOrRange(graph, classIRI, False, False),
            }

            self.populateClassDictionary(classLabel, classRelations)

    def populateClassDictionary(self, classLabel: str, classRelations: dict = None):
        if classRelations is None:
            classRelations = {}

        result = {}

        # Mapping of keys to their types
        type_map = {
            'super-classes': 'class',
            'sub-classes': 'class',
            'members': 'named individual',
            'is disjoint with': 'class',
            'domainDataProperties': 'data property',
            'domainObjectProperties': 'object property',
            'rangeDataProperties': 'data property',
            'rangeObjectProperties': 'object property'
        }

        for key, item_type in type_map.items():
            items = classRelations.get(key, [])
            if items:
                if key.startswith('domain') or key.startswith('range'):
                    # Handle domain and range properties in a combined way
                    domain_key = 'is in domain of' if key.startswith('domain') else 'is in range of'
                    if domain_key not in result:
                        result[domain_key] = {}
                    result[domain_key].update({item: item_type for item in items})
                else:
                    result[f'has {key}'] = {item: item_type for item in items}

        self.classes_dict[classLabel] = result

        # Inherit data properties from super classes
        self.updateDataPropertiesFromSuperClasses()

    def queryClasses(self, graph: Graph):
        query = """
        SELECT ?class ?classLabel
        WHERE {
            ?class rdf:type owl:Class .
            OPTIONAL {
                ?class skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?class rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?classLabel)
            FILTER (?classLabel != "")
        }
        ORDER BY ?classLabel
        """
        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        classes = dict()
        for row in results:
            classes[str(row[0])] = str(row[1])
        return classes

    def queryClassDomainOrRange(self, graph: Graph, classIRI: str, onDomain: bool = True, onObjectProperty: bool = True):
        query = """
        SELECT ?property ?propertyLabel
        WHERE {
            ?property a owl:%s ;
            rdfs:%s <%s> .
            OPTIONAL {
                ?property skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?property rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?propertyLabel)
            FILTER (?propertyLabel != "")
        }
        """ % ('ObjectProperty' if onObjectProperty else 'DatatypeProperty', 'domain' if onDomain else 'range', classIRI)

        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        labels = list()
        for row in results:
            labels.append(str(row[1]))
        return labels

    def queryDisjointClasses(self, graph: Graph, classIRI: str):
        query = """
        SELECT ?disjointClass ?disjointClass_label
        WHERE {
            <%s> owl:disjointWith ?disjointClass .
            OPTIONAL {
                ?disjointClass skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?disjointClass rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?disjointClass_label)
            FILTER (?disjointClass_label != "")
        }
        """ % classIRI

        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        labels = list()
        for row in results:
            labels.append(str(row[1]))
        return labels

    def querySuperClasses(self, graph: Graph, classIRI: str):
        query = """
        SELECT ?superclass ?superclass_label
        WHERE {
            <%s> rdfs:subClassOf ?superclass .
            OPTIONAL {
                ?superclass skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?superclass rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?superclass_label)
            FILTER (?superclass_label != "")
        }
        """ % classIRI

        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        labels = list()
        for row in results:
            labels.append(str(row[1]))
        return labels

    def querySubClasses(self, graph: Graph, classIRI: str):
        query = """
        SELECT ?subclass ?subclass_label
        WHERE {
            ?subclass rdfs:subClassOf <%s> .
            OPTIONAL {
                ?subclass skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?subclass rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?subclass_label)
            FILTER (?subclass_label != "")
        }
        """ % classIRI

        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        labels = list()
        for row in results:
            labels.append(str(row[1]))
        return labels

    def queryMembers(self, graph: Graph, classIRI: str):
        query = """
        SELECT ?namedIndividual ?namedIndividualLabel
        WHERE {
            ?namedIndividual a owl:NamedIndividual.
            ?namedIndividual rdf:type <%s>.
            OPTIONAL {
                ?namedIndividual skos:prefLabel ?prefLabel.
                FILTER (lang(?prefLabel) = 'en')
            }
            OPTIONAL {
                ?namedIndividual rdfs:label ?label.
                FILTER (lang(?label) = 'en')
            }
            BIND(COALESCE(?prefLabel, ?label) AS ?namedIndividualLabel)
            FILTER (?namedIndividualLabel != "")
        }
        """ % classIRI

        results = graph.query(
            query, initNs={'rdf': RDF, 'owl': OWL, 'rdfs': RDFS, 'skos': SKOS})
        labels = list()
        for row in results:
            labels.append(str(row[1]))
        return labels

    def updateDataPropertiesFromSuperClasses(self):
        for class_name in self.classes_dict:
            super_data_properties = self.gather_super_data_properties(
                class_name)
            if super_data_properties:
                if "is in domain of" in self.classes_dict[class_name]:
                    self.classes_dict[class_name]["is in domain of"].update(
                        super_data_properties)
                else:
                    self.classes_dict[class_name]["is in domain of"] = super_data_properties

    def fetch_and_save_context(self):
        """Fetch the latest context from the given URL and save it to a local file."""
        file_path = self.folder_path + '/__output__/context.json'

        if os.path.exists(file_path):
            return

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder, exist_ok=True)

        response = requests.get(self.context_url)
        
        if response.status_code == 200:
            with open(os.path.join(self.folder_path + '/__output__/context.json'), "w") as file:
                file.write(response.text)
        else:
            print("Error fetching and saving the latest context.")
            exit()