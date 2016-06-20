#!/usr/bin/env python
import os
import urllib
import logging
import datetime
import math
import cgi
from urlparse import urlparse
import re

from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import webapp2
import jinja2

MAX_PAGE_LIST = 2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))

class UserInfo(ndb.Model):
    author = ndb.UserProperty()
    friends = ndb.UserProperty(repeated=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)

class Question(ndb.Model):
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    title = ndb.StringProperty(indexed=False)
    content = ndb.TextProperty(indexed=False)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    modified_date = ndb.DateTimeProperty()
    tags = ndb.StringProperty(repeated=True)

class Answer(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.TextProperty(indexed=False)
    vote = ndb.IntegerProperty(indexed=False)
    voters = ndb.StringProperty(repeated=True)
    created_date = ndb.DateTimeProperty(auto_now_add=True)
    modified_date = ndb.DateTimeProperty()

class UserPhoto(ndb.Model):
    author = ndb.UserProperty()
    blob_key = ndb.BlobKeyProperty()
    url = ndb.StringProperty(indexed=False)
    note = ndb.StringProperty(indexed=False)
    created_date = ndb.DateTimeProperty(auto_now_add=True)

def url_repl(m):
    ext = m.group(1)
    if ext in ['.png', '.jpg', '.gif']:
        return "<img src='%s'>" % m.group(0)
    else:
        return "<a href='%s'>%s</a>" % (m.group(0), m.group(0))

def parse_content(content):

    return re.sub(r'[a-zA-Z0-9]+://(?:[a-zA-Z0-9_]+:[a-zA-Z0-9_]+@)?(?:[a-zA-Z0-9.-]+\.[A-Za-z]{2,4})(?::[0-9]+)?(?:/[^ \.]*)?(\.[^\s]*)?', url_repl, content)


class HomePageHandler(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        userinfo = None
        if user:
            userinfos = UserInfo.query(ancestor=ndb.Key('UserInfo', user.user_id()))
            #userinfo = userinfos.fetch(99999)  #this returns a list, we can use len() to it
            #for ui in userinfos:
            #    userinfo = ui
            if userinfos.count() == 0:
                userinfo = UserInfo(author=user, parent=ndb.Key('UserInfo', user.user_id()))
            else:
                userinfo = userinfos.get()

            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        template_values = {
            'userinfo':userinfo,
            'user':user,
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('homePage.html')
        self.response.write(template.render(template_values))

class QuestionHomeHandler(webapp2.RequestHandler):

    def get_page_list(self, page=0, num_of_pages=1):
        PageCount = {}
        pl = []
        for i in range(page, page+MAX_PAGE_LIST):
            if i < num_of_pages:
                pl.append(i)
            else:
                break
        PageCount['pagelist'] = pl

        PageCount['pre'] = page-1  # Yes >=0  or No == -1

        if page + MAX_PAGE_LIST < num_of_pages:
            PageCount['post'] = page + MAX_PAGE_LIST
        else:
            PageCount['post'] = -1

        if page > 0:
            PageCount['start'] = 0
        else:
            PageCount['start'] = -1

        if page < num_of_pages - 1:
            PageCount['end'] = num_of_pages - 1
        else:
            PageCount['end'] = -1

        return PageCount

    def preprocess(self, cls, f = ''):
        user = users.get_current_user()
        max_page_size = 5

        tag = self.request.get('tag').split(' ')
        page = self.request.get('page')

        if not page:
            page = 0
        else:
            page = int(page)

        func = getattr(cls, f)  # use this to replace cls.query, introduce more flexibility

        if tag[0] != '':
            question_query = func().filter(cls.tags.IN(tag)).order(-cls.created_date)
        else:
            question_query = func().order(-cls.created_date)
            #ancestor=ndb.Key("Questions", "0")

        num_of_page = int(math.ceil(question_query.count() / float(max_page_size)))

        questions = question_query.fetch(max_page_size, offset=page * max_page_size)

        tagstr = " ".join(tag)

        PageCount = self.get_page_list(page, num_of_page)

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        self.user = user
        self.max_page_size = max_page_size
        self.page = page
        self.tag = tag
        self.tagstr = tagstr
        self.questions = questions
        self.num_of_page = num_of_page
        self.PageCount = PageCount
        self.user_url = user_url
        self.user_url_linktext = user_url_linktext

    def get(self):

        self.preprocess(Question, 'query')

        template_values = {
            'parse_content':parse_content,
            'num_of_page': self.num_of_page,
            'PageCount':self.PageCount,
            'tag' : self.tag,
            'tagstr' : self.tagstr,
            'page': self.page,
            'user': self.user,
            #'userinfo':userinfo,
            'questions': self.questions,
            'user_url':self.user_url,
            'user_url_linktext':self.user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('Question_Home.html')
        self.response.write(template.render(template_values))

class QuestionPageHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        question_key = ndb.Key(urlsafe=self.request.get('qid'))
        question = question_key.get()

        answers = Answer.query(ancestor=question_key).order(-Answer.created_date)

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        template_values = {
            'parse_content':parse_content,
            'user': user,
            'question': question,
            'answers': answers,
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('Question.html')
        self.response.write(template.render(template_values))

class AddQuestion(webapp2.RequestHandler):
    def post(self):

        user = users.get_current_user()

        if user:
            question = Question(author=user, parent=ndb.Key("Questions", "0"))
            question.title = self.request.get('title')
            question.content = self.request.get('content')
            q_tags = self.request.get('tags').split(r',')
            question.tags = q_tags

            question.put()

        else:
            self.redirect(users.create_login_url())

        self.redirect('/Question?qid='+question.key.urlsafe())

class EditQuestion(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
            question = ndb.Key(urlsafe=self.request.get('qid')).get()
            decision = self.request.get('decision')
            if decision == 'Yes':
                question.key.delete()
                self.redirect('/DeleteSuccess')
                return

            template_values = {
                'parse_content':parse_content,
                'question': question,
                'user_url':user_url,
                'user_url_linktext':user_url_linktext
            }

            template = JINJA_ENVIRONMENT.get_template('EditQuestion.html')
            self.response.write(template.render(template_values))

        else:
            self.redirect(users.create_login_url())

    def post(self):
        user = users.get_current_user()

        question = ndb.Key(urlsafe=self.request.get('qid')).get()

        if user:

            question.title = self.request.get('title')
            question.content = self.request.get('content')
            question.modified_date = datetime.datetime.now()

            q_tags = self.request.get('tags').split(r',')
            question.tags = q_tags

            question.put()

            self.redirect('/Question?qid='+question.key.urlsafe())

        else:
            self.redirect(users.create_login_url())

class EditAnswerHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
            answer = ndb.Key(urlsafe=self.request.get('aid')).get()  #not get Key, get the entity itself!
            question = ndb.Key(urlsafe=self.request.get('qid')).get()
            decision = self.request.get('decision')
            if decision == 'Yes':
                answer.key.delete()
                self.redirect('/Question?qid='+question.key.urlsafe())
                return

            template_values = {
                'question':question,
                'answer': answer,
                'user_url':user_url,
                'user_url_linktext':user_url_linktext
            }

            template = JINJA_ENVIRONMENT.get_template('EditAnswer.html')
            self.response.write(template.render(template_values))

        else:
            self.redirect(users.create_login_url())

    def post(self):
        user = users.get_current_user()

        answer = ndb.Key(urlsafe=self.request.get('aid')).get()
        question = ndb.Key(urlsafe=self.request.get('qid')).get()

        if user:

            answer.content = self.request.get('content')
            answer.modified_date = datetime.datetime.now()

            answer.put()

            self.redirect('/Question?qid='+ question.key.urlsafe())

        else:
            self.redirect(users.create_login_url())


class AnswerHandler(webapp2.RequestHandler):
    def post(self):
        question_key = ndb.Key(urlsafe= self.request.get('qid'))
        user = users.get_current_user()

        if user:
            answer = Answer(author=user, parent=question_key)
            answer.content = self.request.get('content')
            answer.vote = 0
            answer.voters = []
            answer.put()
            self.redirect("/Question?qid="+self.request.get('qid'))
        else:
            self.redirect(users.create_login_url)

class UpVoteHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        answer = ndb.Key(urlsafe = self.request.get('aid')).get()
        id = user.user_id() + ''

        if user and  id not in answer.voters:
            answer.vote += 1
            answer.voters.append(id)
            answer.put()

        self.redirect("/Question?qid="+self.request.get('qid'))

class DownVoteHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        answer = ndb.Key(urlsafe = self.request.get('aid')).get()
        id = user.user_id() + ''

        if user and  id not in answer.voters:
            answer.vote -= 1
            answer.voters.append(id)
            answer.put()

        self.redirect("/Question?qid="+self.request.get('qid'))

class AlbumPageHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        upload_url = None
        userinfo = None
        photos = None
        if user:
            upload_url = blobstore.create_upload_url('/Upload')
            userinfos = UserInfo.query(ancestor=ndb.Key('UserInfo', user.user_id()))  #retrive all entities (in this case, only one returned)
            for ui in userinfos:
                userinfo = ui
            upload_url = upload_url + '?uid=' + user.user_id()
            photos = UserPhoto.query(ancestor=ndb.Key('UserPhoto', user.user_id())).order(-UserPhoto.created_date)
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
            template_values = {
                'user': user,
                'userinfo':userinfo,
                'photos': photos,
                'upload_url':upload_url,
                'user_url':user_url,
                'user_url_linktext':user_url_linktext
            }

            template = JINJA_ENVIRONMENT.get_template('Album.html')
            self.response.write(template.render(template_values))

        else:
            self.redirect(users.create_login_url())


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads()[0]
        blob_key = upload_files.key()

        url = images.get_serving_url(blob_key)

        user = users.get_current_user()
        user_id =self.request.get('uid')


        if user and user_id == user.user_id():
            #userinfos = UserInfo.query(ancestor=ndb.Key('UserInfo', user.user_id()))  #retrive all entities (in this case, only one returned)
            #for ui in userinfos:
                #userinfo = ui
            photo = UserPhoto(author=user,blob_key=blob_key, url=url, parent=ndb.Key('UserPhoto', user.user_id()))
            photo.put()
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'


        template_values = {
            'user': user,
            'url': url,
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('Upload.html')
        self.response.write(template.render(template_values))


class DeletePhotoHandler(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()

        #current_url = urlparse(self.request.url)
        #querys = cgi.parse_qs(current_url.query)
        #pid_num = querys.get('pid')

        photo = ndb.Key(urlsafe = self.request.get('pid')).get()


        if not user:
            self.redirect(users.create_login_url())
        elif user != photo.author:
            self.redirect('/Album')
        else:
            blob_key = photo.blob_key
            images.delete_serving_url(blob_key)
            blob_info = blobstore.BlobInfo.get(blob_key)
            blob_info.delete()
            photo.key.delete()

        self.redirect('/Album')

class AboutPageHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        template_values = {
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('About.html')
        self.response.write(template.render(template_values))

class DeleteSuccessHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        template_values = {
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template('DeleteSuccess.html')
        self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
    ('/', HomePageHandler),
    ('/Question_Home', QuestionHomeHandler),
    ('/ask', AddQuestion),
    ('/Question', QuestionPageHandler),
    ('/EditQuestion', EditQuestion),
    ('/Answer', AnswerHandler),
    ('/upVote', UpVoteHandler),
    ('/downVote', DownVoteHandler),
    ('/EditAnswer', EditAnswerHandler),
    ('/Album', AlbumPageHandler),
    ('/Upload', UploadHandler),
    ('/DeletePhoto', DeletePhotoHandler),
    ('/About', AboutPageHandler),
    ('/DeleteSuccess', DeleteSuccessHandler)
], debug=True)
