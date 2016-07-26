
from __future__ import absolute_import

from pgoapi.exceptions import PleaseInstallProtobufVersion3

import pkg_resources

protobuf_exist = False
protobuf_version = 0
try:
    protobuf_version = pkg_resources.get_distribution("protobuf").version
    protobuf_exist = True
except:
    pass

if (not protobuf_exist) or (int(protobuf_version[:1]) < 3):
    raise PleaseInstallProtobufVersion3()

from pgoapi.pgoapi import PGoApi
from pgoapi.rpc_api import RpcApi
from pgoapi.auth import Auth

try:
    import requests.packages.urllib3
    requests.packages.urllib3.disable_warnings()
except:
    pass