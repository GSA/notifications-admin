from flask_basicauth import BasicAuth
from flask import jsonify, request

class CustomBasicAuth(BasicAuth):
    """
        Description:

        Usage:

    """
    
    def check_credentials(self, username, password):
        # here, for example, you can search user in the database by passed `username` and `password`, etc.
        return username == 'user' and password == 'password'


custom_basic_auth = CustomBasicAuth()