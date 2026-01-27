# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# DISCLAIMER: This software is provided "as is" without any warranty,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and non-infringement.
#
# In no event shall the authors or copyright holders be liable for any
# claim, damages, or other liability, whether in an action of contract,
# tort, or otherwise, arising from, out of, or in connection with the
# software or the use or other dealings in the software.
# -----------------------------------------------------------------------------
import os
import time
import uuid
# CM CHANGE telnetlib deprecated at pyton 3.13
import sys


if sys.version_info < (3, 13):
    from telnetlib import EC
else:
    from telnetlib3 import EC

from owlready2 import owl, default_world
from rdflib import Graph, Namespace
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from custom_accounts.predictions import ontology_classes_dict, prettyfy
from privux import settings

# CMTD2102
import threading
lock=threading.Lock()

#CM2102NEWONT
query_prefix = """
    PREFIX cc: <http://creativecommons.org/ns#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX vcard: <http://www.w3.org/2006/vcard/ns#>
    PREFIX sw: <http://www.w3.org/2003/06/sw-vocab-status/ns#>
    PREFIX vann: <http://purl.org/vocab/vann/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX odrl: <http://www.w3.org/ns/odrl/2/>
    PREFIX dpv: <https://w3id.org/dpv#>
    PREFIX dvpowl: <https://w3id.org/dpv/owl#>
    PREFIX dcam: <http://purl.org/dc/dcam/>
    """


def use_case_ontology_classes(ontology_file):
    """Returns the list of classes from the ontology
    :param ontology_file: ontology file
    :type ontology_file: str
    :return: list of classes
    :rtype: list
    Example:
            {
          "Exercise": [
            "CleanAndJerk",
            "Crunch",
            "Deadlift",
            "ImaginaryChair",
            "MachineRow",
            "PushUp",
            "RussianTwist",
            "SplitSquats",
            "Squat",
            "Weightlifting"
          ],
          "DifficultyLevel": [
            "Easy",
            "Hard",
            "Medium"
          ],
          "ExerciseTypes": [
            "AgilityAndPlyometric",
            "Balance",
            "Cardiovascular",
            "CoreTraining",
            "Endurance",
            "Flexibility",
            "FunctionalTraining",
            "HighIntensityIntervalTraining",
            "Isolation",
            "Rehabilitation",
            "Strength"
          ],
          "MuscleGroup": [
            "Abdominals",
            "Abs",
            "Arms",
            "Chest",
            "Legs",
            "Shoulders"
          ]
        }
    """
    thing_subclass = {}
    read_ontology(ontology_file)
    for cls in list(owl.Thing.subclasses()):
        subitems = [
            prettyfy(str(item), False)
            for item in list(cls.subclasses())
            if (len(list(cls.subclasses())) > 0)
        ]
        thing_subclass[prettyfy(str(cls), False)] = subitems
    return thing_subclass


def read_ontology(ontology_file, world=None):
    """Reads the ontology file and returns the ontology
    :param ontology_file: ontology file
    :type ontology_file: str
    :param world: world
    :type world: owlready2.World
    :return: ontology
    :rtype: owlready2.Ontology
    """
    ontology_file = str(os.path.relpath(ontology_file))
    if world is not None:
        ontology = world.get_ontology(
            os.path.join(settings.MEDIA_ROOT, str(ontology_file))
        ).load()
        if ontology_classes_dict(ontology):
            ontology.destroy()
            ontology = world.get_ontology(
                os.path.join(settings.MEDIA_ROOT, str(ontology_file))
            ).load()
    else:
        ontology = default_world.get_ontology(
            os.path.join(settings.MEDIA_ROOT, str(ontology_file))
        ).load()
        if ontology_classes_dict(ontology):
            try:
                ontology.destroy()
            except Exception as e:
                print(f"Ontology classes: {(ontology, e)}")
            ontology = default_world.get_ontology(
                os.path.join(settings.MEDIA_ROOT, str(ontology_file))
            ).load()
    return ontology


class MakeTree:
    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)


def tree_to_dict(node):
    result = {"node_name": node.data}
    if node.children:
        result["children"] = [tree_to_dict(child) for child in node.children]
    return result


def ontology_data_to_dict_tree(
    ontology,
    root,
    class_first_name=None,
    class_second_name=None,
):
    """Converts the daa classes of an ontology to a dict tree
    :param ontology: Ontology in owl/rdf format
    :type ontology: owlready2.Ontology
    :return: tree of purposes
    :rtype: dict
    """
    class_a = []
    class_b = []

    if root is None:
        return {"error": "Root class is not defined"}

    if class_first_name is not None:
        class_a = list(ontology_classes_dict(ontology)[class_first_name].subclasses())
    if class_second_name is not None:
        class_b = list(ontology_classes_dict(ontology)[class_second_name].subclasses())

    combined_data = class_a + class_b

    if not combined_data:
        return {}

    root = MakeTree(prettyfy(str(ontology_classes_dict(ontology)[root]), False))
    for cls in combined_data:
        root_child = MakeTree(prettyfy(str(cls), False))
        root.children.append(root_child)
        root_child_has_subclasses = list(cls.subclasses())
        if root_child_has_subclasses:
            for childcls in root_child_has_subclasses:
                root_child.children.append(MakeTree(prettyfy(str(childcls), False)))
    dict_tree = tree_to_dict(root)
    return dict_tree


