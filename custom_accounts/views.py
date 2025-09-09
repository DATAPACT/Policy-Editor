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
import datetime

# @Author  : Tek Raj Chhetri
# @Email   : tekraj.chhetri@sti2.at
# @Web     : https://tekrajchhetri.com/
# @File    : views.py
# @Software: PyCharm

from django.shortcuts import render

from PolicyHelpers.Parsers import ODRLParser
from PolicyHelpers.Translators import LogicTranslator
from .helper import convert_user_consent_to_odrl
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from .helper import generate_token
import json
from .helper import (
    sentence_rule_permission_status,
    sentence_rule_permission_status_revoke,
)
from .helper import get_all_users
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth import authenticate, login, logout

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseServerError
from django.http import JsonResponse
# ADDED
from django.http import HttpResponse

from .helper import match_user_data_with_controller_request_data
from .helper import convert_to_list
from custom_accounts.helper import merge_dictionaries
from custom_accounts.ajax_ontology import (
    read_ontology,
    use_case_ontology_classes,
    get_rules_from_odrl,
    get_actions_from_odrl,
    get_dataset_titles_and_uris,
    get_constraints_types_from_odrl,
    get_operators_from_odrl,
    convert_list_to_odrl_jsonld,
    get_purposes_from_dpv,
    get_actors_from_dpv, get_fields_from_datasets, convert_list_to_odrl_jsonld_no_user, get_properties_of_a_class,
    populate_graph, get_action_hierarchy_from_odrl, populate_content_to_graph, get_actor_hierarchy_from_dpv,
    get_purpose_hierarchy_from_dpv, get_constraints_for_instances,
)
from custom_accounts.ajax_ontology import ontology_data_to_dict_tree
import os

# because of the custom user model
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.urls import resolve
from django.contrib import messages
from django.core.mail import EmailMessage
from privux import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from datetime import date

from .models import CustomOntologyUpload, ODRLRuleUpload

User = get_user_model()


DATAPACKET=""

def check_rule_exists(user_id, name):
    
        
    try:
        odrl = ODRLRuleUpload.objects.get(edit_uid=user_id, name=name)
        # Assuming the content is a valid JSON string
        print("<<<<<< IN check_rule_exists: The rule data is " + str(odrl.content))
        return True
    except ODRLRuleUpload.DoesNotExist:
        print("Policy not found")
        return False
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return False
    


def index(request):
    print("Have come into the main index view")
    return render(request, "common/index.html")


def signin(request):
    if request.method == "POST":

 # Dealing with coming back to page (next three lines)
 # Does not get called
        #if request.user.is_authenticated:
        #    print("THE USER IS ALREADY LOGGED IN ")
        #    return redirect(reverse("create_rule_dataset_no_user"))
            
        username = request.POST["username"]
        password = request.POST["password"]
        # CM0304
        request_query = request.POST["request_query"]
# DEBUG       
#        print("THE USER NAME IS ", username, password)
        print("THE REQUEST QUERY IS ", request_query)

        user_login = authenticate(username=username, password=password)

# Commented this block out as we do not require redirect code
# Just added back in line login(request, user_login) and redirect
        if user_login is not None:
            #DEBUG
            print("THE AUTHENTICATION IS OK ", username, password)
            login(request, user_login)
            print("LOGGED IN ", username, password)
            # UITEST - Changed the entry oage next two lines
            
            #return redirect(request.POST.get('next'))
            if request_query == "DUMMY":
                return redirect(reverse("userhome"))
            else:
                # https://stackoverflow.com/questions/4995279/including-a-querystring-in-a-django-core-urlresolvers-reverse-call
                # https://stackoverflow.com/questions/25864935/pass-a-query-parameter-with-django-reverse
                
                #match = resolve(request_query)
                #print("The query params returned are " + str(match.kwargs))
                
                # CM0304
                # This code can be better generalised.
                # It assumes exact use case but OK for now
                
                query_url=request_query.split("?")[0]
                query_url=query_url.strip("/")
                print("Request url is " + query_url)
                query=request_query.split("?")[1]
                query_params=query.split("&")
                query_param_dict={}
                for query_param in query_params:
                    q_param_name=query_param.split("=")[0]
                    q_param_value=query_param.split("=")[1]
                    print("Parameter is " + q_param_name + " / " + q_param_value)
                    query_param_dict[q_param_name]=q_param_value
                
                
                #return redirect(reverse("userhome"))
                return redirect(reverse(query_url) +  "?" + query)
                return redirect(reverse(query_url, kwargs=query_param_dict))
                
            #return redirect(reverse("create_rule_dataset_no_user"))
        #if user_login is not None:
        #    login(request, user_login)
            # now rediredct to the home page based on the role
            # DATA_PROVIDER
       #    if user_login.role == "DATA_PROVIDER":
        #        return redirect(
        #            reverse("userhome"),
        #        )
            # DATA_CONTROLLER_PROCESSOR
        #    elif user_login.role == "DATACONTROLLER_PROCESSOR":
        #        return redirect(
        #            reverse("datacontrollerhome"),
        #        )
        #    else:
                # make sure that login is invlaid
        #        messages.error(request, "Bad Credentials!!")
        #        return redirect("login")
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect("login")

    print("The contents of the request dict GET is as follows " + str(request.GET.get('next')))
    return render(request, "register_login/login.html")


