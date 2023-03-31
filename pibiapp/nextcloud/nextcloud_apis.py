# Copyright (c) 2018-2019, Dolores Juliana Fdez Martin
# License: GNU General Public License v3. See license.txt
#
# This file is part of Pibiapp_Nextcloud.
#
# Pibiapp_Nextcloud is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation, version 3 of the License.
#
# Pibiapp_Nextcloud is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY  or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pibiapp_Nextcloud included in the license.txt file.
# If not, see <https://www.gnu.org/licenses/>.

import requests
from numbers import Number
import json
import os
import xml.etree.ElementTree as ET

class WebdavException(Exception):
	pass

class WebDav(object):
    def __init__(self, host, port=0, auth=None, username=None, password=None,
                 protocol='http', verify_ssl=True, path=None, cert=None):

        vurl = host.replace("//","").split(":")
        if vurl[0] == "http" or vurl[0] == "https":
          protocol = vurl[0]
          host = vurl[1]
          if len(vurl) == 3:
            port = vurl[2]

        # If the NextCloud version requires a port, it must be specified in the parameter Script URL
        # https://mynextcloud.com:443 if protocol == 'https' else 80
        if not port:
            self.baseurl = '{0}://{1}'.format(protocol, host)
        else:
            self.baseurl = '{0}://{1}:{2}'.format(protocol, host, port)
	
        if path:
            self.baseurl = '{0}/{1}'.format(self.baseurl, path)
        self.cwd = '/'
        self.session = requests.session()
        self.session.verify = verify_ssl
        self.session.stream = True

        if cert:
            self.session.cert = cert

        if auth:
            self.session.auth = auth
        elif username and password:
            self.session.auth = (username, password)

    def getUrl(self, path):
        try: path = str(path).strip()
        except UnicodeEncodeError: path = path.encode("ascii", "ignore").decode("ascii").strip()
        if path.startswith('/'):
            return self.baseurl + path
        return "".join((self.baseurl, self.cwd, path))

    def command(self, method, path, expected_code, **kwargs):
        url = self.getUrl(path)
        response = self.session.request(method, url, allow_redirects=False, **kwargs)
        if isinstance(expected_code, Number) and response.status_code != expected_code \
            or not isinstance(expected_code, Number) and response.status_code not in expected_code:
            msg = "Webdav Exception: " + str(response.status_code) + " Method: " + method + " " + url 
            raise WebdavException(msg)
        return response

    def search_path(self, nc_path):
        response = self.command('HEAD', nc_path, (200, 301, 404))
        return True if response.status_code != 404 else False

    def cd(self, nc_path):
        path = nc_path.strip()
        if not path:
            return
        stripped_path = '/'.join(part for part in path.split('/') if part) + '/'
        if stripped_path == '/':
            self.cwd = stripped_path
        elif path.startswith('/'):
            self.cwd = '/' + stripped_path
        else:
            self.cwd += stripped_path

    def mkdir(self, path, safe=False):
        expected_codes = 201 if not safe else (201, 301, 405)
        self.command('MKCOL', path, expected_codes)

    def mkdirs(self, nc_path):
        dirs = [d for d in nc_path.split('/') if d]
        if not dirs:
            return
        if nc_path.startswith('/'):
            dirs[0] = '/' + dirs[0]
        old_cwd = self.cwd
        try:
            for dir in dirs:
                try:
                    self.mkdir(dir, safe=True)
                except Exception as e:
                    if e == 409:
                        raise

                finally:
                    self.cd(dir)
        finally:
            self.cd(old_cwd)

    def delete(self, path):
        self.command('DELETE', path, (204, 404))

    def upload(self, local_fileobj, remote_fileobj, nc_path="."	):
        if nc_path != ".":
            ispath = self.search_path(nc_path)
            if not ispath:
                self.mkdirs(nc_path)
            self.cd(nc_path)
        if isinstance(local_fileobj, str):
            with open(local_fileobj, 'rb') as fileobj:
                self.command('PUT', remote_fileobj, (200, 201, 204), data=fileobj)
        else:
            self.command('PUT', remote_fileobj, (200, 201, 204), data=local_fileobj)

    def addtag(self, display_name):
        if "/dav/files/" in self.baseurl:
            url = self.baseurl.split("/files/")[0] + "/systemtags"
        else:
            url = self.baseurl.replace("webdav","dav") + "/systemtags"
        x = {"name": display_name, "userVisible": "true", "userAssignable": "true"}
        data = json.dumps(x)
        headers = {"Content-Type": "application/json" }
        response = self.session.post(url, data=data, headers=headers)
        return response.status_code

    def assingtag(self, idfile, idtag):
        if "/dav/files/" in self.baseurl:
            url = self.baseurl.split("/files/")[0] + "/systemtags-relations/files/" + str(idfile) + "/" + str(idtag)
        else:
            url = self.baseurl.replace("webdav","dav") + "/systemtags-relations/files/" + str(idfile) + "/" + str(idtag)
        headers = {"Content-Type": "text/xml" }
        response = self.session.put(url, headers=headers)
        return response.status_code

    def gettag(self, idtag):
        method='PROPFIND'
        if "/dav/files/" in self.baseurl:
            url = self.baseurl.split("/files/")[0] + "/systemtags/" + str(idtag)
        else:
            url = self.baseurl.replace("webdav","dav") + "/systemtags/" + str(idtag)
        headers = {"Content-Type": "text/xml" }
        fullpath = os.path.realpath(__file__).replace("nextcloud_apis.py","tagpropfind.xml")
        fullpath = fullpath.replace('xmlc','xml')
        xmlfile = open(fullpath,"r") 
        data = xmlfile.read()
        xmlfile.close()
        response = self.session.request(method, url, headers=headers, data=data, allow_redirects=False)
        if response.status_code >= 400: return ''
        root = ET.fromstring(response.content)
        # when "userVisible": "true", "userAssignable": "true"
        if root[0][1][0][1].text == 'true' and root[0][1][0][2].text == 'true':
            return root[0][1][0][0].text
        else:
            return ''

    def deletetags(self, idfile, nodelete):
        method='PROPFIND'
        if "/dav/files/" in self.baseurl:
            url = self.baseurl.split("/files/")[0] + "/systemtags-relations/files/" + str(idfile)
        else:
            url = self.baseurl.replace("webdav","dav") + "/systemtags-relations/files/" + str(idfile)
        headers = {"Content-Type": "text/xml" }
        fullpath = os.path.realpath(__file__).replace("nextcloud_apis.py","tagpropfind.xml")
        fullpath = fullpath.replace('xmlc','xml')
        xmlfile = open(fullpath,"r")
        data = xmlfile.read()
        xmlfile.close()
        response = self.session.request(method, url, headers=headers, data=data, allow_redirects=False)
        if response.status_code >= 400: return ''
        root = ET.fromstring(response.content)
        i = 1
        while i < len(root):
            tag = root[i][1][0][0].text
            if not tag in nodelete:
                idtag = root[i][1][0][3].text
                status_code = self.deletetag(idfile, idtag)
                if status_code >= 400: break
            i += 1
        return

    def deletetag(self, idfile, idtag):
        method='DELETE'
        if "/dav/files/" in self.baseurl:
            url = self.baseurl.split("/files/")[0] + "/systemtags-relations/files/" + str(idfile) + "/" + str(idtag)
        else:
            url = self.baseurl.replace("webdav","dav") + "/systemtags-relations/files/" + str(idfile) + "/" + str(idtag)
        headers = {"Content-Type": "text/xml" }
        response = self.session.request(method, url, headers=headers)
        return response.status_code

    def downloadtoserver(self, remote_fileobj, local_fileobj):
        resp = self.command('GET', remote_fileobj, (200), stream=True)
        response = open(local_fileobj, 'wb')
        for chunk in resp.iter_content(100000):
            response.write(chunk)
        response.close()