def get_leaf_node_names(node):
    """Returns the list of leaf node names from the ontology
    Input is the tree data constructed based on data_context ontology.
    Example:
      'node_name': 'DataSource',
    'children': [
        {'node_name': 'Humidity'},
        {'node_name': 'Magnetometer'},
        {
            'node_name': 'PersonalData',
            'children': [
                {'node_name': 'Email'},
                {'node_name': 'Name'},
                {'node_name': 'SocialSecurityNumber'}
            ]
        },
        {'node_name': 'IPAddress'}
    ]

    Output:
     ['Humidity', 'Magnetometer', 'Email', 'Name', 'SocialSecurityNumber', 'IPAddress']

    :param node: Tree format
    :type node: MakeTree
    :return:  leaf node names
    :rtype: list
    """
    if "children" not in node:
        return [node["node_name"]]
    else:
        # Recursive case: node has children
        leaf_node_names = []
        for child in node["children"]:
            leaf_node_names.extend(get_leaf_node_names(child))
        return leaf_node_names

def get_fields_from_datasets(dataset,ThisUserid=0):
    # THREADSAFEFIX Attempt
    #g = global_graph
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]
    
    #CMTD2102
    with lock:
        #g=Graph()
        #g=g+global_graph
        # Query actions
        actions_query = f"""
             PREFIX ex: <http://example.org/datasets/>
             PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
             PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

             SELECT DISTINCT ?columnName ?columnType ?columnDescription ?columnExample
             WHERE {{
                 <{dataset}> rdf:type ex:Dataset ;
                     ex:hasColumn [ rdf:type ex:Column ;
                               ex:columnName ?columnName ;
                               ex:columnDataType ?columnType ;
                               ex:columnDescription ?columnDescription ;
                               ex:columnExample ?columnExample ] .
             }}
         """

        fields = [
             {"uri": row.columnName.value,"label": row.columnName.value,"columnName": row.columnName.value,"columnType": row.columnType.value,"columnDescription": row.columnDescription.value,"columnExample": row.columnExample.value}
             for row in g.query(actions_query)
         ]

        return fields

#CM2102NEWONT
#global_graph = Graph()
global_graphs={}

#CCM2102NEWONT
# Now uses user based graphs
def populate_graph(ttl_file_path, format="xml", ThisUserid=0):
    g = Graph()
    g.parse(ttl_file_path, format=format)
    
    #global global_graph
    global global_graphs
    # ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    if GraphName in global_graphs.keys():
        global_graphs[GraphName] += g
    else:
        global_graphs[GraphName] = Graph()
        global_graphs[GraphName] += g
    
    
    #global_graph += g

#CCM2102NEWONT
# Now uses user based graphs
def populate_content_to_graph(ttl_content, format="xml", ThisUserid=0):
    try:
        
        print("In populate_content_to_graph " + str(format))
        
        # CM2102NEWONT
        # Detect format from header to override format parameter
        #   a very quick fix at the moment
        # If we see "<?xml version"  at start of ttl_content then set of xml (otherwise ttl)
        if "<?xml version" in ttl_content[0:1000]:
            format="xml"
        else:
            format="turtle"       

        print("In populate_content_to_graph format now " + str(format))  
        print("In populate_content_to_graph format now " + str(ttl_content[0:2000]))          
   
        g = Graph()
        g.parse(data=ttl_content, format=format)
        
        #global global_graph
        #global_graph += g
        global global_graphs
        #ThisUserid = request.user.id
        # Check for existence in dict
        GraphName = str(ThisUserid)+"_graph"
        if GraphName in global_graphs.keys():
            global_graphs[GraphName]  += g
        else:
            global_graphs[GraphName] = Graph()
            global_graphs[GraphName]  += g    
        
        print("Out populate_content_to_graph " + str(GraphName))
    except:
        pass

#CCM2102NEWONT
# No longer used
def get_actions_from_ttl(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
    # Define the relevant namespaces
    # odrl = Namespace("http://www.w3.org/ns/odrl/2/#")
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")

    # Query for actions in the skos:Collection
    actions_query = """
    SELECT ?action
    WHERE {
      ?collection a skos:Collection ;
                  skos:member ?action .
    }
    """

    # Execute the query
    actions_result = g.query(actions_query, initNs={"skos": skos})

    # Extract and return the list of actions
    actions_list = [str(action) for action, in actions_result]
    return actions_list

#CCM2102NEWONT
# No longer used
def get_subclasses_of_rule2(ttl_file_path):
    # Load the TTL file into an RDF graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
    g.parse(ttl_file_path, format="turtle")

    # Define the relevant namespaces
    odrl = Namespace("http://www.w3.org/ns/odrl/2/#")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")

    # Query for subclasses of :Rule
    subclasses_query = """
    SELECT ?subclass
    WHERE {
      ?subclass a rdfs:Class ;
                rdfs:subClassOf odrl:Rule .
    }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query, initNs={"odrl": odrl, "rdfs": rdfs})

    # Extract and return the list of subclasses of :Rule
    subclasses_list = [str(subclass) for subclass, in subclasses_result]
    return subclasses_list

#CCM2102NEWONT
# Now uses user based graphs
def get_rules_from_odrl(ttl_file_path, ThisUserid):
    # THREADSAFEFIX Attempt
    #g = global_graph
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]

    # Define namespace
    # odrl = Namespace(
    #     "http://www.w3.org/ns/odrl/2/#"
    # )  # Replace with the actual namespace
    # rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")


    # Define namespace
    # odrl = Namespace(
    #     "http://www.w3.org/ns/odrl/2/#"
    # )  # Replace with the actual namespace
    # rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")

    # Query for subclasses of :Rule
    #Xsubclasses_query = """
    #X    SELECT ?subClass ?label
    #X    WHERE {
    #X      ?subClass rdfs:subClassOf odrl:Rule ;
    #X                rdfs:label ?label .
    #X    }
    #X"""
    
    # CM2102NEWONT
    
    # OPTIONAL ( ?subClass ( skos:definition | rdfs:comment )  ?definition . )
    
    #subclasses_query = query_prefix+"""
    #SELECT DISTINCT ?subClass ?label ?definition
    #    WHERE {
    #      ?subClass rdfs:subClassOf odrl:Rule ;
    #                ( rdfs:label | skos:prefLabel ) ?label ;
    #                skos:definition  ?definition .
    #    }
    #"""
    
    subclasses_query = query_prefix+"""
    SELECT DISTINCT ?subClass ?label ?definition
        WHERE {
          bind("No definition available" as ?default_definition)
          
          ?subClass rdfs:subClassOf odrl:Rule .
          ?subClass ( rdfs:label | skos:prefLabel ) ?label .                    
          OPTIONAL { ?subClass ( skos:definition | rdfs:comment | skos:note )  ?definition_res . }
          
          bind(coalesce(?definition_res, ?default_definition) as ?definition)
        }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.subClass), "label": str(row.label), "definition": str(row.definition)} for row in subclasses_result
    ]
    
    print("Out get_rules_from_odrl " + str(GraphName))
    
    return result_list

#CCM2102NEWONT
# No longer used
def get_actors_from_dpv(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
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

#CCM2102NEWONT
# No longer used
def get_purposes_from_dpv_old(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
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

#CCM2102NEWONT
# Now uses user based graphs
def get_constraints_types_from_odrl(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]
    
    # Query for subclasses of :Rule
    #Xquery = """
    #X    SELECT ?leftoperand ?label
    #X    WHERE {
    #X      ?leftoperand a odrl:LeftOperand, owl:NamedIndividual ;
    #X                rdfs:label ?label .
    #X    }
    #X"""
    
    
    
    

    #CM2102NEWONT
    query = query_prefix+"""
    SELECT DISTINCT ?leftoperand ?label
            WHERE {
              ?leftoperand rdf:type odrl:LeftOperand ;
                        ( rdfs:label | skos:prefLabel ) ?label .
            }
    """

    # Execute the query
    result = g.query(query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.leftoperand), "label": str(row.label)} for row in result
    ]
    
    print("Out get_constraints_types_from_odrl " + str(GraphName))
    
    return result_list

