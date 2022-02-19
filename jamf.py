#!/usr/bin/env python3

"""
Script:	jamf.py
Date:	2020-01-10
Platform: macOS/Linux
Description:
Jamf classes to manage and interact with the APIs

v2 - Removed all dependencies for external libraries
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '2.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

import base64
import json
import logging
import ssl
import urllib.error
import urllib.request
import urllib.request


class APIResponse:
    """
    Data object containing data of the query
    :property success: (bool) success of the call
    :property url: (str) url that was called
    :property response: (str, json) depending on the success
    :property http_code: (int) http code returned
    :property err: (str) Error if exception
    """

    def __init__(self, success: bool = False, url: str = None, response: str = None, http_code: int = 0,
                 err: str = None, **kwargs):
        """
        Initialisation method
        :param success: (bool) success of the call
        :param url: (str) url that was called
        :param response: (str, json) depending on the success
        :param http_code: (int) http code returned
        :param err: (str) Error if exception
        :param kwargs: (dict)
        """
        self.success = kwargs['success'] if 'success' in kwargs else success
        self.url = kwargs['url'] if 'url' in kwargs else url
        self.response = kwargs['response'] if 'response' in kwargs else response
        if isinstance(self.response, dict):
            self.__dict__['d'] = self.response
        self.http_code = kwargs['http_code'] if 'http_code' in kwargs else http_code
        self.err = kwargs['err'] if 'err' in kwargs else err

        self.data = self.response

    def success(self, success: bool = None) -> bool:
        """
        :param success: Set or retrieve property success
        :return: (bool) Current/new setting
        """
        if success is not None:
            self.success = bool(success)

        return self.success

    def response(self, response: str = None) -> str:
        """
        :param response: Set or retrieve property response
        :return: (int) Current/new setting
        """
        if response is not None:
            self.response = self.data = response

        return self.response

    def http_code(self, http_code: int = None) -> int:
        """
        :param http_code: Set or retrieve property http_code
        :return: (int) Current/new setting
        """
        if http_code is not None:
            self.http_code = int(http_code)

        return self.http_code

    def err(self, err: str = None) -> float:
        """
        :param err: Set or retrieve property err
        :return: (int) Current/new setting
        """
        if err is not None:
            self.err = float(err)

        return self.err


class JamfClassic:
    """
    JamfClassic interacts with the classic API of Jamf
    """

    def __init__(self, api_url: str, username: str, password: str, *args, **kwargs):
        """
        Initialisation method
        :param api_url: (str) url of the api
        :param username: (str) username
        :param password: (str) password
        :param args: (list)
        :param kwargs: (dict)
        """
        self.__api_url = api_url
        self.__username = username
        self.__password = password

        self.__headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/xml',
            'User-Agent': 'lynx',
        }
        self.__timeout = int(kwargs['timeout']) if 'timeout' in kwargs else 240.0
        self.__verify = bool(kwargs['verify']) if 'verify' in kwargs else True
        self.__disable_warnings = bool(kwargs['disable_warnings']) if 'disable_warnings' in kwargs else False
        self.__proxy = kwargs['proxy'] if 'proxy' in kwargs else {}

        if self.__disable_warnings:
            urllib3.disable_warnings()

    def __del__(self):
        """
        Destruction method
        :return: (void)
        """
        try:
            del self.__username
            del self.__password
        except AttributeError:
            pass

    def __enter__(self):
        """
        Support for the with command
        :return: (JamfClassic) self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Destruction method
        :param exc_type: None
        :param exc_val: None
        :param exc_tb: None
        :return: (void)
        """
        self.__del__()

    def timeout(self, timeout: int = None) -> float:
        """
        Set or retrieve the timeout
        :param timeout: (int) new value or (None) to remain
        :return: (int) Current/new setting
        """
        if timeout is not None:
            self.__timeout = float(timeout)

        return self.__timeout

    def verify_ssl(self, verify: bool = None) -> bool:
        """
        Set or retrieve whether to verify teh SSL certificate
        :param verify: (bool) new value or (None) to remain
        :return: (bool) Current/new setting
        """
        if verify is not None and isinstance(verify, bool):
            self.__verify = verify

        return self.__verify

    def get_data(self, *objects, **kwargs) -> urllib.request:
        """
        GET from the api
        :param objects: (list) of objects ex. /JSSResource/computer/id/0 = ['computer', 'id', 0]
        :param kwargs: None
        :return:
        """
        if not objects:
            return APIResponse(response='No object specified')

        # Get data
        request_url = f'{self.__api_url}/JSSResource/{"/".join(str(arg) for arg in objects)}'
        try:
            request = self.request(request_url, params=kwargs, auth=(self.__username, self.__password),
                                   headers=self.__headers, timeout=self.__timeout, verify=self.__verify)
        except urllib.error.URLError as err:
            return APIResponse(url=request_url, err=err)

        return request

    def request(self, url: str, method: str = 'GET', data: dict = None, auth: tuple = None, params: dict = None,
                headers: dict = None, timeout: int = 120, verify: bool = True) -> urllib.request:
        # Set defaults
        params = params if params else {}
        headers = headers if headers else {}

        # SSL validations
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
        context.check_hostname = verify
        context.load_default_certs()

        # Url parameters
        parameters = self.get_params(params)

        try:
            url_request = urllib.request.Request(url + parameters, data=data, headers=headers, method=method)
            if auth:
                basic_encoded = base64.standard_b64encode(f'{auth[0]}:{auth[1]}'.encode('ascii'))
                url_request.add_header('Authorization', f'Basic {basic_encoded.decode("ascii")}')
            with urllib.request.urlopen(url_request, timeout=timeout, context=context) as response:
                response.text = response.read()
                setattr(response, 'success', True if 200 <= response.code < 300 else False)
                try:
                    setattr(response, 'data', json.loads(response.text))
                except (UnicodeDecodeError, json.decoder.JSONDecodeError):
                    setattr(response, 'data', dict(text=response.text))
        except urllib.error.HTTPError as err:
            logging.error(err)

        return response

    @staticmethod
    def get_params(params: dict) -> str:
        def parse(value=None, key=None):
            parsed_params = []
            if isinstance(value, dict):
                for key, value in value.items():
                    parsed_params.extend(parse(value, key))
            elif isinstance(value, list):
                for item in value:
                    parsed_params.append(f'{key}={item}')
            else:
                parsed_params.append(f'{key}={value}')

            return parsed_params

        param_options = parse(params)
        if len(param_options) > 0:
            return f'?{"&".join(param_options)}'
        else:
            return ''


class JamfUAPI:
    """
    JamfUAPI interacts with the universal API of Jamf
    """

    def __init__(self, api_url: str, username: str, password: str, *args, **kwargs):
        """
        Initialisation method
        :param api_url: (str) url of the api
        :param username: (str) username
        :param password: (str) password
        :param args: (list)
        :param kwargs: (dict)
        """
        self.__api_url = api_url
        self.__username = username
        self.__password = password
        self._token = None

        self.__headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'lynx',
        }
        self.__timeout = int(kwargs['timeout']) if 'timeout' in kwargs else 240.0
        self.__verify = bool(kwargs['verify']) if 'verify' in kwargs else True
        self.__disable_warnings = bool(kwargs['disable_warnings']) if 'disable_warnings' in kwargs else False

        if self.__disable_warnings:
            urllib3.disable_warnings()

        self.__login()

    def __del__(self):
        """
        Destruction method
        :return: (void)
        """
        try:
            self.request(f'{self.__api_url}/api/v1/auth/invalidate-token', method='POST',
                         headers=self.__headers, timeout=self.__timeout, verify=self.__verify, data=None)
        except urllib.error.HTTPError:
            return None

        self._token = None
        self.__headers = None

    def __enter__(self):
        """
        Support for the with command
        :return: (JAMFUAPI) self
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Destruction method
        :param exc_type: None
        :param exc_val: None
        :param exc_tb: None
        :return: (void)
        """
        self.__del__()

    def __login(self):
        """
        Initialise the login
        :return: (APIResponse)
        """
        url = f'{self.__api_url}/api/v1/auth/token'

        try:
            request = self.request(url, method='POST', auth=(self.__username, self.__password),
                                   headers=self.__headers, timeout=self.__timeout, verify=self.__verify, data=None)
        except urllib.error.HTTPError as err:
            return APIResponse(url=url, err=err)

        if 200 <= request.code < 300:
            self._token = request.data['token']
            self.__headers['Authorization'] = f'Bearer {self._token}'
            return request
        else:
            self._token = None
            return request

    def renew_token(self) -> urllib.request:
        """
        Renew the login token
        :return: (APIResponse)
        """
        url = f'{self.__api_url}/api/v1/auth/keep-alive'

        try:
            request = self.request(url, method='POST',
                                   headers=self.__headers, timeout=self.__timeout, verify=self.__verify, data=None)
        except urllib.error.HTTPError as err:
            return APIResponse(url=url, err=err)

        if 200 <= request.code < 300:
            self._token = request.data['token']
            self.__headers['Authorization'] = f'Bearer {self._token}'
            return request
        else:
            return request

    def timeout(self, timeout: int = None) -> float:
        """
        Set or retrieve the timeout
        :param timeout: (int) new value or (None) to remain
        :return: (int) Current/new setting
        """
        if timeout is not None:
            self.__timeout = float(timeout)

        return self.__timeout

    def verify_ssl(self, verify: bool = None) -> bool:
        """
        Set or retrieve whether to verify teh SSL certificate
        :param verify: (bool) new value or (None) to remain
        :return: (bool) Current/new setting
        """
        if verify is not None and isinstance(verify, bool):
            self.__verify = verify

        return self.__verify

    def get_login(self) -> dict:
        """
        Get login information
        :return: (APIResponse)
        """
        return self.get_data('auth')

    def get_data(self, *objects: any, **params: dict) -> urllib.request:
        """
        GET from the api
        :param objects: (list) of objects ex. /uapi/computer/id/0 = ['computer', 'id', 0]
        :param params: (dict) options ex: sort=asc
        :return: (APIResponse)
        """
        if not objects:
            return APIResponse(response='No object specified')

        # Get data
        url = f'{self.__api_url}/uapi/{"/".join(str(arg) for arg in objects)}'
        try:
            request = self.request(url, params=params,
                                   headers=self.__headers, timeout=self.__timeout, verify=self.__verify)
        except requests.exceptions.HTTPError as err:
            return APIResponse(url=url, err=err)

        return request

    def request(self, url: str, method: str = 'GET', data: dict = None, auth: tuple = None, params: dict = None,
                headers: dict = None, timeout: int = 120, verify: bool = True) -> urllib.request:
        # Set defaults
        params = params if params else {}
        headers = headers if headers else {}

        # SSL validations
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.verify_mode = ssl.CERT_REQUIRED if verify else ssl.CERT_NONE
        context.check_hostname = verify
        context.load_default_certs()

        # Url parameters
        parameters = self.get_params(params)

        try:
            url_request = urllib.request.Request(url + parameters, data=data, headers=headers, method=method)
            if auth:
                basic_encoded = base64.standard_b64encode(f'{auth[0]}:{auth[1]}'.encode('ascii'))
                url_request.add_header('Authorization', f'Basic {basic_encoded.decode("ascii")}')
            with urllib.request.urlopen(url_request, timeout=timeout, context=context) as response:
                response.text = response.read()
                setattr(response, 'success', True if 200 <= response.code < 300 else False)
                try:
                    setattr(response, 'data', json.loads(response.text))
                except (UnicodeDecodeError, json.decoder.JSONDecodeError):
                    setattr(response, 'data', dict(text=response.text))
        except urllib.error.HTTPError as err:
            logging.error(err)

        return response

    @staticmethod
    def get_params(params: dict) -> str:
        def parse(value=None, key=None):
            parsed_params = []
            if isinstance(value, dict):
                for key, value in value.items():
                    parsed_params.extend(parse(value, key))
            elif isinstance(value, list):
                for item in value:
                    parsed_params.append(f'{key}={item}')
            else:
                parsed_params.append(f'{key}={value}')

            return parsed_params

        param_options = parse(params)
        if len(param_options) > 0:
            return f'?{"&".join(param_options)}'
        else:
            return ''