class OCS():
    def __init__(self, ncurl, user, passwd, js=False):
        self.tojs = "?format=json" if js else ""
        self.ncurl = ncurl
        self.User_url = ncurl + "/ocs/v1.php/cloud/users"
        self.Group_url = ncurl + "/ocs/v1.php/cloud/groups"
        self.Share_url = ncurl + "/ocs/v2.php/apps/files_sharing/api/v1"
        self.h_get = {"OCS-APIRequest": "true"}
        self.h_post = {"OCS-APIRequest":"true","Content-Type":"application/x-www-form-urlencoded"}
        self.auth_pk = (user, passwd)

    def res(self,resp):
        if self.tojs:
            try:
                return resp.json()
            except ValueError:
                return resp.text
        else:
            return resp.text

    def get(self,ur):
        resp = requests.get(ur,auth=self.auth_pk,headers=self.h_get)
        return self.res(resp)

    def post(self,ur,dt=None):
        if dt == None: resp = requests.post(ur,auth=self.auth_pk,headers=self.h_post)
        else: resp = requests.post(ur,auth=self.auth_pk,data=dt,headers=self.h_post)
        return self.res(resp)

    def getUsers(self,search=None,limit=None,offset=None):
        url = self.User_url
        if search != None or limit != None or offset != None:
            url+= "?"
            added = False
            if search != None:
                url+="search="+search
                added = True
            if limit != None:
                if added == False: url += "&"
                url+="limit="+limit
                added = True
            if offset != None:
                if added == False: url += "&"
                url+="offset="+offset
                added = True
        url+= self.tojs
        return self.get(url)

    def getGroup(self,gid):
        return self.get(self.Group_url + "/"+ gid + self.tojs)

    def addGroup(self,gid):
        url = self.Group_url + self.tojs
        msg = {"groupid":gid}
        return self.post(url,msg)

    def createShare(self,path,shareType,shareWith=None,publicUpload=None,password=None,permissions=None):
        url = self.Share_url + "/shares" + self.tojs
        if publicUpload == True: publicUpload = "true"
        if (path == None or isinstance(shareType, int) != True) or (shareType in [0,1] and shareWith == None): return False
        msg = {"path":path,"shareType":shareType}
        if shareType in [0,1]: msg["shareWith"] = shareWith
        if publicUpload == True: msg["publicUpload"] = publicUpload
        if shareType == 3 and password != None: msg["password"] = str(password)
        if permissions != None: msg["permissions"] = permissions
        return self.post(url,msg)