#CCM2102NEWONT
# Now uses user based graphs
def get_dataset_titles_and_uris(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]
    
    # Define the relevant namespaces
    ex = Namespace("http://example.org/datasets/")
    dct = Namespace("http://purl.org/dc/terms/")

    # Query for dataset titles and URIs
    query = """
    SELECT ?dataset ?title
    WHERE {
      ?dataset rdf:type ex:Dataset ;
               dct:title ?title .
    }
    """

    # Execute the query
    result = g.query(query, initNs={"ex": ex, "dct": dct})

    # Extract and return the list of dataset titles and URIs
    dataset_info_list = [
    # CMADD - The URI is now required as the label (done this way to minimise change in profile.html)
        #{"uri": str(dataset), "label": str(title)} for dataset, title in result
        {"uri": str(dataset), "label": str(dataset)} for dataset, title in result
    ]
    
    print("Out get_dataset_titles_and_uris " + str(GraphName))
    
    return dataset_info_list

#CCM2102NEWONT
# Now uses user based graphs
def get_action_hierarchy_from_odrl(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]

    # Define the SPARQL query to get actions and their relationships
    #X actions_query = """
    #X SELECT DISTINCT ?action ?label ?sub_action ?sub_label
    #X WHERE {
    #X     ?action a odrl:Action.
    #X     ?action rdfs:label ?label.
    #X     { ?sub_action odrl:includedIn ?action }
    #X     UNION
    #X     { ?action odrl:includedBy ?sub_action }
    #X     ?sub_action rdfs:label ?sub_label
    #X }
    #X """
    
    # CM2102NEWONT
    actions_query = query_prefix+"""
    SELECT DISTINCT ?action ?label ?definition ?sub_action ?sub_label ?sub_definition

        WHERE {
            ?sub_action (rdf:type /  rdfs:subClassOf?) odrl:Action.
            ?sub_action ( rdfs:label | skos:prefLabel ) ?sub_label.
            ?sub_action skos:definition ?sub_definition.
            ?sub_action odrl:includedIn | rdfs:subClassOf ?action .
            ?action ( rdfs:label | skos:prefLabel ) ?label .
            ?action skos:definition ?definition .

        }
    """
    # bind(... as ?default_foo)

    #optional { 
        # try to get value ?foo
     #}

    # bind(coalesce(?foo, ?default_foo) as ?result_foo)
    
    actions_query = query_prefix+"""
    SELECT DISTINCT ?action ?label ?definition ?sub_action ?sub_label ?sub_definition

        WHERE {
            bind("No definition available" as ?default_definition)
            bind("No definition available" as ?default_sub_definition)
            
            ?sub_action (rdf:type /  rdfs:subClassOf?) odrl:Action .
            ?sub_action ( rdfs:label | skos:prefLabel ) ?sub_label .
            OPTIONAL { ?sub_action ( skos:definition | rdfs:comment | skos:note ) ?sub_definition_res . }
            ?sub_action odrl:includedIn | rdfs:subClassOf ?action .
            ?action ( rdfs:label | skos:prefLabel ) ?label .
            OPTIONAL { ?action ( skos:definition | rdfs:comment | skos:note ) ?definition_res . }
            
            bind(coalesce(?definition_res, ?default_definition) as ?definition)
            bind(coalesce(?sub_definition_res, ?default_sub_definition) as ?sub_definition)
        }
    """
    
    #actions_query = query_prefix+"""
    #SELECT DISTINCT ?action ?label ?definition ?sub_action ?sub_label ?sub_definition

    #    WHERE {
            
    #        ?sub_action (rdf:type /  rdfs:subClassOf?) odrl:Action .
    #        ?sub_action ( rdfs:label | skos:prefLabel ) ?sub_label .
    #        OPTIONAL { ?sub_action ( skos:definition | rdfs:comment | skos:note ) ?sub_definition . }
    #        ?sub_action odrl:includedIn | rdfs:subClassOf ?action .
    #        ?action ( rdfs:label | skos:prefLabel ) ?label .
    #        OPTIONAL { ?action ( skos:definition | rdfs:comment | skos:note ) ?definition . }
           
    #    }
    #"""

    # Dictionaries to hold actions and their labels
    uri_label_dict = {}
    uri_definition_dict = {}
    action_hierarchy = {}

    # Execute the query and populate the dictionaries
    for row in g.query(actions_query):
        #print("In get_action_hierarchy_from_odrl(): The next row from query is " + str(row.action) + "/" + str(row.label) + "/" + str(row.sub_action) + "/" + str(row.sub_label))
        action_uri = str(row.action)
        action_label = str(row.label)
        action_definition = str(row.definition)
        sub_action_uri = str(row.sub_action)
        sub_action_label = str(row.sub_label)
        sub_action_definition = str(row.sub_definition)

        # Store labels for each URI
        uri_label_dict[action_uri] = action_label
        uri_label_dict[sub_action_uri] = sub_action_label
        
        # Store definitions for each URI
        uri_definition_dict[action_uri] = action_definition
        uri_definition_dict[sub_action_uri] = sub_action_definition

        # Organise actions into a hierarchy
        if action_uri not in action_hierarchy:
            action_hierarchy[action_uri] = {"uri": action_uri, "label": action_label, "definition": action_definition, "children": []}
        if sub_action_uri not in action_hierarchy:
            action_hierarchy[sub_action_uri] = {"uri": sub_action_uri, "label": sub_action_label, "definition": sub_action_definition, "children": []}
        action_hierarchy[action_uri]["children"].append(action_hierarchy[sub_action_uri])

    # Filter to include only top-level actions
    top_level_actions = {
        key: value for key, value in action_hierarchy.items()
        if not any(key in item["children"] for item in action_hierarchy.values())
    }
    
    #for item in top_level_actions:
        #print("The new top level actions are " + str(item))
    
    #print("Out get_action_hierarchy_from_odrl " + str(GraphName) + "/" + str(top_level_actions.values()))
    
    # Return the hierarchy as a list
    return list(top_level_actions.values())

