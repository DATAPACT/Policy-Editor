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

# @Time    : 19.12.23 20:23
# @Author  : Tek Raj Chhetri
# @Email   : tekraj.chhetri@cair-nepal.org
# @Web     : https://tekrajchhetri.com/
# @File    : models.py
# @Software: PyCharm


from django.contrib.auth.models import AbstractUser
from django.db import models
from django_currentuser.db.models import CurrentUserField

"""
DATA_PROVIDER: The term data provider here represent the data subject in GDPR terminology, who owns or produce the data.
DATACONTROLLER_PROCESSOR: The term data controller and data processor here represent the data controller and data processor in GDPR terminology, who process the data from the data subject or the other data controller, i.e., process on the behalf of another controller.
"""
USER_TYPES = (
    ("DATA_PROVIDER", "Data Subject/Data Provider"),
    ("DATACONTROLLER_PROCESSOR", "Data Contact/Data Processor"),
    # ("ADMIN", "Admin"),
)

CONSENT_FORM_DELETE_STATUS = (("ACTIVE", "Active"), ("DELETED", "Deleted"))

USER_CONSENT_ANSWER_STATUS = (
    ("REQUESTED", "Requested"),
    ("RESPONDED", "Responded"),
    ("REVOKED", "Revoked"),
)

REQUEST_STATUS = (("SENT", "Sent"), ("CREATED", "Created"))

ONTOLOGY_TYPES_CHOICES = (
    ("DATA_CONTEXT", "Data and Context Information Ontology"),
    ("CONSENT", "Consent Ontology with Purpose and Data Processing Operations"),
    ("CUSTOM_CONSTANT", "Use case specific privacy constraints ontology"),
)

class User(AbstractUser):
    role = models.CharField(default="DATA_PROVIDER", choices=USER_TYPES, max_length=100)

class CustomOntologyUpload(models.Model):
    """
    Model to handle uploaded ontology file content stored as a string,
    along with metadata and related information.
    """
    id = models.AutoField(primary_key=True)
    # Added line below to add a user column
    # Default just there for migration
    edit_uid = models.IntegerField(default=0, help_text="Id of the user who added this rule.")
    name = models.CharField(max_length=100, help_text="Name of the ontology.")
    content = models.TextField(help_text="Ontology file content as a string.")
    ontology_type = models.CharField(
        max_length=150,
        choices=ONTOLOGY_TYPES_CHOICES,
        default="DATA_CONTEXT",
        help_text="Type of ontology being uploaded."
    )
    # CM0311 - 'Privacy' Flag for use with API
    protection = models.IntegerField(default=1, help_text="Determines API visibility of the ontologies. 0 Public 1 Private")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated.")

    def __str__(self):
        return self.name

class ODRLRuleUpload(models.Model):
    """
    Model to handle uploaded ontology file content stored as a string,
    along with metadata and related information.
    """
    id = models.AutoField(primary_key=True)
    # Added line below to add a user column
    # Default just there for migration
    edit_uid = models.IntegerField(default=0, help_text="Id of the user who added this rule.")
    name = models.CharField(max_length=100, help_text="Name of the ontology.")
    content = models.TextField(help_text="Json content as a string.")
    # CM0311 - 'Privacy' Flag for use with API
    protection = models.IntegerField(default=1, help_text="Determines API visibility of the policies. 0 Public 1 Private")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated.")

    def __str__(self):
        return self.name
