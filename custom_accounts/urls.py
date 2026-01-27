from django.urls import path
from . import views
# UI STEP1
from django.contrib import admin

urlpatterns = [
    
    # TEST LINE
    # Convenience make sure commented out after use
    # UI STEP1
    #path("admin/", admin.site.urls),
    
    path("user/home", views.userhome, name="userhome"),
    
    path("organization/home", views.datacontrollerhome, name="datacontrollerhome"),
    path('policy/create/', views.policy_create, name='policy_create'),
    path('get-dropdown-data/', views.get_dropdown_data, name='get_dropdown_data'),
    path('json-editor', views.json_editor, name='json_editor'),

    path(
        "organization/convert_to_odrl",
        views.convert_to_odrl,
        name="convert_to_odrl",
    ),
    path(
        "organization/convert_to_odrl_login",
        views.convert_to_odrl_login,
        name="convert_to_odrl_login",
    ),
    path(
        "organization/ajax_get_fields_from_datasets",
        views.ajax_get_fields_from_datasets,
        name="ajax_get_fields_from_datasets",
    ),
    path(
        "organization/ajax_get_properties_from_properties_file",
        views.ajax_get_properties_from_properties_file,
        name="ajax_get_properties_from_properties_file",
    ),
    path(
        "organization/get_properties_of_a_class",
        views.ajax_get_properties_of_a_class,
        name="get_properties_of_a_class",
    ),
    path(
        "organization/get_constraints_for_instances",
        views.ajax_get_constraints_for_instances,
        name="get_constraints_for_instances",
    ),
    path(
        "create-rule",
        views.create_rule_dataset_no_user,
        name="create_rule_dataset_no_user",
    ),
    path(
        "create-logic",
        views.extract_logic_expressions_page,
        name="extract_logic_expressions_page",
    ),
    path(
        "extract_logic_expressions",
        views.extract_logic_expressions,
        name="extract_logic_expressions",
    ),
    path("organization/custom-ontology-upload", views.upload_custom_ontology, name="uploadcustomontology"),
    path('organization/get_uploaded_ontologies/', views.get_uploaded_ontologies, name='get_uploaded_ontologies'),
    path('organization/delete_ontology/<int:ontology_id>/', views.delete_ontology, name='delete_ontology'),
    path('organization/get_ontology/<int:ontology_id>/', views.get_ontology, name='get_ontology'),
    path("organization/rule-upload", views.upload_rules, name="uploadodrl"),
    #path('organization/get_uploaded_rules/', views.get_uploaded_rules, name='get_uploaded_odrls'),
    path('organization/get_uploaded_rules/', views.get_uploaded_rules, name='get_uploaded_rules'),
    path('organization/delete_rule/<int:odrl_id>/', views.delete_rule, name='delete_rule'),
    path('organization/get_rule/<int:odrl_id>/', views.get_rule, name='get_rule'),
    path("login", views.signin, name="login"),
    path("logout", views.signout, name="logout"),
    path("activate/<uidb64>/<token>", views.activate, name="activate"),
    path("sign-up", views.register, name="register"),

    # Changed the path rule here to begin at a 'splash' page
    #path("", views.create_rule_dataset_no_user, name="index"),
    path("update", views.create_rule_dataset_no_user, name="update"),
    #path("update*", views.create_rule_dataset_no_user, name="update"),

        
    #CMADD
    path("update_ontol", views.update_ontol, name="update_ontol"),
    path("", views.index, name="index"),
    
    
    path("compare", views.compare_policies, name="compare_policies"),
    
    path("testview", views.testview, name="testview"),
    path("callComparisonAPI", views.callComparisonAPI, name="testview"),
    
    path("review_public", views.review_public, name="review_public"),
    path('organization/get_public_rule/<int:odrl_id>/', views.get_public_rule, name='get_public_rule'),
    
    # CM0311
    path("organization/toggle_ontology_api_visibility/<int:ontology_id>/", views.toggle_ontology_api_visibility, name="toggle_ontology_api_visibility"),
    path("organization/toggle_policy_api_visibility/<int:policy_id>/", views.toggle_policy_api_visibility, name="toggle_policy_api_visibility")
    
]