#CCM2102NEWONT
# Now uses user based graphs
def get_purpose_hierarchy_from_dpv(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]

    # Define the SPARQL query to get actions and their relationships
    #X purpose_query = """
    #X SELECT DISTINCT ?purpose ?label ?sub_purpose ?sub_label
    #X WHERE {
    #X     ?purpose a <https://w3id.org/dpv#Purpose> .
    #X     ?purpose skos:prefLabel ?label .
    #X     { ?sub_purpose skos:broader ?purpose }
    #X     UNION
    #X     { ?purpose skos:narrower ?sub_purpose }
    #X     ?sub_purpose skos:prefLabel ?sub_label
    #X }
    #X """
    
    #CM2102NEWONT
    #purpose_query = query_prefix+"""
    #SELECT DISTINCT ?purpose ?label ?definition ?sub_purpose ?sub_label ?sub_definition
    #    WHERE {
    #        ?sub_purpose rdf:type dvpowl:Purpose .
    #        ?sub_purpose ( rdfs:label | skos:prefLabel ) ?sub_label.
    #        ?sub_purpose skos:definition ?sub_definition .
    #        ?sub_purpose ( skos:broader | rdfs:subClassOf) ?purpose .
    #        ?purpose ( rdfs:label | skos:prefLabel ) ?label .
    #        ?purpose skos:definition ?definition .
    #    }
    #"""
    
    purpose_query = query_prefix+"""
    SELECT DISTINCT ?purpose ?label ?definition ?sub_purpose ?sub_label ?sub_definition
        WHERE {
        
            bind("No definition available" as ?default_definition)
            bind("No definition available" as ?default_sub_definition)
            
            ?sub_purpose rdf:type dvpowl:Purpose .
            ?sub_purpose ( rdfs:label | skos:prefLabel ) ?sub_label.
            OPTIONAL { ?sub_purpose ( skos:definition | rdfs:comment | skos:note ) ?sub_definition_res . }
            ?sub_purpose ( skos:broader | rdfs:subClassOf) ?purpose .
            ?purpose ( rdfs:label | skos:prefLabel ) ?label .
            OPTIONAL { ?purpose ( skos:definition | rdfs:comment | skos:note ) ?definition_res . }
            
            bind(coalesce(?definition_res, ?default_definition) as ?definition)
            bind(coalesce(?sub_definition_res, ?default_sub_definition) as ?sub_definition)
        }
    """

    # Dictionaries to hold actions and their labels
    uri_label_dict = {}
    uri_definition_dict = {}
    purpose_hierarchy = {}
    

    # Execute the query and populate the dictionaries
    for row in g.query(purpose_query):
        purpose_uri = str(row.purpose)
        purpose_label = str(row.label)
        purpose_definition = str(row.definition)
        sub_purpose_uri = str(row.sub_purpose)
        sub_purpose_label = str(row.sub_label)
        sub_purpose_definition = str(row.sub_definition)

        # Store labels for each URI
        uri_label_dict[purpose_uri] = purpose_label
        uri_label_dict[sub_purpose_uri] = sub_purpose_label
        
        # Store definitions for each URI
        uri_definition_dict[purpose_uri] = purpose_definition
        uri_definition_dict[purpose_uri] = sub_purpose_definition

        # Organise actions into a hierarchy
        if purpose_uri not in purpose_hierarchy:
            purpose_hierarchy[purpose_uri] = {"uri": purpose_uri, "label": purpose_label, "definition": purpose_definition, "children": []}
        if sub_purpose_uri not in purpose_hierarchy:
            purpose_hierarchy[sub_purpose_uri] = {"uri": sub_purpose_uri, "label": sub_purpose_label, "definition": sub_purpose_definition, "children": []}
        purpose_hierarchy[purpose_uri]["children"].append(purpose_hierarchy[sub_purpose_uri])

    # Filter to include only top-level actions
    top_level_purposes = {
        key: value for key, value in purpose_hierarchy.items()
        if not any(key in item["children"] for item in purpose_hierarchy.values())
    }
    
    print("Out get_purpose_hierarchy_from_dpv " + str(GraphName))
    
    # Return the hierarchy as a list
    return list(top_level_purposes.values())

