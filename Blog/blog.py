#!/usr/bin/env python
"""
Google App Engine Script that handles display of the published
items in the blog.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import os
import sys
import math
import random
import logging
import datetime

# Google AppEngine imports
from google.appengine.api import users
from google.appengine.ext import ndb

from models import *

import webapp2
import jinja2

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------

MAX_ARTICLES_PER_PAGE = 5
MAX_PAGE_LIST = 2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))


class FrontPageHandler(webapp2.RequestHandler):
    """
    Handles requests to display the home page of the blog.
    """
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


    def preprocess(self, cls, funcName = 'get_all', handleSinglePage = False):
        user = users.get_current_user()
        admin = users.is_current_user_admin()  # boolean value

        if handleSinglePage:
            max_page_size = 1
            tag = []
            tagstr = ""
            year = 0
            month = 0
            page = 0
            num_of_pages = 1
            articles = []
            PageCount = None
        else:
            max_page_size = 5
            tag = self.request.get('tag').split(' ')
            year = self.request.get('year')
            month = self.request.get('month')
            tagstr = ""

            func = getattr(cls, funcName)  # returns the handler of cls.funcName

            if tag[0]!='':
                articles_query = cls.search_for_tag(tag)
                tagstr = " ".join(tag)
            elif year and month:
                articles_query = cls.search_for_month(int(year), int(month))
            else:
                articles_query = func()

            page = self.request.get('page')
            if page:
                page = int(page)
            else:
                page = 0

            num_of_pages =  int(math.ceil(articles_query.count() / float(MAX_ARTICLES_PER_PAGE)))
            articles = articles_query.fetch(MAX_ARTICLES_PER_PAGE, offset=MAX_ARTICLES_PER_PAGE * page)   # a list of articles

            PageCount = self.get_page_list(page, num_of_pages)

        tags = cls.get_tag_counts()

        group_by_month = {}

        month_count = cls.get_month_counts()

        for dct in month_count:
            # all_in_month is a query object
            all_in_month = cls.search_for_month(dct.date.year, dct.date.month)
            group_by_month[dct] = all_in_month

        if user:
            user_url = users.create_logout_url(self.request.uri)
            user_url_linktext = 'Logout'
        else:
            user_url = users.create_login_url(self.request.uri)
            user_url_linktext = 'Login'

        self.user = user
        self.admin = admin
        self.max_page_size = max_page_size
        self.page = page
        self.tag = tag
        self.tags = tags
        self.tagstr = tagstr
        self.year = year
        self.month = month
        self.group_by_month = group_by_month
        self.month_count = month_count
        self.articles = articles
        self.num_of_pages = num_of_pages
        self.PageCount = PageCount
        self.user_url = user_url
        self.user_url_linktext = user_url_linktext


    def get(self):

        self.preprocess(Article, 'published')

        template_values = {
            'articles':self.articles,    # this is a list of articles, not query entity
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
        template = JINJA_ENVIRONMENT.get_template('BlogHome.html')
        self.response.write(template.render(template_values))


class SingleArticleHandler(FrontPageHandler):
    """
    Handles requests to display a single article, given its unique ID.
    Handles nonexistent IDs.
    """
    def preprocessArticle(self, htmlPage='ArticlePage.html'):

        self.preprocess(Article, handleSinglePage = True)

        article = ndb.Key(urlsafe=self.request.get('aid')).get()  # it's an article entity

        template_values = {
            'article':article,
            'articles':self.articles,
            'page':self.page,
            'num_of_pages': self.num_of_pages,
            'user':self.user,
            'admin':self.admin,
            'tag':self.tag,
            'tags':self.tags,
            'year':self.year,
            'month':self.month,
            'group_by_month':self.group_by_month,
            'month_count':self.month_count,
            'user_url':self.user_url,
            'user_url_linktext':self.user_url_linktext
        }

        template = JINJA_ENVIRONMENT.get_template(htmlPage)
        self.response.write(template.render(template_values))

    def get(self):
        self.preprocessArticle('ArticlePage.html')


# -----------------------------------------------------------------------------
# Main program
# -----------------------------------------------------------------------------

app = webapp2.WSGIApplication([
    ('/', FrontPageHandler),
    ('/Article', SingleArticleHandler)
    ],debug=True)
