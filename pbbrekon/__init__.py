import locale
import os
from types import (
    StringType,
    UnicodeType,
    )
from urllib import (
    urlencode,
    quote,
    quote_plus,
    )    
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound,
    )
from sqlalchemy import engine_from_config
from security import (
    group_finder,
    get_user,
    )
from models import (
    DBSession,
    Base,
    init_model,
    )
from tools import (
    DefaultTimeZone,
    money,
    should_int,
    thousand,
    as_timezone,
    split,
    )

# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true    
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path.endswith('/'):
            noslash_path = path.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        return self.notfound_view(context, request)
    
# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def has_permission_(request, perm_names):
    if type(perm_names) in [UnicodeType, StringType]:
        perm_names = [perm_names]
    for perm_name in perm_names:
        if request.has_permission(perm_name):
            return True

@subscriber(BeforeRender)
def add_global(event):
     event['has_permission'] = has_permission_
     event['urlencode'] = urlencode
     event['quote_plus'] = quote_plus
     event['quote'] = quote   
     event['money'] = money
     event['should_int'] = should_int  
     event['thousand'] = thousand
     event['as_timezone'] = as_timezone
     event['split'] = split

def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]

routes = [    
    ('home', '/', 'Home'),
    ('login', '/login', 'Login'),
    ('logout', '/logout', None),
    ('password', '/password', 'Change password'),
    ('user', '/user', 'Users'),
    ('user-add', '/user/add', 'Add user'),
    ('user-edit', '/user/{id}/edit', 'Edit user'),
    ('user-delete', '/user/{id}/delete', 'Delete user'),
    ('group', '/group', 'User group'),
    ('group-add', '/group/add', 'Add user group'),
    ('group-edit', '/group/{id}/edit', 'Edit user group'),
    ('group-delete', '/group/{id}/delete', 'Delete user group'),  
    
    ('pbb-rekon', '/pbb/rekon', 'Rekonsiliasi PBB'),  
    ('pbb-rekon-realisasi-pospbb', '/pbb/rekon/realisasi/pospbb', 'Rekonsiliasi Realisasi POSPBB'),  
    ('pbb-rekon-realisasi-pospbb-act', '/pbb/rekon/realisasi/pospbb/{act}/act', 'Action Rekonsiliasi Realisasi POSPBB'),  
    ('pbb-rekon-realisasi-pospbb-csv', '/pbb/rekon/realisasi/pospbb/{csv}/csv', 'CSV Rekonsiliasi Realisasi POSPBB'),  
    ('pbb-rekon-realisasi-sismiop', '/pbb/rekon/realisasi/sismiop', 'Rekonsiliasi Realisasi SISMIOP'),  
    ('pbb-rekon-realisasi-sismiop-act', '/pbb/rekon/realisasi/sismiop/{act}/act', 'Action Rekonsiliasi Realisasi SISMIOP'),  
    ('pbb-rekon-realisasi-sismiop-csv', '/pbb/rekon/realisasi/sismiop/{csv}/csv', 'CSV Rekonsiliasi Realisasi SISMIOP'),  

    ('pbb-rekon-ketetapan-pospbb', '/pbb/rekon/ketetapan/pospbb', 'Rekonsiliasi Ketetapan POSPBB'),  
    ('pbb-rekon-ketetapan-pospbb-act', '/pbb/rekon/ketetapan/pospbb/{act}/act', 'Action Rekonsiliasi Ketetapan POSPBB'),  
    ('pbb-rekon-ketetapan-pospbb-csv', '/pbb/rekon/ketetapan/pospbb/{csv}/csv', 'CSV Rekonsiliasi Ketetapan POSPBB'),  
    ('pbb-rekon-ketetapan-sismiop', '/pbb/rekon/ketetapan/sismiop', 'Rekonsiliasi Ketetapan SISMIOP'),  
    ('pbb-rekon-ketetapan-sismiop-act', '/pbb/rekon/ketetapan/sismiop/{act}/act', 'Action Rekonsiliasi Ketetapan SISMIOP'),  
    ('pbb-rekon-ketetapan-sismiop-csv', '/pbb/rekon/ketetapan/sismiop/{csv}/csv', 'CSV Rekonsiliasi Ketetapan SISMIOP'),  
    
    ]

main_title = 'pbb-rekon'
titles = {}
for name, path, title in routes:
    if title:
        titles[name] = ' - '.join([main_title, title])
    
pbb_schema    = ""
pospbb_schema = ""

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    ###Engine Tambahan
    if settings['pbb.url']:
        from models.pbb import (
            PbbDBSession,
            PbbBase
        )
        os.environ["NLS_LANG"] = ".AL32UTF8"
        pbb_engine = engine_from_config(settings, 'pbb.') #, encoding='.AL32UTF8', convert_unicode=True)
        PbbDBSession.configure(bind=pbb_engine)
        PbbBase.metadata.bind = pbb_engine
        pbb_schema = settings['pbb_schema']

    if settings['pospbb.url']:
        from models.pospbb import (
            PosPbbDBSession,
            PosPbbBase,
        )
        pospbb_engine = engine_from_config(settings, 'pospbb.')
        PosPbbDBSession.configure(bind=pospbb_engine)
        PosPbbBase.metadata.bind = pospbb_engine
        pospbb_schema = settings['pospbb_schema']

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'
    locale.setlocale(locale.LC_ALL, settings['localization'])        
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone
    config = Configurator(settings=settings,
                          root_factory='pbbrekon.models.RootFactory',
                          session_factory=session_factory)
    config.include('pyramid_beaker')                          
    config.include('pyramid_chameleon')

    authn_policy = AuthTktAuthenticationPolicy('sosecret',
                    callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()                          
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_notfound_view(RemoveSlashNotFoundViewFactory())        
                          
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    config.add_static_view('files', settings['static_files'])    

    config.add_renderer('csv', '.tools.CSVRenderer')
    
    for name, path, title in routes:
        config.add_route(name, path)
    config.scan()
    app = config.make_wsgi_app()
    from paste.translogger import TransLogger
    app = TransLogger(app, setup_console_handler=False)    
    return app
