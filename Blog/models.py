import datetime
import math

from google.appengine.ext import ndb

class DateCount(object):
    """
    Convenience class for storing and sorting year/month counts.
    """
    def __init__(self, date, count):
        self.date = date
        self.count = count

    def __cmp__(self, other):
        return cmp(self.date, other.date)

    def __hash__(self):
        return self.date.__hash__()

    def __str__(self):
        return '%s(%d)' % (self.date, self.count)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, str(self))

class TagCount(object):
    """
    Convenience class for storing and sorting tags and counts.
    """
    def __init__(self, tag, count):
        self.css_class = ""
        self.count = count
        self.tag = tag

    def __cmp__(self, other):
        return cmp(self.count, other.count)

class Article(ndb.Model):

    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty()
    published_date = ndb.DateTimeProperty(auto_now_add=True)
    tags = ndb.StringProperty(repeated=True)
    id = ndb.StringProperty()
    draft = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def get_all(cls):
        q = Article.query().order(-Article.published_date)
        return q   # return a Query object, not a list of entities

    @classmethod
    def get(cls, url):
        q = ndb.Key(urlsafe=url)
        # q = cls.query()
        # q = q.filter(cls.id==id)
        return q.get()  # return the fist entity in Query q

    @classmethod
    def published_query(cls):
        q = Article.query()
        q = q.filter(Article.draft==False)
        return q   # Query Object

    @classmethod
    def published(cls):
        return Article.published_query().order(-Article.published_date)

    @classmethod
    def get_all_tags(cls):
        """
        Return all tags, as TagCount objects:
        { 'tagName1': 10, 'tagName12': 20 }
        """
        tag_counts = {}
        for article in Article.published():
            for tag in article.tags:
                tag = unicode(tag)
                try:
                    tag_counts[tag] += 1
                except KeyError:
                    tag_counts[tag] = 1

                """  # equivlant to the following code:
                if tag_counts.has_key(tag):
                    tag_counts[tag] += 1
                else:
                    tag_counts[tag] = 1   """

        return tag_counts

    @classmethod
    def get_all_datetimes(cls):
        dates = {}
        for article in Article.published():
            """class datetime.datetime   https://docs.python.org/2/library/datetime.html
            A combination of a date and a time. Attributes:
            year, month, day, hour, minute, second, microsecond, and tzinfo."""
            date = datetime.datetime(article.published_date.year,
                                     article.published_date.month,
                                     article.published_date.day)
            try:
                dates[date] += 1
            except KeyError:
                dates[date] = 1

        return dates

    @classmethod
    def search_for_month(cls, year, month):
        """
        Get article query object that matches the requirment.
        requirment --> Article.published_date.year == year
        and Article.published_date.month == month

        :rtype: Query object
        :return: list of articles in query
        """
        start_date = datetime.datetime(year, month, 1)
        if start_date.month == 12:
            next_year = start_date.year + 1
            next_month = 1
        else:
            next_year = start_date.year
            next_month = start_date.month + 1

        end_date = datetime.datetime(next_year, next_month, 1)
        return Article.published_query()\
                       .filter(Article.published_date >= start_date)\
                       .filter(Article.published_date < end_date)\
                       .order(-Article.published_date)

    @classmethod
    def search_for_tag(cls, tags):
        """
        Get article query object that matches the requirment.
        requirment --> one or more tag in tags list matches any tag in article.tags

        :rtype: Query object
        :return: list of articles in query
        """
        return Article.published_query()\
                      .filter(Article.tags.IN(tags))\
                      .order(-Article.published_date)


    def __unicode__(self):
        return self.__str__()

    def __str__(self):
        return '[%s] %s' %\
               (self.published_date.strftime('%Y/%m/%d %H:%M'), self.title)

    @classmethod
    def get_tag_counts(self):
        """
        Get tag counts and calculate tag cloud frequencies.

        :rtype: list
        :return: list of ``TagCount`` objects, in reverse order

        TagCount's attributes:
        self.css_class = ""
        self.count = count
        self.tag = tag
        """
        tag_counts = Article.get_all_tags()
        result = []
        if tag_counts:
            maximum = max(tag_counts.values())

            for tag, count in tag_counts.items():
                tc = TagCount(tag, count)

                # Determine the popularity of this term as a percentage.

                percent = math.floor((tc.count * 100) / maximum)

                # determine the CSS class for this term based on the percentage

                if percent <= 20:
                    tc.css_class = 'tiny'
                elif 20 < percent <= 40:
                    tc.css_class = 'small'
                elif 40 < percent <= 60:
                    tc.css_class = 'medium'
                elif 60 < percent <= 80:
                    tc.css_class = 'large'
                else:
                    tc.css_class = 'huge'

                result.append(tc)

        result.sort()
        result.reverse()
        return result

    @classmethod
    def get_month_counts(self):
        """
        Get date counts, sorted in reverse chronological order.

        :rtype: list
        :return: list of ``DateCount`` objects
        """
        # get_all_datetimes() returns a set dates, where
        # dates = { 'date1': count, 'date2': count }
        datetime_set = Article.get_all_datetimes()
        datetimes = datetime_set.keys()
        date_count = {}
        for dt in datetimes:
            just_year_month = datetime.date(dt.year, dt.month, 1)
            try:
                date_count[just_year_month] += datetime_set[dt]
            except KeyError:
                date_count[just_year_month] = datetime_set[dt]

        dates = date_count.keys()
        dates.sort()
        dates.reverse()
        return [DateCount(date, date_count[date]) for date in dates]
