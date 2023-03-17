=========================
Customizing Look and Feel
=========================

Flask is a great framework for creating small applications, but it is also
rather bad in allowing customizations to be outside of the application tree.

Technically speaking there are few things that allow customization.

Templates
=========

In order to customize template or replace it completely it is required to put
file with the name of the template that needs to be overriden in the
`app/templates` folder. Flask adds this folder into the search path and the first
one will be chosen. Please refer to
`Flask docs <https://flask.palletsprojects.com/en/2.2.x/blueprints/#templates>`_ for details.

Static content
==============

This is a bit more complex and Flask does not have possibility to define
alternative places to search for the static content. The only possibility to
override content of the `app/static` files is only to place new content inside.
When running status dashboard in the container it is required either to mount
some external volume under the `/app/app/static` or to overwrite individual
files there. In case of mounting a volume it must contain all files as in the
original `app/static` folder.

Customizations with Docker
==========================

It is possible to build new docker container image from the status-dashboard
overwriting required content. This helps to keep customizations under version
control and have a clear code separation (see `Example
<https://github.com/stackmon/otc-status-dashboard>`_).