#CCM2102NEWONT
# Now uses user based graphs
def get_actor_hierarchy_from_dpv(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]

    #Xdpv = Namespace("https://w3id.org/dpv/dpv-owl#")
    #Xskos = Namespace("http://www.w3.org/2004/02/skos/core#")
    #Xg.bind("dpv",dpv)
    #Xg.bind("skos",skos)

    # Define the SPARQL query to get actions and their relationships
    #X actor_query = """
    #X SELECT DISTINCT ?actor ?label ?sub_actor ?sub_label
    #X WHERE {
    #X    ?actor rdfs:subClassOf* dpv:Entity .
    #X     ?actor skos:prefLabel|rdfs:label ?label .
    #X     ?sub_actor rdfs:subClassOf ?actor .
    #X     ?sub_actor skos:prefLabel|rdfs:label ?sub_label
    #X }
    #X """
    
    # CM2102NEWONT
    #actor_query = query_prefix+"""
    #SELECT DISTINCT ?actor ?label ?definition ?sub_actor ?sub_label ?sub_definition

    #    WHERE {
    #        ?actor rdfs:subClassOf* dvpowl:Entity .
    #        ?actor skos:prefLabel|rdfs:label ?label .
    #        ?actor skos:definition ?definition .
    #        ?sub_actor rdfs:subClassOf ?actor .
    #        ?sub_actor skos:prefLabel|rdfs:label ?sub_label .
    #        ?sub_actor skos:definition ?sub_definition

    #    }
    #"""
    
    actor_query = query_prefix+"""
    SELECT DISTINCT ?actor ?label ?definition ?sub_actor ?sub_label ?sub_definition

        WHERE {
            bind("No definition available" as ?default_definition)
            bind("No definition available" as ?default_sub_definition)
            
            ?actor rdfs:subClassOf* dvpowl:Entity .
            ?actor skos:prefLabel|rdfs:label ?label .
            OPTIONAL { ?actor ( skos:definition | rdfs:comment | skos:note ) ?definition_res . }
            ?sub_actor rdfs:subClassOf ?actor .
            ?sub_actor skos:prefLabel|rdfs:label ?sub_label .
            OPTIONAL { ?sub_actor ( skos:definition | rdfs:comment | skos:note ) ?sub_definition_res . }
            
            bind(coalesce(?definition_res, ?default_definition) as ?definition)
            bind(coalesce(?sub_definition_res, ?default_sub_definition) as ?sub_definition)

        }
    """
    
    # Dictionaries to hold actions and their labels
    uri_label_dict = {}
    uri_definition_dict = {}
    actor_hierarchy = {}

    # Execute the query and populate the dictionaries
    for row in g.query(actor_query):
        actor_uri = str(row.actor)
        actor_label = str(row.label)
        actor_definition = str(row.definition)
        sub_actor_uri = str(row.sub_actor)
        sub_actor_label = str(row.sub_label)
        sub_actor_definition = str(row.sub_definition)

        # Store labels for each URI
        uri_label_dict[actor_uri] = actor_label
        uri_label_dict[sub_actor_uri] = sub_actor_label
        
        # Store definitions for each URI
        uri_definition_dict[actor_uri] = actor_definition
        uri_definition_dict[sub_actor_uri] = sub_actor_definition

        # Organise actions into a hierarchy
        if actor_uri not in actor_hierarchy:
            actor_hierarchy[actor_uri] = {"uri": actor_uri, "label": actor_label, "definition": actor_definition, "children": []}
        if sub_actor_uri not in actor_hierarchy:
            actor_hierarchy[sub_actor_uri] = {"uri": sub_actor_uri, "label": sub_actor_label, "definition": sub_actor_definition, "children": []}
        actor_hierarchy[actor_uri]["children"].append(actor_hierarchy[sub_actor_uri])

    # Filter to include only top-level actions
    top_level_actors = {
        key: value for key, value in actor_hierarchy.items()
        if not any(key in item["children"] for item in actor_hierarchy.values())
    }
    
    print("Out get_actor_hierarchy_from_dpv " + str(GraphName))
    #print("Out get_actor_hierarchy_from_dpv " + str(top_level_actors.values()))
    
    # Return the hierarchy as a list
    return list(top_level_actors.values())

#CCM2102NEWONT
# No longer used
def get_actions_from_odrl(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
    # Define namespaces
    # odrl = Namespace("http://www.w3.org/ns/odrl/2/#")

    # Query actions
    actions_query = """
    SELECT ?action ?label ?parent_action ?parent_label
    WHERE {
        ?action a odrl:Action.
        ?action rdfs:label ?label.
        OPTIONAL { ?action odrl:includedIn ?parent_action .
                    ?parent_action rdfs:label ?parent_label . }
    }
    """
    actions = [
        {"uri": str(row.action), "label": str(row.label), "parent_uri" : str(row.parent_action), "parent_label" : str(row.parent_label)}
        for row in g.query(actions_query)
    ]

    return actions

#CCM2102NEWONT
# No longer used
def get_constraints_for_class_from_odrl(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph
    # Query for subclasses of :Rule
    query = """
        SELECT DISTINCT ?classname ?p
        WHERE {
          ?property a rdf:Property .
          ?instance a ?classname .
          ?classname a owl:Class .
          ?instance ?p ?o .
        }
    """

    # Execute the query
    result = g.query(query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.classname), "label": str(row.p)} for row in result
    ]

    return result_list