def send_activation_email(register_user, email_host_user, request):
    # Email Address Confirmation Email
    current_site = get_current_site(request)
    subject = "Confirm your Email Privacy Preference UI - UPCAST Project"
    message = render_to_string(
        "register_login/confirmation_email.html",
        {
            "name": register_user.first_name,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(register_user.pk)),
            "token": generate_token.make_token(register_user),
        },
    )
    email = EmailMessage(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [register_user.email],
    )
    email.fail_silently = True
    email.send()

def register(request):
    if request.method == "POST":
        user_name = request.POST.get("username")
        first_name = request.POST.get("firstname")
        last_name = request.POST.get("lastname")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmpassword")

        print(user_name, first_name, last_name, email, password, confirm_password)

        if User.objects.filter(username=user_name):
            messages.error(request, "Username exist! Please select new username.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email ID already registered.")
            return redirect("register")

        if user_name is None or user_name == "":
            messages.error(request, "Username cannot be empty.")
            return redirect("register")
        if len(user_name) < 4 and len(user_name) > 20:
            messages.error(request, "Username should be between 4 and 20 charcters.")
            return redirect("register")

        if password != confirm_password:
            messages.error(request, "The confirmation password does not match.")
            return redirect("register")
            
        # CM2102NEWONT
        # The default ORDL_DPV ontology will now be loaded into the core database
        # This can then be accessed via the new api.py service and will display for users 
        #       on the index page
        
        # Look in the central database to see if the default ontology has already been loaded
        # It is loaded as user id 999999. A arbitrary id that will not be allocated in normal runnning
        #
        
        # Get records for the default ontology user
        ontologies = CustomOntologyUpload.objects.filter(edit_uid = 999999)
        
        ontology_list = [
            # CM0311
            {"id": ontology.id, "name": ontology.name, "type": ontology.ontology_type, "content": ontology.content, "protection": ontology.protection}
            for ontology in ontologies
        ]
        
        if len(ontology_list) == 0:
            # If default ontologies not found then load them into the database
            
            #module_dir = os.path.dirname(__file__)  # get current directory
            #file_path = os.path.join(module_dir, "./media/default_ontology/ODRL_DPV.rdf")
            file_path = "./media/default_ontology/ODRL_DPV.rdf"
            ontology_file = open(file_path, encoding='utf8')
            
            if ontology_file:
                try:
                    # Read file content
                    #file_content = ontology_file.read().decode("utf-8")
                    file_content = ontology_file.read()


                    # Save content to the database
                
                    # Get the current user name
                    ThisUserid = 999999
                                
                    # Added try/except protecttion
                    try:
                        ontology = CustomOntologyUpload.objects.create(
                            # Added the current user name field
                            edit_uid = ThisUserid,
                
                            name="ODRL_DPV.rdf",
                            content=file_content,
                            ontology_type="DATA_CONTEXT",
                            # CM0311
                            protection=0
                        )
                    except Exception as err:
                        print("The error message is " + str(err))
                    
                                   
                except Exception as e:
                    print("The error returned during default ontology load is " + str(e))
                    messages.error(request, "Unable to load default ontologies.")
                    return redirect("register")

        register_user = User.objects.create_user(user_name, email, password)
        register_user.first_name = first_name
        register_user.last_name = last_name
        
        # In short term set to True to avaoid activation loop with emails
        #    See also activate()
        # register_user.is_active = False
        register_user.is_active = True
        
        
            
            
        
        register_user.role = "DATA_PROVIDER"
        register_user.save()
        messages.success(
            request,
            # CM2102NEWONT
            # "Your Account has been created succesfully!! Please check your email to activate your account.",
            "Your Account has been created succesfully!! ",
        )

        # activation email
        # 
        # Commented out for the moment as cannot get email working reliably
        # send_activation_email(register_user, settings.EMAIL_HOST_USER, request)

        return redirect("login")
    return render(request, "register_login/sign-up.html")


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        registered_user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        registered_user = None

    if registered_user is not None and generate_token.check_token(
        registered_user, token
    ):
        registered_user.is_active = True
        registered_user.save()
        messages.success(request, "Your Account has been activated!!")
        return redirect("login")
    else:
        # go back to home page
        return render(request, "common/index.html")


