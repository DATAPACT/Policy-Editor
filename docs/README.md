# Policy Editor

Powered by

[![UoSLOGO](./images/UniSouthampton.png)](https://dips.soton.ac.uk/#home)

## **General Description**

This repository contains a django app, which displays the Policy Editor reference UI. Allow user-friendly creation and maintenance of ODRL policies (including integration with domain specific ontologies).

## **How to Use**

Uploading domain specific ontologies. 
* This allows you to customise the policies you create with relevant terminology. These ontologies should link to the ODRL terms, and it is advised to use the [ODRL and DPV](https://github.com/DATAPACT/ODRL-DPV_ontology) base ontology.

Creating a new policy
* You can create a new policy by specifying which dataset (asset) the policy applies to.
* You can then specify a number of rules. Each rule must be either a permission, a prohibition or an obligation.
* For each rule, you can specify, among others:
  * The Action, that is, what is the action that is being permitted/prohibited/obliged  
  * The Actor, that is, who will have to follow this rule
  * The Purpose, the only allowed purpose for the action
  * Any additional constraints, such as until when the rule is valid.
* You can then save the policy, download its ODRL representation in a machine processable file.
* You can re-visit and edit saved policies.

## **Commercial Information**


| Organisation (s) | License Nature | License |
| --- | --- | --- |
| University of Southampton  | Open Source | MIT Licence |


## **How To Install**

### Requirements

Docker

### Software

Django, MongoDB

### Detailed Steps
1. Install dependencies
```bash
pip install -r requirements.txt
```
2.  Run the migrations
```bash
python manage.py makemigrations
python manage.py migrate
```
3. Create a superuser to access admin interface
```bash
python manage.py createsuperuser
```
4. Run the server
```bash
python manage.py runserver 

```



## Expected KPIs

| What | How | Values |
| --- | --- | --- |
| Coverage of the ODRL 2.2 language expressable by the editor | Listing the ODRL 2.2 terms and constructs expressible by the editor, and comparing them against the whole ODRL 2.2 language and vocabulary.   | >80% (100% of the non-ambiguous part of ODRL according Jaime et al. Evaluation and Comparison Semantics for ODRL, 2025)  |

Progress towards KPIs
* 04/03/2026: Improved interface usability and some additional language features. The editor is currently supporting 60% of the language features.
