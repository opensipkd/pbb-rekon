from datetime import datetime
from pyramid.view import view_config
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )
from pyramid.security import (
    remember,
    forget,
    authenticated_userid,
    )
import transaction
import colander
from deform import (
    Form,
    ValidationFailure,
    widget,
    )
########                    
# List #
########    
@view_config(route_name='pbb-rekon', renderer='templates/home.pt',
             permission='edit_group')
def view_list(request):
    return dict(project='pbb-rekon')    