@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")
def userhome(request):
    # UITEST - Changed the entry oage next two lines
    print("The data received userhome is " + str(request))
    # Get the current user name
    ThisUserid = request.user.id
        
    # Get records for this user
    # odrls = ODRLRuleUpload.objects.all()
    odrls = ODRLRuleUpload.objects.filter(edit_uid = ThisUserid)
        
    odrl_list = [
    # CM0311
        {"id": odrl.id, "name": odrl.name, "protection": odrl.protection}
        for odrl in odrls
    ]
    
    # CM2102NEWONT
    # Get default ontologies
    ontols_default = CustomOntologyUpload.objects.filter(edit_uid = 999999)
        
    ontol_list_default = [
        # CM0311
        {"id": ontol.id, "name": ontol.name, "protection": ontol.protection}
        for ontol in ontols_default
    ]
    
    # Get records for this user
    # odrls = ODRLRuleUpload.objects.all()
    ontols = CustomOntologyUpload.objects.filter(edit_uid = ThisUserid)
        
    ontol_list = [
        # CM0311
        {"id": ontol.id, "name": ontol.name, "protection": ontol.protection}
        for ontol in ontols
    ]
    
    # CustOntList=CustomOntologyUpload.objects.all()
    # SavedPols=ODRLRuleUpload.objects.all()
    
    StdOnts=["Application specific integration of ODRL and DPV"]
    context={"CustOntList":ontol_list_default + ontol_list, "SavedPols":odrl_list, "StdOnts":StdOnts}
    # CM2403 NewIndex
    return render(request, "common/USER_TEST.html",context)
    #return render(request, "common/MainIndexPage.html",context)
    #return render(request, "users/index.html")


@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
def datacontrollerhome(request):
    return render(request, "admin_organization/index.html")


def signout(request):
    logout(request)
    return redirect("login")


#CM2102NEWONT
#  Probably no longer used 
@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
def configurepolicy(request):
    #CM2102NEWONT
    # Get the current user name
    ThisUserid = request.user.id
    
    rules = get_rules_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    actors = get_actors_from_dpv("./media/default_ontology/dpv.rdf", ThisUserid)
    actions = get_actions_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    targets = get_dataset_titles_and_uris("./media/default_ontology/Datasets.ttl", ThisUserid)
    constraints = get_constraints_types_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    purposes = get_purposes_from_dpv("./media/default_ontology/dpv.rdf", ThisUserid)
    operators = get_operators_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)

    context = {
        "rules": rules,
        "actors": actors,
        "actions": actions,
        "targets": targets,
        "constraints": constraints,
        "operators": operators,
        "purposes": purposes,
    }
    return render(request, "../templates/policy/policy.html", context=context)

def ajax_get_fields_from_datasets(request):
    if request.method == "POST":
        try:
            
            #CM2102NEWONT
            # Get the current user name
            ThisUserid = request.user.id
            
            data = json.loads(request.body)
            
            data = json.loads(request.body)
            dataset = data.get("uri")
            print("ajax_get_fields_from_dataset the dataset/uri is " + str(dataset))
            fields = get_fields_from_datasets(dataset, ThisUserid)
            res = 200
            # res = _fetch_valid_status(odrl)
            return JsonResponse({"fields":fields})
        except BaseException as b:
                print("The error response from get_fields_from_datasets is " + str(b));
                return b

#CM2102NEWONT
#  No longer used 
def ajax_get_properties_from_properties_file1(request):
    if request.method == "POST":
        try:
            uri = request.GET["uri"]
            fields = get_properties_of_a_class(uri,"./media/default_ontology/AdditionalProperties.ttl")
            res = 200
            # res = _fetch_valid_status(odrl)
            return JsonResponse({"fields":fields})
        except BaseException as b:
                return b

