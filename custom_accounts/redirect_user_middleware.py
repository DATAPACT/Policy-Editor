# -*- coding: utf-8 -*-
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

# @Time    : 20.12.23 12:27
# @Author  : Tek Raj Chhetri
# @Email   : tekraj.chhetri@cair-nepal.org
# @Web     : https://tekrajchhetri.com/
# @File    : redirect_user_middleware.py
# @Software: PyCharm

from django.shortcuts import redirect
from django.urls import reverse


class UserRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        if request.user.is_authenticated and request.path == reverse("index"):
            if request.user.role == "DATACONTROLLER_PROCESSOR":
                return redirect("datacontrollerhome")
            elif request.user.role == "DATA_PROVIDER":
                # Changed the redirect here for the moment to support basic login demo
                # return redirect("userhome")
                #return redirect("create_rule_dataset_no_user")
                print("The request paramters found in UserRedrectMiddleware are " + str(request.GET))
                return redirect("userhome")

        response = self.get_response(request)

        return response