#CCM2102NEWONT
# Now uses user based graphs
def get_properties_of_a_class(class_uri, ThisUserid):
    global global_graphs
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    #CMTD2102
    with lock:
        #CMADD
        #global global_graph
        #g = global_graph
        #     global global_graphs
        #ThisUserid = request.user.id
        # Check for existence in dict
        GraphName = str(ThisUserid)+"_graph"
        g = global_graphs[GraphName]
    
        print("<<<<< We are in get_properties_of a_class. The class uri is " + class_uri)

        #X if "dpv" in class_uri:
        #X     instance = "dpv:" + instance.split("#")[1]
        #CMTD2102NEWONT
        if "dpv/owl" in class_uri:
            class_uri = "dvpowl:" + class_uri.split("#")[1]
        if "/" in class_uri:
            class_uri = "<" + class_uri + ">"
        
        
        #X properties_query = f"""
        #X    PREFIX dpv: <https://w3id.org/dpv/dpv-owl#>
        #X    PREFIX dpv: <https://w3id.org/dpv/dpv-owl#>
        #X    PREFIX cc: <http://creativecommons.org/ns#>
        #X    PREFIX odrl: <http://www.w3.org/ns/odrl/2/>
        #X    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #X    PREFIX owl: <http://www.w3.org/2002/07/owl#>

        #X    SELECT ?property ?label
        #X    WHERE {{
        #X      {class_uri} rdfs:subClassOf* ?class .
        #X      ?property rdf:type rdf:Property ;
        #X                rdfs:domain ?class ;
        #X                rdfs:label ?label .
        #X    }}
        #X"""
    
        #CM2102NEWONT  (Two versions of query second required to decrease run time)
        print("The class uri value in get_properties_of_a_class is " + class_uri)
        #X properties_query = query_prefix+"""
        #X SELECT DISTINCT ?property ?label
        #X         WHERE {{
        #X           {class_uri} ( skos:broader* | rdfs:subClassOf* ) ?class .
        #X           ?property (^rdfs:subPropertyOf | rdfs:subPropertyOf)? / ( rdfs:domain | schema:domainIncludes | dcam:domainIncludes ) / ( ^skos:broader | ^rdfs:subClassOf | skos:broader | rdfs:subClassOf)? ?class ;
        #X                     ( rdfs:label | skos:prefLabel ) ?label .
        #X         }}
        #X """
        properties_query = query_prefix+"""
        SELECT DISTINCT ?property ?label
        WHERE {{
          {class_uri} ( skos:broader? | rdfs:subClassOf? ) ?class .
          ?property ( rdfs:domain | schema:domainIncludes | dcam:domainIncludes ) / ( skos:broader | rdfs:subClassOf)? ?class ;
                    ( rdfs:label | skos:prefLabel ) ?label .
        }}
        """
        properties_query = properties_query.replace("{class_uri}", class_uri)
        
        properties_query = query_prefix+"""
        SELECT DISTINCT ?property ?label
        WHERE {
          {class_uri} rdf:type? / ( odrl:includedIn? | skos:broader? | rdfs:subClassOf* ) ?class .
          ?property ( rdfs:domain | schema:domainIncludes | dcam:domainIncludes ) / ( skos:broader | rdfs:subClassOf)? ?class ;
                    ( rdfs:label | skos:prefLabel ) ?label .
          FILTER ( ?property NOT IN ( odrl:includedIn, odrl:implies, odrl:hasPolicy) )
        }
        """
        properties_query = properties_query.replace("{class_uri}", class_uri)
    
        properties = [
            {"uri": str(row.property), "label": str(row.label)}
            for row in g.query(properties_query)
        ]
        print("<<<<< We are leaving get_properties_of a_class")
        print("Out get_properties_of a_class " + str(GraphName))
        return properties

#CCM2102NEWONT
# Now uses user based graphs
def get_constraints_for_instances(instance, ThisUserid):
    global global_graphs
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    #CMTD2102
    with lock:
        #CMADD
        #global global_graph
        #g = global_graph
        #   global global_graphs
        #ThisUserid = request.user.id
        # Check for existence in dict
        GraphName = str(ThisUserid)+"_graph"
        g = global_graphs[GraphName]
    
        print ("We are in get_constraints_for_instances and the instance is " + str(instance))
    
        #X if "dpv" in instance:
        #X     instance = "dpv:" + instance.split("#")[1]
        #CMTD2102NEWONT
        if "dpv/owl" in instance:
            instance = "dvpowl:" + instance.split("#")[1]

        if "/" in instance:
            instance = "<" + instance + ">"
        
        print ("We are in get_constraints_for_instances and the instance is " + str(instance))
    
        #X query = f"""
        #X     PREFIX dpv: <https://w3id.org/dpv#>
        #X     PREFIX odrl: <http://www.w3.org/ns/odrl/2/>
        #X     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        #X     PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        #X     PREFIX : <http://example.org/>

        #X     SELECT DISTINCT ?property ?label
        #X     WHERE {{
        #X       {instance} (skos:broader|odrl:includedIn)* ?parent .
        #X       ?parent :hasAttribute ?property .
        #X       ?property rdfs:label ?label .
        #X     }} ORDER BY UCASE(?label)
        #X """
        
        #CM2102NEWONT
        query = query_prefix+"""
        SELECT DISTINCT ?property ?label
        WHERE {
              {instance} (skos:broader|odrl:includedIn)* ?parent .

              ?parent <http://example.org/:hasAttribute> ?property .

              ?property rdfs:label ?label .

            } ORDER BY UCASE(?label)
        """
        query = query.replace("{instance}", instance)
        
        query = query_prefix+"""
        SELECT DISTINCT ?property ?label
        WHERE {
          {instance} rdf:type? / ( odrl:includedIn? | skos:broader? | rdfs:subClassOf* ) ?class .
          ?property ( rdfs:domain | schema:domainIncludes | dcam:domainIncludes ) / ( skos:broader | rdfs:subClassOf)? ?class ;
                    ( rdfs:label | skos:prefLabel ) ?label .
          FILTER ( ?property NOT IN ( odrl:includedIn, odrl:implies, odrl:hasPolicy) )
        }
        """
        query = query.replace("{instance}", instance)

        # Execute the query
        result = g.query(query)

        # Convert results to a list of dictionaries
        result_list = [
            {"uri": str(row.property), "label": str(row.label)} for row in result
        ]
    
        print ("We are out of get_constraints_for_instances and the instance is " + str(instance))
        print("Out get_constraints_for_instances " + str(GraphName))

        return result_list