def ajax_get_constraints_for_instances(request):
    if request.method == "POST":
        try:
            #CM2102NEWONT
            # Get the current user name
            ThisUserid = request.user.id
                        
            data = json.loads(request.body)
            uri = data.get("uri")
            fields = get_constraints_for_instances(uri, ThisUserid)
            return JsonResponse({"fields": fields}, status=200)
        except BaseException as e:
            print("ajax_get_constraints_for_instances: ERROR : " + str(uri) + " / " + str(e))
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def ajax_get_properties_of_a_class(request):
    if request.method == "POST":
        try:
            #CM2102NEWONT 
            # Get the current user name
            ThisUserid = request.user.id
            
            data = json.loads(request.body)
            uri = data.get("uri")
            fields = get_properties_of_a_class(uri, ThisUserid )
            return JsonResponse({"fields": fields}, status=200)
        except BaseException as e:
            print("ajax_get_properties_of_a_class: ERROR : " + str(uri) + " / " + str(e))
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def ajax_get_properties_from_properties_file(request):
    if request.method == "POST":
        try:
            #CM2102NEWONT 
            # Get the current user name
            ThisUserid = request.user.id
            
            data = json.loads(request.body)
            uri = data.get("uri")
            fields = get_properties_of_a_class(uri, "./media/default_ontology/AdditionalProperties.ttl")
            return JsonResponse({"fields": fields}, status=200)
        except BaseException as e:
            print("ajax_get_properties_from_properties_file: ERROR : " + str(uri) + " / " + str(e))
            return JsonResponse({"error": str(e)}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

def has_none_value_on_first_level(d):
    """ Check if dictionary d has at least one None value on the first level """
    return any((value is None) or (value == '' and key == "value") for key, value in d.items())

def filter_dicts_with_none_values(data):
    """
    Recursively filter out dictionaries from data that have at least one None value on the first level.
    Handles nested lists and dictionaries.
    """
    if isinstance(data, list):
        filtered_list = []
        for item in data:
            if isinstance(item, dict):
                if not has_none_value_on_first_level(item):
                    filtered_list.append(filter_dicts_with_none_values(item))
            elif isinstance(item, list):
                filtered_list.append(filter_dicts_with_none_values(item))
            else:
                filtered_list.append(item)
        return filtered_list
    elif isinstance(data, dict):
        filtered_dict = {}
        for key, value in data.items():
            if isinstance(value, dict):
                if not has_none_value_on_first_level(value):
                    filtered_dict[key] = filter_dicts_with_none_values(value)
            elif isinstance(value, list):
                filtered_dict[key] = filter_dicts_with_none_values(value)
            else:
                filtered_dict[key] = value
        return filtered_dict
    else:
        return data
# @login_required(login_url="login")
# @user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
def convert_to_odrl(request):
    if request.method == "POST":
        # try:
            translator = LogicTranslator()
            response = json.loads(request.body)
            filtered_response = filter_dicts_with_none_values(response)
            odrl = convert_list_to_odrl_jsonld_no_user(filtered_response)

            try:
                odrl_parser = ODRLParser()
                policies = odrl_parser.parse_list([odrl])
                logic = translator.translate_policy(policies)
                return JsonResponse({"odrl": odrl, "formal_logic": logic, "data":filtered_response})
            except BaseException as b:
                return JsonResponse({"odrl": odrl})

            res = 200
            # res = _fetch_valid_status(odrl)

            #return JsonResponse(odrl)

        #return JsonResponse({"Policy": odrl, "response": res})
        # except BaseException as b:
        #     return JsonResponse({})
        #     #return b


def json_editor(request):
    # Define pre-existing keys and values here
    predefined_keys = ["uid", "@type", "profile", "prohibition", "target", "action", "assigner", "assignee",
                       "rdf:value"]
    predefined_values = [
        "http://example.com/policy:001", "Policy", "http://example.com/odrl:profile:10",
        "http://example.com/asset:123", "read", "http://example.com/book/1999",
        "http://example.com/org/paisley-park", "odrl:reproduce", "http://example.com/party:0001",
        "http://example.com/looking-glass.ebook", "Party", "vcard:Organization",
        "http://example.com/org/sony-books", "Sony Books LCC", "sony-contact@example.com",
        "PartyCollection", "vcard:Group", "http://example.com/team/A", "Team A",
        "teamA@example.com", "use", "http://example.com/document:1234", "http://example.com/org:616",
        "odrl:print"
    ]

    context = {
        'predefined_keys': predefined_keys,
        'predefined_values': predefined_values,
    }
    return render(request, 'editor.html', context)
def policy_create(request):
    return render(request, 'policy_create.html')

def get_dropdown_data(request):
    # Placeholder data - replace with your actual data fetching logic
    rule_data = [{"value": "http://www.w3.org/ns/odrl/2/Offer", "label": "Offer"},{"value": "http://www.w3.org/ns/odrl/2/Offer", "label": "Offer"}]
    actor_data = [{"value": "http://example.com/actor1", "label": "Actor 1"},{"value": "http://example.com/actor1", "label": "Actor 1"}]
    action_data = [{"value": "http://www.w3.org/ns/odrl/2/execute", "label": "Execute"}]
    purpose_data = [{"value": "http://example.com/purpose1", "label": "Purpose 1"}]
    target_data = [{"value": "http://example.com/target1", "label": "Target 1"}]
    constraint_data = [{"value": "http://example.com/constraint1", "label": "Constraint 1"}]
    operator_data = [{"value": "http://example.com/operator1", "label": "Operator 1"}]

    return JsonResponse({
        'rule_data': rule_data,
        'actor_data': actor_data,
        'action_data': action_data,
        'purpose_data': purpose_data,
        'target_data': target_data,
        'constraint_data': constraint_data,
        'operator_data': operator_data,
    })

@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
def convert_to_odrl_login(request):
    if request.method == "POST":
        try:
            response = json.loads(request.body)
            odrl = convert_list_to_odrl_jsonld(response)
            res = 200
            # res = _fetch_valid_status(odrl)
            return JsonResponse({"Policy": odrl, "response": res})
        except BaseException as b:
            return b

def get_uploaded_rules(request):
    if request.method == "GET":
        # Get the current user name
        ThisUserid = request.user.id
        
        # Get records for this user
        # odrls = ODRLRuleUpload.objects.all()
        odrls = ODRLRuleUpload.objects.filter(edit_uid = ThisUserid)
        
        odrl_list = [
            # 0311
            {"id": odrl.id, "name": odrl.name, "protection": odrl.protection}
            for odrl in odrls
        ]
        return JsonResponse({"odrls": odrl_list})
    return JsonResponse({"error": "Invalid request method."}, status=405)

# This not uid based as odrl_id assumed unique across users
def delete_rule(request, odrl_id):
    if request.method == "DELETE":
        try:
            odrl = ODRLRuleUpload.objects.get(id=odrl_id)
            odrl.delete()
            return JsonResponse({"message": "ODRL deleted successfully."})
        except ODRLRuleUpload.DoesNotExist:
            return JsonResponse({"error": "ODRL not found."}, status=404)
    return JsonResponse({"error": "Invalid request method."}, status=405)


def upload_rules(request):
    if request.method == "POST":
        try:
            # CMADDED
            # https://sentry.io/answers/how-do-i-access-parameters-from-the-url-as-part-the-httprequest-object/
            mode=request.GET.get("mode")
            print("The mode parameter is " + mode)
            
            # DEBUG
            # return JsonResponse({"message": "ODRL uploaded successfully.", "id": "TBC"})
            
            
            # Parse JSON content from the request body
            body_unicode = request.body.decode('utf-8')
            body_data = json.loads(body_unicode)

            # Validate required fields in the JSON structure
            name = body_data.get("name")
            print("The name is " + str(name))
            content = body_data.get("content")
            if not name or not content:
                return JsonResponse({"error": "Missing 'name' or 'content' in the request."}, status=400)

            # Save content to the database
            
            # CMADD
            #   Added check for mode
            #      create - behaves as previously
            #      update - updates an existing policy
            # Get the current user name
            ThisUserid = request.user.id
            #DEBUG
            # print("The user name is " + str(ThisUserid))
            
            if mode == "create":
 
                # Added try/except protecttion
                try:
                    odrl = ODRLRuleUpload.objects.create(
                     
                        # Added the current user name field
                        edit_uid = ThisUserid,
                
                        name=name,
                        content=json.dumps(content),
                        # CM0311
                        protection=1
                        # Save content as JSON string in the database
                    )
                except Exception as err:
                    print("The error message is " + str(err))
                    return JsonResponse({"error": "Unable to upload."}, status=405)
            else:
                
                
                print("<<>> Updating ")
                # Added try/except protecttion
                try:
                    odrltest = ODRLRuleUpload.objects.filter( # Extract the required queryset based on user id and name
                     
                        # Added the current user name field
                        edit_uid = ThisUserid,
                
                        name=name).first()
                    
                    print("The id returned is ", odrltest.id)
                    
                    #odrl = ODRLRuleUpload.objects.filter( # Extract the required queryset based on user id and name
                     
                        # Added the current user name field
                    #    edit_uid = ThisUserid,
                
                    #    name=name).update(
                    #        content=json.dumps(content))  # Update content as JSON string in the database
                            
                    odrl = ODRLRuleUpload.objects.get(# Added the current user name field
                        edit_uid = ThisUserid,                
                        name=name)
                    odrl.content = json.dumps(content)
                    odrl.save()
                   
                except Exception as err:
                    print("The error message is " + str(err))
                    return JsonResponse({"error": "Unable to upload."}, status=405)
                
            
            return JsonResponse({"message": "ODRL uploaded successfully.", "id": odrl.id})

        except json.JSONDecodeError:
            print("Found a JSONDecodeError")
            return JsonResponse({"error": "Invalid JSON format."}, status=400)
        except Exception as e:
            print("Found a general error " + str(e))
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)

