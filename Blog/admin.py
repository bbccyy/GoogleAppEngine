
"""
Google App Engine Script that handles administration screens for the
blog.
"""

import os
import cgi
import math
import random
import datetime
import logging

from google.appengine.api import users

from models import *
from blog import FrontPageHandler
from blog import SingleArticleHandler

import webapp2
import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

class AdminHomePageHandler(FrontPageHandler):
    """
    Handles the main admin page, which lists all articles in the blog,
    with links to their corresponding edit pages. Also allows search
    by tags and/or search by year month
    """
    def get(self):

        self.preprocess(Article, 'get_all')

        template_values = {
            'articles':self.articles,
            'page':self.page,
            'num_of_pages': self.num_of_pages,
            'PageCount':self.PageCount,
            'user':self.user,
            'admin':self.admin,
            'tag':self.tag,
            'tags':self.tags,
            'tagstr':self.tagstr,
            'year':self.year,
            'month':self.month,
            'group_by_month':self.group_by_month,
            'month_count':self.month_count,
            'user_url':self.user_url,
            'user_url_linktext':self.user_url_linktext
        }
        template = JINJA_ENVIRONMENT.get_template('AdminHome.html')
        self.response.write(template.render(template_values))

class NewArticleHandler(webapp2.RequestHandler):
    """
    Handles requests to create a new article, then redirect page to
    /admin/EditArticle?aid=urlsafe
    """
    def get(self):
        article = Article(title='place your new article\'s title here',
                          content='Content goes here',
                          draft=True)
        article_key = article.put()
        self.redirect('/admin/EditArticle?aid=' + article_key.urlsafe())


class EditArticleHandler(FrontPageHandler):
    """
    Handles from show to modify to submit an article in textarea.
    """
    def get(self):

        self.preprocess(Article, handleSinglePage = True)

        if self.user and self.admin:
            article = ndb.Key(urlsafe=self.request.get('aid')).get()
            template_values = {
                'article':article,
                'articles':self.articles,
                'page':self.page,
                'num_of_pages': self.num_of_pages,
                'user':self.user,
                'admin':self.admin,
                'tag':self.tag,
                'tags':self.tags,
                'tagstr':self.tagstr,
                'year':self.year,
                'month':self.month,
                'group_by_month':self.group_by_month,
                'month_count':self.month_count,
                'user_url':self.user_url,
                'user_url_linktext':self.user_url_linktext
            }
            template = JINJA_ENVIRONMENT.get_template('EditArticle.html')
            self.response.write(template.render(template_values))
        else:
            self.redirect('/')


    def post(self):
        title = self.request.get('title')
        content = self.request.get('content')
        article_urlsafe = cgi.escape(self.request.get('aid'))
        tags = cgi.escape(self.request.get('tags'))
        decision = self.request.get('decision')

        if decision == 'P':
            draft = False
        else:
            draft = True

        if tags:
            tags = [t.strip() for t in tags.split(',')]
        else:
            tags = []

        article = ndb.Key(urlsafe=article_urlsafe).get()

        is_published = article.draft and draft
        article.title = title
        article.content = content
        article.tags = tags
        article.draft = is_published
        # -------- for test only start ---------
        #test_date = datetime.datetime(2016,2,1)
        #article.published_date = test_date
        # -------- for test only end ---------
        article.put()

        self.redirect('/admin/Article?aid=' + article_urlsafe)


class AdminArticleHandler(SingleArticleHandler):
    """
    Handles to display a single article page in full size
    """
    def get(self):
        self.preprocessArticle('AdminArticlePage.html')



class DeleteArticleHandler(webapp2.RequestHandler):
    """
    Handles form submissions to delete an article.
    """
    def get(self):
        user = users.get_current_user()
        admin = users.is_current_user_admin()

        if not user or not admin:
            self.redirect('/')
        else:
            article = ndb.Key(urlsafe = self.request.get('aid')).get()
            if article:
                article.key.delete()
                self.redirect('/admin/PageDeleted')


class PageDeletedHandler(webapp2.RequestHandler):
    """
    Handles the page displayed after deleting the article
    """
    def get(self):
        user = users.get_current_user()

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        template_values = {
            'user':user,
            'user_url':user_url,
            'user_url_linktext':user_url_linktext
        }
        template = JINJA_ENVIRONMENT.get_template('DeletePage.html')
        self.response.write(template.render(template_values))

# -----------------------------------------------------------------------------
# Main program
# -----------------------------------------------------------------------------

app = webapp2.WSGIApplication([
    ('/admin', AdminHomePageHandler),
    ('/admin/AddArticle', NewArticleHandler),
    ('/admin/EditArticle', EditArticleHandler),
    ('/admin/Article', AdminArticleHandler),
    ('/admin/DeleteArticle', DeleteArticleHandler),
    ('/admin/PageDeleted',PageDeletedHandler)
    ],debug=True)
