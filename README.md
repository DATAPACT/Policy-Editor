# Policy Editor UI 
This repository contains a django app, which displays only the Policy Editor reference UI. 


#### How to run?
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
#### KPIs

| What | How | Values |
| --- | --- | --- |
| 1) Policy management expressiveness: ability to represent data processing regulations in a machine processable form. 2) Policy-based Data Access Control Accuracy | 1) analysis of an existing large (>100) corpus of data sharing/data processing agreements 2) Experiments over at least two policies, asking the pilots to express (in machine processable form, through our tool's interface) a sample (min 20 each) of( access requests (evenly distributed as requests to be permitted, and to be denied).  | 1) analysis of an existing large (>100) corpus of data sharing/data processing agreements 2) Experiments over at least two policies, asking the pilots to express (in machine processable form, through our tool's interface) a sample (min 20 each) of( access requests (evenly distributed as requests to be permitted, and to be denied).  |