# This not uid based as odrl_id assumed unique across users
def get_rule(request, odrl_id):
    if request.method == "GET":
        
        try:
            odrl = ODRLRuleUpload.objects.get(id=odrl_id)
            # Assuming the content is a valid JSON string
            print("<<<<<< IN get_rule: The rule data is " + str(odrl.content))
            import json
            content_json = json.loads(odrl.content)  # Convert string to JSON
            return JsonResponse({"id": odrl.id, "name": odrl.name, "content": content_json})
        except ODRLRuleUpload.DoesNotExist:
            return JsonResponse({"error": "ODRL not found."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format in content."}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)

def get_uploaded_ontologies(request):
    if request.method == "GET":
        
        # CM2102NEWONT
        # Also load the deault ontology into the list available
        
        # Get the default user id
        ThisUserid = 999999
        
        #
        # Get records for this user
        # ontologies = CustomOntologyUpload.objects.all()
        ontologies = CustomOntologyUpload.objects.filter(edit_uid = ThisUserid)
        
        ontology_list_default = [
            # CM0311
            {"id": ontology.id, "name": ontology.name, "type": ontology.ontology_type, "content": ontology.content, "protection": ontology.protection}
            for ontology in ontologies
        ]
        
        # Get the current user name
        ThisUserid = request.user.id
        
        #CMADDED 
        # Get records for this user
        # ontologies = CustomOntologyUpload.objects.all()
        ontologies = CustomOntologyUpload.objects.filter(edit_uid = ThisUserid)
        
        ontology_list = [
            # CM0311
            {"id": ontology.id, "name": ontology.name, "type": ontology.ontology_type, "content": ontology.content, "protection": ontology.protection}
            for ontology in ontologies
        ]
        return JsonResponse({"ontologies": ontology_list_default + ontology_list })
    return JsonResponse({"error": "Invalid request method."}, status=405)

# This not uid based as ontology_id assumed unique across users
def get_ontology(request, ontology_id):
    if request.method == "GET":
        ontology = CustomOntologyUpload.objects.get(id=ontology_id)
        return JsonResponse(ontology)
    return JsonResponse({"error": "Invalid request method."}, status=405)

# This not uid based as ontology_id assumed unique across users
def delete_ontology(request, ontology_id):
    if request.method == "DELETE":
        try:
            ontology = CustomOntologyUpload.objects.get(id=ontology_id)
            ontology.delete()
            return JsonResponse({"message": "Ontology deleted successfully."})
        except CustomOntologyUpload.DoesNotExist:
            return JsonResponse({"error": "Ontology not found."}, status=404)
    return JsonResponse({"error": "Invalid request method."}, status=405)

def upload_custom_ontology(request):
    if request.method == "POST":
        ontology_file = request.FILES.get("ontologyFile")
        if ontology_file:
            try:
                # Read file content
                file_content = ontology_file.read().decode("utf-8")

                # Save content to the database
                
                # Get the current user name
                ThisUserid = request.user.id
                #DEBUG
                # print("The user name is " + str(ThisUserid))
            
                # Added try/except protecttion
                try:
                    ontology = CustomOntologyUpload.objects.create(
                        # Added the current user name field
                        edit_uid = ThisUserid,
                
                        name=ontology_file.name,
                        content=file_content,
                        ontology_type=request.POST.get("ontologyType", "DATA_CONTEXT"),
                        # CM0311
                        protection = 1
                    )
                except Exception as err:
                    print("The error message is " + str(err))
                    return JsonResponse({"error": "Unable to upload."}, status=405)
                #ontology = CustomOntologyUpload.objects.create(
                #    name=ontology_file.name,
                #    content=file_content,
                #    ontology_type=request.POST.get("ontologyType", "DATA_CONTEXT")
                #)
                
                populate_content_to_graph(file_content,"xml")
                populate_content_to_graph(file_content,"ttl")
                return JsonResponse({"message": "Ontology uploaded successfully.", "id": ontology.id})
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)
        return JsonResponse({"error": "No file uploaded."}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)

# Added decorators to force user athentication for this page
@login_required(login_url="login")
#@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")
def create_rule_dataset_no_user(request):
    print("IN create_rule_no")
    print("The data received is " + str(DATAPACKET))
    
    # CMADDED
    # Now this page may be called directly via URL 
    # strengthen validation of query parameters supplied
    
    params=request.GET.items()
    
    # A list of accepted params and counts of those found to be present
    accepted_params={'mode':0,
                    'policy':0,
                    'target':0}
    
    # A list of accepted params that are additionaly mandatory    
    mandatory_params=['mode', 'policy']
    
    # A list of params that have a fixed set of acceptable values
    fixed_params={'mode':['update', 'create', 'delete', 'read']}
    
    # A working variable to store a list of accepted params (see above)
    param_list=list(accepted_params.keys())
    print("The param list is " + str(param_list))
    
    for item in request.GET.items():
        print("Parameter: " + str(item[0]) + " has value : " + str(item[1]))
        
    
    invalid_option_set_found=False
    invalid_option=True
    
    # Check that all parameter names provided are valid
    
    for next_param in params:
        print("The next param type is " + next_param[0])
        invalid_option=True
        for param_option in param_list:
            if next_param[0] == param_option:
                accepted_params[next_param[0]]+=1
                invalid_option=False
        if invalid_option == True:
            print("Invalid parameter found : " + next_param[0])
            break
            
            
    # Check that all valid parameter names are supplied just once
    # Belt and braces - Looks like django only passes through the last instance
            
    if invalid_option == True:
        invalid_option_set_found=True
    else:                
        for param_option in param_list:
            print("The count value for " + param_option + " is " + str(accepted_params[param_option]))
            if accepted_params[param_option] > 1:
                print("More than one " + param_option + " provided")
                invalid_option_set_found=True
                break
            
            for mandatory_param in mandatory_params:
                if not accepted_params[mandatory_param] == 1:
                    invalid_option_set_found=True
        
            if invalid_option_set_found == True:
                break
                
    # Check that parameters with fixed values have correct values
    
    for fixed_param in list(fixed_params.keys()):
        print("Checking values for " + fixed_param)
        invalid_option_value=True
        for option_value in fixed_params[fixed_param]:
            
            # Iterator needs to be reset
            params=request.GET.items()
            
            for next_param in params:
                
                if next_param[0] == fixed_param: 
                                       
                    if option_value == next_param[1]:
                        print("Found natch for parameter name " + next_param[0] + " : Value given " + next_param[1] + " : Option found " + option_value)
                        invalid_option_value=False
                    else:
                        print("Failed to match the given value " + str(next_param[1]) + " with test value " + str(option_value))
    
    if invalid_option_value == True:
        invalid_option_set_found=True        
            
    # If it is an invalid parmater set then send a 405 error
    
    if invalid_option_set_found == True:
        return JsonResponse({"error": "Invalid options"}, status=405)  
        
        
    
    # CM2102NEWONT
    # Get user id
    ThisUserid = request.user.id
    
    #
    # This view can be accessed directly by URL so check that
    #   if we are in update, read or delete mode that the requsted policy exists (for this user)
    request_mode = request.GET.get("mode")
    request_policy = request.GET.get("policy")
    
    if (request_mode == "update") or (request_mode == "read") or (request_mode == "delete"):
        checkResponse= check_rule_exists(ThisUserid, request_policy)
            
        if checkResponse == False:
             return JsonResponse({"error": "Policy name does not exist for this user"}, status=405) 
    
    if (request_mode == "create") :
        checkResponse= check_rule_exists(ThisUserid, request_policy)
            
        if checkResponse == True:
             return JsonResponse({"error": "Policy name already exists for this user"}, status=405) 
             
             
    
    # https://sentry.io/answers/how-do-i-access-parameters-from-the-url-as-part-the-httprequest-object/
    
    print("The policy parameter is " + request_policy)
    
    ontologies = get_uploaded_ontologies(request)
    # CM2102NEWONT - Need to spot format before trying to load
    for ontology in json.loads(ontologies.content)["ontologies"]:
        populate_content_to_graph(ontology["content"], "turtle", ThisUserid)
    #for ontology in json.loads(ontologies.content)["ontologies"]:
        #populate_content_to_graph(ontology["content"], "ttl")
    # CM2102NEWONT
    #populate_graph("./media/default_ontology/ODRL22.rdf","xml")
    #populate_graph("./media/default_ontology/dpv.ttl","turtle")
    #populate_graph("./media/default_ontology/dpv.rdf","xml")
    #  Now added to database when users created
    #populate_graph("./media/default_ontology/ODRL_DPV.rdf","xml")
    
    populate_graph("./media/default_ontology/Datasets.ttl","turtle", ThisUserid)
    populate_graph("./media/default_ontology/Datasets_with_metadata.ttl","turtle", ThisUserid)

    rules = get_rules_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    actors = get_actor_hierarchy_from_dpv("./media/default_ontology/dpv.ttl", ThisUserid)
    
    #f = open("myfile.txt", "x")
    #f = open("myfile.txt", "w")
    #f.write(str(actors))
    #f.close()
    
    actions = get_action_hierarchy_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    targets = get_dataset_titles_and_uris("./media/default_ontology/Datasets.ttl", ThisUserid)
    constraints = get_constraints_types_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    purposes = get_purpose_hierarchy_from_dpv("./media/default_ontology/dpv.rdf", ThisUserid)
    operators = get_operators_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)

    rules.append({"label": "Obligation", "uri": "http://www.w3.org/ns/odrl/2/Obligation"})

    context = {
        "policy": request_policy,
        "rules": rules,
        "actors": actors[0:1],
        "actions": actions,
        "targets": targets,
        "constraints": constraints,
        "operators": operators,
        "purposes": purposes,
    }
    print("IN create_rule_no part 2")
    return render(request, "../templates/policy/policy.html", context=context)
    
    
