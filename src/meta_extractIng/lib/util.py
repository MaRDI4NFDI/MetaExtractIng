import json
from typing import Any
import csv


def load_json(filename: str):
    """
    Retures the contents in a json file with 'filename' as its name

    Parameters
    ----------
    filename: str
        name of the input file

    Returns
    ----------
    Any
        The contents of file
    """
    with open(filename, "r") as file:
        return json.load(file)


def save_json(data: Any, filename: str):
    """	
    Saves the content of 'data' attribute into a file with name 'filename' as json format  

    Parameters
    ----------
    data: Any
        Content of the file to be written, in a dictionary format

    filename: str
        name
    """

    with open(filename, "w", encoding='utf8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def extract_csv(filepath: str):
    """	
    Extracts metadata in a csv file, first row should contain column names.
    Delimiter is automatically detected.

    Parameters
    ----------
    filepath: str
        File path to csv file

    Returns
    ----------
    dict
        A dictionary with a single key named 'csv_dict' with two items:
            -- headers: List of header names
            -- rows: a dict where each key is id and its value are a dict such that,
                     each key is column name and its value is the corresponding value in that row
    """
    with open(filepath, mode="r") as file:
        sample = file.read(1024)
        file.seek(0)
        detected_dialect = csv.Sniffer().sniff(sample)
        delimiter = detected_dialect.delimiter
        csv_reader = csv.reader(file, delimiter=delimiter)
        keys = next(csv_reader)
        final_dict = {}
        for values in csv_reader:
            data_dict = dict(zip(keys, values))
            data_dict = {k: v for k, v in data_dict.items() if k !=
                         "" and v != ""}
            id = data_dict["id"]
            del data_dict["id"]
            final_dict[id] = data_dict
        return {"csv_dict": {"headers": keys, "rows": final_dict}}
