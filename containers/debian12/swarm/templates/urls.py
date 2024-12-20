""" VirES Swarm server URL Configuration
"""

from django.urls import include, path, re_path
from eoxserver.services.views import ows
from eoxs_allauth.views import wrap_protected_api, wrap_open_api, workspace
from eoxs_allauth.urls import document_urlpatterns
from vires.client_state import parse_client_state
from vires.views import custom_data #, custom_model, client_state
from vires.hapi.urls import urlpatterns as hapi_urlpatterns

urlpatterns = [
    path('', workspace(parse_client_state), name="workspace"),
    path('ows', wrap_protected_api(ows), name="ows"),
    path('hapi/', include(hapi_urlpatterns)),
    path('accounts/', include('eoxs_allauth.urls')),
    re_path(r'^custom_data/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(custom_data)),
    #re_path(r'^custom_model/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(custom_model)),
    #re_path(r'^client_state/(?P<identifier>[0-9a-f-]{36,36})?$', wrap_protected_api(client_state)),
] + document_urlpatterns