# CMADD
# Added decorators to force user athentication for this page
@login_required(login_url="login")
#@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")
def update_ontol(request):
    print("IN update_ontol")
    
    # CM2102NEWONT
    # Get user id
    ThisUserid = request.user.id
        
    # https://sentry.io/answers/how-do-i-access-parameters-from-the-url-as-part-the-httprequest-object/
    ontology=request.GET.get("ontology")
    print("The ontology parameter is " + ontology)
    
    ontologies = get_uploaded_ontologies(request)
    for ontology in json.loads(ontologies.content)["ontologies"]:
        if ontology["name"] == ontology:
            print("Building for names is " + next_custom["name"])
            #populate_content_to_graph(ontology["content"], "xml", ThisUserid)
            populate_content_to_graph(ontology["content"], "ttl", ThisUserid)
            
    #for ontology in json.loads(ontologies.content)["ontologies"]:
    #    populate_content_to_graph(ontology["content"], "xml")
    #for ontology in json.loads(ontologies.content)["ontologies"]:
    #    populate_content_to_graph(ontology["content"], "ttl")
    # CM2102NEWONT
    #populate_graph("./media/default_ontology/ODRL22.rdf","xml")
    #populate_graph("./media/default_ontology/dpv.ttl","turtle")
    #populate_graph("./media/default_ontology/dpv.rdf","xml")
    populate_graph("./media/default_ontology/ODRL_DPV.rdf","xml", ThisUserid)
    
    populate_graph("./media/default_ontology/Datasets.ttl","turtle", ThisUserid)
    populate_graph("./media/default_ontology/Datasets_with_metadata.ttl","turtle", ThisUserid)
    
            
    rules = get_rules_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    actors = get_actor_hierarchy_from_dpv("./media/default_ontology/dpv.ttl", ThisUserid)
    #print("The actor hierarchy is " + str(actors))
    actions = get_action_hierarchy_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    targets = get_dataset_titles_and_uris("./media/default_ontology/Datasets.ttl", ThisUserid)
    constraints = get_constraints_types_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
    purposes = get_purpose_hierarchy_from_dpv("./media/default_ontology/dpv.rdf", ThisUserid)
    operators = get_operators_from_odrl("./media/default_ontology/ODRL22.rdf", ThisUserid)
        
    rules.append({"label": "Obligation", "uri": "http://www.w3.org/ns/odrl/2/Obligation"})

    context = {
        "ontology": ontology,
        "rules": rules,
        "actors": actors,
        "actions": actions,
        "targets": targets,
        "constraints": constraints,
        "operators": operators,
        "purposes": purposes,
    }
    print("IN update_ontol")
    return render(request, "../templates/ontology/ontology.html", context=context)
    