#CCM2102NEWONT
# No longer used
def get_purposes_from_dpv(ttl_file_path):
    global global_graph
    # THREADSAFEFIX Attempt
    #g = global_graph
    
    g=Graph()
    g=g+global_graph

    # Define namespace
    dpv = Namespace("https://w3id.org/dpv#")  # Replace with the actual namespace
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")
    g.bind("dpv",dpv)
    g.bind("skos",skos)

    # Query for subclasses of :Rule
    subclasses_query = """
        SELECT ?subclass ?label ?parent_class ?class_label
        WHERE {
            ?subclass a dpv:Purpose.
            ?subclass skos:prefLabel ?label.
            OPTIONAL { ?subclass skos:broader ?parent_class .
                        ?parent_class skos:prefLabel ?class_label . }
        }
    """

    # Execute the query
    subclasses_result = g.query(subclasses_query)

    # Convert results to a list of dictionaries
    result_list = [
        {"uri": str(row.subclass), "label": str(row.label), "parent_uri" : str(row.parent_class), "parent_label" : str(row.class_label)} for row in subclasses_result
    ]

    return result_list




#CCM2102NEWONT
# No longer used
def get_actions_from_odrl_old(ttl_file_path):
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


#CCM2102NEWONT
# Now uses user based graphs
def get_operators_from_odrl(ttl_file_path, ThisUserid):
    #CMADD
    #global global_graph
    #g = global_graph
    global global_graphs
    #ThisUserid = request.user.id
    # Check for existence in dict
    GraphName = str(ThisUserid)+"_graph"
    g = global_graphs[GraphName]

    # Define namespaces
    # odrl = Namespace("http://www.w3.org/ns/odrl/2/#")

    # Query actions
    #X actions_query = """
    #X SELECT ?action ?label
    #X WHERE {
    #X     ?action a odrl:Operator.
    #X     ?action rdfs:label ?label.
    #X }
    #X """
    
    #CM2102NEWONT
    actions_query = query_prefix+"""
    SELECT DISTINCT ?action ?label
        WHERE {
            ?action rdf:type odrl:Operator.
            ?action ( rdfs:label | skos:prefLabel ) ?label.
        }
    """

    actions = [
        {"uri": str(row.action), "label": str(row.label)}
        for row in g.query(actions_query)
    ]
    
    print("Out get_operators_from_odrl " + str(GraphName))

    return actions

def convert_list_to_odrl_jsonld(data_list):
    odrl_rules = []
    policy = {
        "rule": odrl_rules,
    }
    for data in data_list:
        ruleType = "rule"
        odrl_jsonld = {
            "action": data["action"].split("/")[-1],  # Extract the action type
            "assignee": data["actor"].split("#")[-1],
            "constraint": [],
        }
        for constraint in data["constraints"]:
            odrl_jsonld["constraint"].append(
                {
                    "leftOperand": constraint["type"].split("/")[
                        -1
                    ],  # Extract the constraint type
                    "operator": constraint["operator"].split("/")[-1],
                    "rightOperand": constraint["value"],
                }
            )
        policy[ruleType].append(odrl_jsonld)
    if len(policy["rule"]) == 0:
        del policy["rule"]
    return policy



def convert_list_to_odrl_jsonld_depr(data_list):
    odrl_rules = []
    policy = {
        "rule": odrl_rules,
    }
    for data in data_list:
        if data["action"] is not None and data["actor"] is not None and data["target"] is not None:
            ruleType = "rule"
            targetrefinement = []
            target = ""
            if data["targetrefinements"] is not None:
                target = {"source" : data["target"].split("/")[-1],"refinement": targetrefinement}
            else:
                target = data["target"].split("/")[-1]

            odrl_jsonld = {
                "action": data["action"].split("/")[-1],  # Extract the action type
                "assignee": data["actor"].split("/")[-1],
                "target": target,
                "constraint": [],
            }

            for constraint in data["targetrefinements"]:
                if constraint["operator"] is not None:
                    odrl_jsonld["target"]["refinement"].append(
                        {
                            "leftOperand": constraint["type"].split("/")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"].split("/")[-1],
                            "rightOperand": constraint["value"],
                        }
                    )
            for constraint in data["constraints"]:
                if constraint["operator"] is not None:
                    odrl_jsonld["constraint"].append(
                        {
                            "leftOperand": constraint["type"].split("/")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"].split("/")[-1],
                            "rightOperand": constraint["value"],
                        }
                    )
            policy[ruleType].append(odrl_jsonld)
    if len(policy["rule"]) == 0:
        del policy["rule"]
    return policy

def recursive_replace(data, target_str, replacement_str):
    if isinstance(data, list):
        for i in range(len(data)):
            data[i] = recursive_replace(data[i], target_str, replacement_str)
    elif isinstance(data, dict):
        for key in data:
            data[key] = recursive_replace(data[key], target_str, replacement_str)
    elif isinstance(data, str):
        return data.replace(target_str, replacement_str)
    return data
