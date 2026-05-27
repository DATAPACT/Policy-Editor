import json
from django.conf import settings


def sso_config(request):
    """Injects SSO trusted origins into all template contexts."""
    return {
        "SSO_TRUSTED_ORIGINS_JSON": json.dumps(settings.FRAME_ANCESTORS),
    }