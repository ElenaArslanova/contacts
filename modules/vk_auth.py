import http.cookiejar
import urllib
import urllib.request
from urllib.parse import urlparse, urlencode
from html.parser import HTMLParser


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.url = None
        self.params = {}
        self.in_form = False
        self.form_parsed = False
        self.method = 'GET'

    def handle_starttag(self, tag, attributes):
        tag = tag.lower()
        if tag == 'form':
            if self.form_parsed:
                raise RuntimeError('Second form on page')
            if self.in_form:
                raise RuntimeError('Already in form')
            self.in_form = True
        if not self.in_form:
            return
        attributes = dict((name.lower(), value) for name, value in attributes)
        if tag == 'form':
            self.url = attributes['action']
            if 'method' in attributes:
                self.method = attributes['method'].upper()
        elif tag == 'input' and 'type' in attributes and 'name' in attributes:
            if attributes['type'] in ['hidden', 'text', 'password']:
                self.params[attributes['name']] = (attributes['value']
                                                   if 'value' in attributes
                                                   else '')

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'form':
            if not self.in_form:
                raise RuntimeError('Unexpected end of <form>')
            self.in_form = False
            self.form_parsed = True


def auth(email, password, client_id, scope):
    def split_key_value(kv_pair):
        kv = kv_pair.split('=')
        return kv[0], kv[1]

    def auth_user(email, password, client_id, scope, opener):
        response = opener.open(
            'https://oauth.vk.com/authorize?' +
            'redirect_uri=https://oauth.vk.com/blank.html&response_type=token&'+
            'client_id={}&scope={}&display=page'.format(client_id,
                                                        ','.join(scope))
        )
        doc = response.read().decode('utf-8')
        parser = FormParser()
        parser.feed(doc)
        parser.close()
        if (not parser.form_parsed or parser.url is None or
                'pass' not in parser.params or 'email' not in parser.params):
            raise RuntimeError()
        parser.params['email'] = email
        parser.params['pass'] = password
        if parser.method == 'POST':
            response = opener.open(parser.url,
                                   urlencode(parser.params).encode('utf-8'))
        else:
            raise NotImplementedError('Method {}'.format(parser.method))
        return response.read(), response.geturl()

    def give_access(doc, opener):
        parser = FormParser()
        parser.feed(doc.decode('utf-8'))
        parser.close()
        if not parser.form_parsed or parser.url is None:
            raise RuntimeError()
        if parser.method == 'POST':
            response = opener.open(parser.url,
                                   urlencode(parser.params).encode('utf-8'))
        else:
            raise NotImplementedError('Method {}'.format(parser.method))
        return response.geturl()

    if not isinstance(scope, list):
        scope = [scope]
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPRedirectHandler()
    )
    doc, url = auth_user(email, password, client_id, scope, opener)
    if urlparse(url).path != '/blank.html':
        url = give_access(doc, opener)
    answer = dict(split_key_value(kv_pair) for kv_pair
                  in urlparse(url).fragment.split('&'))
    if 'access_token' not in answer:
        raise RuntimeError('Missing access token in answer')
    return answer['access_token']