def convert_list_to_odrl_jsonld_no_user(data_list):
    # data_list = recursive_replace (data_list,"https://w3id.org/dpv/dpv-owl#","https://w3id.org/dpv#")
    # data_list = recursive_replace (data_list,"http://www.w3.org/ns/odrl/2/","")

    odrl_permissions = []
    odrl_prohibitions = []
    odrl_obligations = []
    odrl_duties = []
    odrl_rules = []


    policy = {
        "permission": odrl_permissions,
        "prohibition": odrl_prohibitions,
        "obligation": odrl_obligations,
        "duty": odrl_duties,
        "rule": odrl_rules,
        "uid": "http://example.org/policy-" + str(uuid.uuid4()),
        "@context": [
        "http://www.w3.org/ns/odrl.jsonld",
        {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dpv": "https://w3id.org/dpv/dpv-owl#",
        }
        ],

        "@type": "Policy",
    }
    for data in data_list:
        if data["action"] is not None and data["actor"] is not None and data["target"] is not None:
            if "rule" in data:
                ruleType = str(data["rule"].split("/")[-1]).lower()

                if len(data["actorrefinements"])>0:
                    actor = {"@type":"PartyCollection", "source": data["actor"], "refinement": []}
                else:
                    actor = data["actor"]
                if len(data["actionrefinements"])>0:
                    action = {"source": data["action"], "refinement": []}
                else:
                    action = data["action"]


                if len(data["targetrefinements"])>0:
                    target = {"@type":"AssetCollection", "source": data["target"], "refinement": []}
                else:
                    target = data["target"]

                odrl_jsonld = {
                    "action": action,  # Extract the action type
                    "assignee": actor,
                    "target": target,
                    "constraint": [],
                }

                if len(data["purposerefinements"])>0:

                    purpose = data["purpose"]
                    purposerefinements = {"and":[]}
                    purposerefinements["and"].append({
                        "leftOperand": "purpose",
                        "operator": "http://www.w3.org/ns/odrl/2/eq",
                        "rightOperand": purpose,
                    })

                    for constraint in data["purposerefinements"]:

                        if constraint["operator"] is not None:
                            purposerefinements["and"].append(
                                {
                                    "leftOperand": constraint["type"].split("#")[
                                        -1
                                    ],  # Extract the constraint type
                                    "operator": constraint["operator"],
                                    "rightOperand": constraint["value"],
                                }
                            )

                    odrl_jsonld["constraint"].append(purposerefinements)
                else:
                    purpose = data["purpose"]
                    odrl_jsonld["constraint"].append(
                        {
                            "leftOperand": "purpose",
                            "operator": "http://www.w3.org/ns/odrl/2/eq",
                            "rightOperand": purpose,
                        }
                    )
            else:
                ruleType = "rule"
                odrl_jsonld = {
                    "action": data["action"],  # Extract the action type
                    "assignee": data["actor"],
                    "constraint": [],
                }
            if "query" in data:
                if data["query"] is not '':
                    odrl_jsonld["constraint"].append(
                        {
                            "leftOperand": "ex:query",
                            "operator": "http://www.w3.org/ns/odrl/2/eq",
                            "rightOperand": data["query"],
                        }
                    )
            for constraint in data["constraints"]:
                if constraint["operator"] is not None:
                    odrl_jsonld["constraint"].append(
                        {
                            "leftOperand": constraint["type"].split("#")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"],
                            "rightOperand": constraint["value"],
                        }
                    )
            for constraint in data["actorrefinements"]:
                if constraint["operator"] is not None:
                    print(constraint)
                    print(odrl_jsonld)
                    print(odrl_jsonld["assignee"]["refinement"])
                    print(constraint["type"])
                    print(constraint["operator"])
                    print(constraint["value"])
                    odrl_jsonld["assignee"]["refinement"].append(
                        {
                            "leftOperand": constraint["type"].split("#")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"],
                            "rightOperand": constraint["value"],
                        }
                    )
            for constraint in data["actionrefinements"]:
                if constraint["operator"] is not None:
                    odrl_jsonld["action"]["refinement"].append(
                        {
                            "leftOperand": constraint["type"].split("#")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"],
                            "rightOperand": constraint["value"],
                        }
                    )
            for constraint in data["targetrefinements"]:
                if constraint["operator"] is not None:
                    odrl_jsonld["target"]["refinement"].append(
                        {
                            "leftOperand": constraint["type"].split("#")[
                                -1
                            ],  # Extract the constraint type
                            "operator": constraint["operator"],
                            "rightOperand": constraint["value"],
                        }
                    )
            policy[ruleType].append(odrl_jsonld)
    if len(policy["permission"]) == 0:
        del policy["permission"]
    if len(policy["prohibition"]) == 0:
        del policy["prohibition"]
    if len(policy["obligation"]) == 0:
        del policy["obligation"]
    if len(policy["duty"]) == 0:
        del policy["duty"]
    if len(policy["rule"]) == 0:
        del policy["rule"]
    return policy

def _fetch_valid_status(odrl_policy):
    edge_options = webdriver.EdgeOptions()
    edge_options.add_argument("--headless")

    driver = webdriver.Edge(options=edge_options)
    driver.get("https://odrlapi.appspot.com/")

    WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.ID, "pgn")))
    print(odrl_policy)

    text_area = driver.find_element(By.ID, "pgn")
    text_area.send_keys(odrl_policy)

    time.sleep(3)

    validate_button = driver.find_element(By.XPATH, '//a[@id="boton2"]')
    validate_button.click()

    time.sleep(25)

    WebDriverWait(driver, 100).until(
        EC.invisibility_of_element_located(
            (By.XPATH, '//div[@id="salida"]/pre[text()="No output"]')
        )
    )

    result_element = driver.find_element(By.ID, "salida")
    result = result_element.text

    driver.implicitly_wait(0)
    driver.quit()

    return result
