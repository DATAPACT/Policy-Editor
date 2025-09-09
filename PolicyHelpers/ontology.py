import os

from rdflib import Graph, Namespace

current_folder_path = os.getcwd()
dpv_file_path = current_folder_path  + "/PolicyHelpers/ontology/dpv.rdf"
odrl_file_path =  current_folder_path  + "/PolicyHelpers/ontology/ODRL22.rdf"

def get_rules_from_odrl():
    ttl_file_path = odrl_file_path
    # Parse TTL data
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # Define namespace
    # odrl = Namespace(
    #     "http://www.w3.org/ns/odrl/2/#"
    # )  # Replace with the actual namespace
    # rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")

    # Query for subclasses of :Rule
    subclasses_query = """
        SELECT ?subClass ?label
        WHERE {
          ?subClass rdfs:subClassOf odrl:Rule ;
                    rdfs:label ?label .
        }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.subClass), "label": str(row.label)} for row in subclasses_result
    ]

    return result_list


def get_actors_from_dpv():
    ttl_file_path = dpv_file_path
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # dpv = Namespace("https://w3id.org/dpv#")
    # skos = Namespace("http://www.w3.org/2004/02/skos/core#")

    # Query for subclasses of :Rule
    subclasses_query = """
        SELECT ?subClass ?label
        WHERE {
          ?subClass rdfs:subClassOf+ <https://w3id.org/dpv/dpv-owl#LegalEntity> .
          ?subClass rdfs:label ?label .
        }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.subClass), "label": str(row.label)} for row in subclasses_result
    ]

    return result_list


def get_purposes_from_dpv():
    ttl_file_path = dpv_file_path
    # Parse TTL data
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # Define namespace
    # dpv = Namespace("https://w3id.org/dpv#")  # Replace with the actual namespace
    # skos = Namespace("http://www.w3.org/2004/02/skos/core#")

    # Query for subclasses of :Rule
    subclasses_query = """
        SELECT ?subClass ?label
        WHERE {
          ?subClass rdfs:subClassOf <https://w3id.org/dpv/dpv-owl#Purpose> .
          ?subClass rdfs:label ?label .
        }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.subClass), "label": str(row.label)} for row in subclasses_result
    ]

    return result_list


def get_constraints_types_from_odrl():
    ttl_file_path = odrl_file_path
    # Parse TTL data
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # Query for subclasses of :Rule
    query = """
        SELECT ?leftoperand ?label
        WHERE {
          ?leftoperand a odrl:LeftOperand, owl:NamedIndividual ;
                    rdfs:label ?label .
        }
    """

    # Execute the query
    result = g.query(query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.leftoperand), "label": str(row.label)} for row in result
    ]

    return result_list

def get_actions_from_odrl():
    ttl_file_path = odrl_file_path
    # Parse TTL content
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # Define namespaces
    # odrl = Namespace("http://www.w3.org/ns/odrl/2/#")

    # Query actions
    actions_query = """
    SELECT ?action ?label
    WHERE {
        ?action a odrl:Action.
        ?action rdfs:label ?label.
    }
    """

    actions = [
        {"uri": str(row.action), "label": str(row.label)}
        for row in g.query(actions_query)
    ]

    return actions


def get_operators_from_odrl():
    ttl_file_path = odrl_file_path
    # Parse TTL content
    g = Graph()
    g.parse(ttl_file_path, format="xml")

    # Define namespaces
    # odrl = Namespace("http://www.w3.org/ns/odrl/2/#")

    # Query actions
    actions_query = """
    SELECT ?action ?label
    WHERE {
        ?action a odrl:Operator.
        ?action rdfs:label ?label.
    }
    """

    actions = [
        {"uri": str(row.action), "label": str(row.label)}
        for row in g.query(actions_query)
    ]

    return actions

