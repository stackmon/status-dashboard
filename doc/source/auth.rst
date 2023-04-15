=============
Authorization
=============

Status Dashbord responsibility is to visualize state of the monitored system.
However there is always a need for an administrative interface for scheduling
maintenance windows, opening or closing incidents. Currently there are 2
supported methods: GitHub and OpenIDConnect. Both methods delegate
authentication to the identity provider and do not store and user information
locally.

Providers
=========


GitHub
------

In order to use GitHub as an identity provider it is required to create a new
`GitHub Oauth application
<https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/creating-an-oauth-app>`_.
`client_id` and `client_secret` must be provided to the `StatusDashboard` as
`SDB_GITHUB_CLIENT_ID` and `SDB_GITHUB_CLIENT_SECRET` environment
variables. In the GitHub application settings `Authorization callback URL`
should be set to <http://domain:port/auth/github>, where `domain:port` point to
the application.

OpenIDConnect
-------------

Another way to provide authenticated user infrormation to the application is to
rely on the widely adopted OpenIDConnect. Currently using KeyCloak server is
the only tested method, but most other implementations should work as well.  In
order to configure OpenIDConnect for the `StatusDashboard` it is required to do
the following configuration on the identity provider side:

- Create a new client with `OpenID Connect` type

  - Client authentication is enabled

  - `Valid redirect URIs` set to <http://domain:port/auth/openid>

  - `Client Scope` `status-dashboard-aud` with `OpenID Connect` protocol
    created and a mapper with a type `Group Membership` and name `groups`
    created and assigned to the client

On the `StatusDashboard` side `SDB_OPENID_CLIENT_ID`,
`SDB_OPENID_CLIENT_SECRET`, `SDB_OPENID_ISSUER_URL` environment
variables should be set to their corresponding values. ISSUER_URL normally
should be pointing to the tenan on the identity server and
`{ISSUER_URL}/.well-known/openid-configuration` should be resolvable.

When `SDB_OPENID_REQUIRED_GROUP` variable is set user will be authorized only
when member of the specified group (for Keycloak i.e. `/status-dashboard`)

Authorization Routes
====================

`StatusDashboard` implements following routes for the authorization:

.. autoflask:: status_dashboard:app
   :endpoints: web.login, web.auth_callback, web.logout
