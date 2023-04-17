=========
RSS feed
=========

Status Dashboard application comes with a RSS feeds to provide the information about the incidents

Description
===========

Current RSS Feeds based on the "feedgen" library

https://pypi.org/project/feedgen/


Examples of requests for RSS feed
=================================

If you run the application on your local environment
the example of URL will be like this:

http://127.0.0.1:5000/rss/?mt=Region2&srv=Component32

Feed supports attributes such as the following:
"mt"
"srv"
where "mt" is the name of the region (attribute)
and "srv" is the name of the component

You can make a request without the "srv" attribute:

http://127.0.0.1:5000/rss/?mt=Region2

In that case you will get the incidentsfor the all components in region