# CMADD
# Added decorators to force user athentication for this page
@login_required(login_url="login")
#@user_passes_test(lambda u: u.role == "DATACONTROLLER_PROCESSOR")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")
def compare_policies(request):
    print("IN compare_policies")
    
    ThisUserid = request.user.id
    
    # Get records for this user
    # odrls = ODRLRuleUpload.objects.all()
    odrls = ODRLRuleUpload.objects.filter(edit_uid = ThisUserid)
        
    odrl_list = [
    # CM0311
        {"id": odrl.id, "name": odrl.name, "protection": odrl.protection}
        for odrl in odrls
    ]
    
    # CM2102NEWONT
    # Get default ontologies
    ontols_default = CustomOntologyUpload.objects.filter(edit_uid = 999999)
        
    ontol_list_default = [
        # CM0311
        {"id": ontol.id, "name": ontol.name, "protection": ontol.protection}
        for ontol in ontols_default
    ]
    
    # Get records for this user
    # odrls = ODRLRuleUpload.objects.all()
    ontols = CustomOntologyUpload.objects.filter(edit_uid = ThisUserid)
        
    ontol_list = [
        # CM0311
        {"id": ontol.id, "name": ontol.name, "protection": ontol.protection}
        for ontol in ontols
    ]
    
    # CustOntList=CustomOntologyUpload.objects.all()
    # SavedPols=ODRLRuleUpload.objects.all()
    
    StdOnts=["Application specific integration of ODRL and DPV"]
    context={"CustOntList":ontol_list_default + ontol_list, "SavedPols":odrl_list, "StdOnts":StdOnts}
        
    
    return render(request, "../templates/comparison/Comparison.html", context)

