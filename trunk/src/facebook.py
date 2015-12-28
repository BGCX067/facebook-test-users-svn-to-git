'''
Created on 2011-04-13

@author: Steve Pennington
'''

import re
import json
import urllib
import urllib2

def dictToCSV(permissions):
    if permissions is not None:
        return ','.join(i for i in permissions)
    else:
        return ''

class Facebook:
    '''
    Provides high level functionality for interacting with the Facebook
    Graph API focusing on app related connections
    '''
    
    def __init__(self, appId, appSecret):
        self.appId = appId
        self.appSecret = appSecret
        self.appAccessToken = self.__accessToken()
        
    def __accessToken(self):
        args = {'client_id': self.appId, 'client_secret': self.appSecret, 'grant_type': 'client_credentials'}
        accessTokenResponse = self.graph('/oauth/access_token', args)
        match = re.match('access_token=(.+)', accessTokenResponse)
        return match.group(1)
    
    def graph(self, path, args=None, post_args=None, access_token=None):
        '''
        GET or POST data to the Facebook Graph.
        
        If post_args is provided a POST request is made,
        otherwise a GET request is made.
        
        path should be the facebook path such as:
        /app_id/accounts/test-users
        '''
        if not args: args = {}
        if access_token:
            if post_args is not None:
                post_args['access_token'] = access_token
            else:
                args['access_token'] = access_token
        post_data = None if post_args is None else urllib.urlencode(post_args)
        file = urllib2.urlopen('https://graph.facebook.com/' + path.strip('/') + '?' +
                              urllib.urlencode(args), post_data)
        try:
            response = file.read()
        finally:
            file.close()
        return response
    
    def graphJson(self, path, args=None, post_args=None, access_token=None):
        '''
        Execute a graph request and parse the response as JSON
        '''
        response = self.graph(path, args, post_args, access_token)
        return json.JSONDecoder().decode(response)
            
    def createTestUser(self, installed=True, permissions=None):
        '''
        Create a new test user. If installed is False permissions
        are ignored.
        
        Returns a FacebookTestUser
        '''
        if(installed):
            post_args = {'installed': 'true', 'permissions': dictToCSV(permissions)}
        else:
            post_args = {'installed': 'false' }
            
        response = self.graphJson('/%s/accounts/test-users' % self.appId, post_args=post_args, access_token=self.appAccessToken)
        if response.get('error'):
            raise Exception(response['error']['type'] + ': ' + response['error']['message'])
        return FacebookTestUser(response['id'], response['access_token'], response['login_url'])
    
    def friendRequest(self, user1, user2):
        '''
        Create a friend request from user1 to user2. 
        Note that a bi-directional friend request is considered
        an accepted friend request by Facebook. So, calling this
        twice will accept a friend reqeust. Ex.
        
        friendRequest(user1, user2)
        friendRequest(user2, user1)
        '''
        url = '/%s/friends/%s' % (user1.id,  user2.id)
        return self.graph(url, access_token=user1.accessToken)
    
    def userRequest(self, userId, message, data):
        '''
        Send an application request to the user.
        '''
        return self.graph('/%s/apprequests' % (userId), 
                          post_args={'message': message, 'data': data},
                          access_token=self.__accessToken())

class FacebookTestUser:
    '''
    Storage object for test user data
    '''
    def __init__(self, id, accessToken, loginUrl):
        self.id = id
        self.accessToken = accessToken
        self.loginUrl = loginUrl