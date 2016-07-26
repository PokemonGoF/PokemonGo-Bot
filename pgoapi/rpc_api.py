"""
pgoapi - Pokemon Go API
Copyright (c) 2016 tjado <https://github.com/tejado>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.

Author: tjado <https://github.com/tejado>
"""

from __future__ import absolute_import

import re
import logging
import requests
import subprocess

from importlib import import_module

from pgoapi.protobuf_to_dict import protobuf_to_dict
from pgoapi.exceptions import NotLoggedInException, ServerBusyOrOfflineException
from pgoapi.utilities import f2i, h2f, to_camel_case

from . import protos
from POGOProtos.Networking.Envelopes_pb2 import RequestEnvelope
from POGOProtos.Networking.Envelopes_pb2 import ResponseEnvelope
from POGOProtos.Networking.Requests_pb2 import RequestType

class RpcApi:
    
    def __init__(self, auth_provider):
    
        self.log = logging.getLogger(__name__)
    
        self._session = requests.session()
        self._session.headers.update({'User-Agent': 'Niantic App'})
        self._session.verify = True
        
        self._auth_provider = auth_provider
    
    def get_rpc_id(self):
        return 8145806132888207460

    def decode_raw(self, raw):
        output = error = None
        try:
            process = subprocess.Popen(['protoc', '--decode_raw'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate(raw)
        except:
            output = "Couldn't find protoc in your environment OR other issue..."
            
        return output
    
    def get_class(self, cls):
        module_, class_ = cls.rsplit('.', 1)
        class_ = getattr(import_module(module_), class_)
        return class_
        
    def _make_rpc(self, endpoint, request_proto_plain):
        self.log.debug('Execution of RPC')
        
        request_proto_serialized = request_proto_plain.SerializeToString()
        try:
            http_response = self._session.post(endpoint, data=request_proto_serialized)
        except requests.exceptions.ConnectionError as e:
            raise ServerBusyOrOfflineException
        
        return http_response
    
    def request(self, endpoint, subrequests, player_position):
    
        if not self._auth_provider or self._auth_provider.is_login() is False:
            raise NotLoggedInException()
    
        request_proto = self._build_main_request(subrequests, player_position)
        response = self._make_rpc(endpoint, request_proto)
        
        response_dict = self._parse_main_response(response, subrequests)

        if isinstance(response_dict, dict) and 'status_code' in response_dict:
            sc = response_dict['status_code']
            if sc == 102:
                raise NotLoggedInException()

        return response_dict
    
    def _build_main_request(self, subrequests, player_position = None):
        self.log.debug('Generating main RPC request...')
        
        request = RequestEnvelope()
        request.status_code = 2
        request.request_id = self.get_rpc_id()
        
        if player_position is not None:
            request.latitude, request.longitude, request.altitude = player_position
        
        # ticket = self._auth_provider.get_ticket()
        # if ticket:
            # request.auth_ticket.expire_timestamp_ms, request.auth_ticket.start, request.auth_ticket.end = ticket
        # else:
        request.auth_info.provider = self._auth_provider.get_name()
        request.auth_info.token.contents = self._auth_provider.get_token()
        request.auth_info.token.unknown2 = 59
        
        # unknown stuff
        request.unknown12 = 989
        
        request = self._build_sub_requests(request, subrequests)
        
        self.log.debug('Generated protobuf request: \n\r%s', request )
        
        return request
    
    def _build_sub_requests(self, mainrequest, subrequest_list):
        self.log.debug('Generating sub RPC requests...')
            
        for entry in subrequest_list:
            if isinstance(entry, dict):
            
                entry_id = list(entry.items())[0][0]
                entry_content = entry[entry_id]

                entry_name = RequestType.Name(entry_id)
                
                proto_name = to_camel_case(entry_name.lower()) + 'Message'
                proto_classname = 'POGOProtos.Networking.Requests.Messages_pb2.' + proto_name
                subrequest_extension = self.get_class(proto_classname)()
                
                self.log.debug("Subrequest class: %s", proto_classname)

                for (key, value) in entry_content.items():
                    if isinstance(value, list):
                        self.log.debug("Found list: %s - trying as repeated", key)
                        for i in value:
                            try:
                                self.log.debug("%s -> %s", key, i)
                                r = getattr(subrequest_extension, key)
                                r.append(i)
                            except Exception as e:
                                self.log.warning('Argument %s with value %s unknown inside %s (Exception: %s)', key, i, proto_name, str(e))
                    else:
                        try:
                            setattr(subrequest_extension, key, value)
                        except Exception as e:
                            try:
                                self.log.debug("%s -> %s", key, value)
                                r = getattr(subrequest_extension, key)
                                r.append(value)
                            except Exception as e:
                                self.log.warning('Argument %s with value %s unknown inside %s (Exception: %s)', key, value, proto_name, str(e))

                subrequest = mainrequest.requests.add()
                subrequest.request_type = entry_id
                subrequest.request_message = subrequest_extension.SerializeToString()
                
            elif isinstance(entry, int):
                subrequest = mainrequest.requests.add()
                subrequest.request_type = entry
            else:
                raise Exception('Unknown value in request list')
    
        return mainrequest
        
    
    def _parse_main_response(self, response_raw, subrequests):
        self.log.debug('Parsing main RPC response...')
        
        if response_raw.status_code != 200:
            self.log.warning('Unexpected HTTP server response - needs 200 got %s', response_raw.status_code)
            self.log.debug('HTTP output: \n%s', response_raw.content.decode('utf-8'))
            return False
        
        if response_raw.content is None:
            self.log.warning('Empty server response!')
            return False
    
        response_proto = ResponseEnvelope()
        try:
            response_proto.ParseFromString(response_raw.content)
        except google.protobuf.message.DecodeError as e:
            self.log.warning('Could not parse response: %s', str(e))
            return False
        
        self.log.debug('Protobuf structure of rpc response:\n\r%s', response_proto)
        try:
            self.log.debug('Decode raw over protoc (protoc has to be in your PATH):\n\r%s', self.decode_raw(response_raw.content).decode('utf-8'))
        except:
            self.log.debug('Error during protoc parsing - ignored.')
       
        response_proto_dict = protobuf_to_dict(response_proto)
        response_proto_dict = self._parse_sub_responses(response_proto, subrequests, response_proto_dict)
        
        return response_proto_dict
    
    def _parse_sub_responses(self, response_proto, subrequests_list, response_proto_dict):
        self.log.debug('Parsing sub RPC responses...')
        response_proto_dict['responses'] = {}
        
        if 'returns' in response_proto_dict:
            del response_proto_dict['returns']

        list_len = len(subrequests_list) -1
        i = 0
        for subresponse in response_proto.returns:
            if i > list_len:
                self.log.info("Error - something strange happend...")
            
            request_entry = subrequests_list[i]
            if isinstance(request_entry, int):
                entry_id = request_entry
            else:
                entry_id =  list(request_entry.items())[0][0]
                
            entry_name = RequestType.Name(entry_id)
            proto_name = to_camel_case(entry_name.lower()) + 'Response'
            proto_classname = 'POGOProtos.Networking.Responses_pb2.' + proto_name
            
            self.log.debug("Parsing class: %s", proto_classname)
            
            subresponse_return = None
            try:
                subresponse_extension = self.get_class(proto_classname)()         
            except Exception as e:
                subresponse_extension = None
                error = 'Protobuf definition for {} not found'.format(proto_classname)
                subresponse_return = error
                self.log.debug(error)
            
            if subresponse_extension:
                try: 
                    subresponse_extension.ParseFromString(subresponse)
                    subresponse_return = protobuf_to_dict(subresponse_extension)
                except:
                    error = "Protobuf definition for {} seems not to match".format(proto_classname)
                    subresponse_return = error
                    self.log.debug(error)
            
            response_proto_dict['responses'][entry_name] = subresponse_return
            i += 1
           
        return response_proto_dict