def extract_logic_expressions_page(request):

    return render(request, "../templates/policy/logic.html")

def extract_logic_expressions(request):
    translator = LogicTranslator()
    incoming_request = translator.odrl.parse_list(json.loads(str(request.body, "UTF")))
    print (incoming_request)
    result = translator.translate_policy(incoming_request)
    # return JsonResponse({"logic_expression":result})


    return JsonResponse(
        {
            "logic_expression": result
        }
    )
    
    
    
def testview(request):
    if request.method == "PUT":
        try:
            DATAPACKET=request.body
            
            print("The data received is " + str(request.body))
            print("The data received is " + str(request.method))
    
            DATAPACKET=request.body
    
            return JsonResponse({"NullCheck":0})
            # Can't do this as this is a PUT
            #return redirect(reverse("create_rule_dataset_no_user"))
            
        except BaseException as b:
                return bprint("The data received is " + str(request))
    #print("The data received is " + str(request.body))
    #print("The data received is " + str(request.method))
    
    #DATAPACKET=request.body
    
    #return JsonResponse({},status=200)
    #if request.method == "PUT":
        
    #    request.method = "GET"
    #    return redirect(reverse("create_rule_dataset_no_user"))
         

    #return render(request, "register_login/login.html")*/

# CM0311
@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")    
def toggle_ontology_api_visibility(request, ontology_id):
    if request.method == "POST":
        
                        
            # Get the current user id
            ThisUserid = request.user.id
            
                
            print("<<>> Toggle onotology visibility ")
            
            try:
                                            
                ontol = CustomOntologyUpload.objects.get(
                    edit_uid = ThisUserid,                
                    id = ontology_id)
                if ontol.protection==0:
                    ontol.protection=1
                    toggle_text="toggled from Public to Private"
                else:
                    ontol.protection=0
                    toggle_text="toggled from Private to Public"
                ontol.save()
                
            except CustomOntologyUpload.DoesNotExist:
                return JsonResponse({"error": "Ontology not found."}, status=404)
                   
            except Exception as err:
                print("The error message is " + str(err))
                return JsonResponse({"error": "Unable to make ontology public."}, status=405)
                
            
            return JsonResponse({"message": "Ontology " + toggle_text , "id": ontol.id})


    return JsonResponse({"error": "Invalid request method."}, status=405)
    
# CM0311
@login_required(login_url="login")
@user_passes_test(lambda u: u.role == "DATA_PROVIDER")    
def toggle_policy_api_visibility(request, policy_id):
    if request.method == "POST":
        
                        
            # Get the current user id
            ThisUserid = request.user.id
            
                
            print("<<>> Toggle policy visibility for " + str(policy_id))
            
            try:
                                            
                policy = ODRLRuleUpload.objects.get(
                    edit_uid = ThisUserid,                
                    id = policy_id)
                if policy.protection==0:
                    policy.protection=1
                    toggle_text="toggled from Public to Private"
                    print(toggle_text)
                else:
                    policy.protection=0
                    toggle_text="toggled from Private to Public"
                    print(toggle_text)
                policy.save()
                
            except ODRLRuleUpload.DoesNotExist:
                return JsonResponse({"error": "Policy not found."}, status=404)
                   
            except Exception as err:
                print("The error message is " + str(err))
                return JsonResponse({"error": "Unable to make policy public."}, status=405)
                
            
            return JsonResponse({"message": "Policy " + toggle_text , "id": policy.id})


    return JsonResponse({"error": "Invalid request method."}, status=405)
