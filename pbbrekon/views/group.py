from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import (
    DBSession,
    Group,
    GroupPermission,
    )
from ..tools import dict_to_str


SESS_ADD_FAILED = 'group add failed'
SESS_EDIT_FAILED = 'group edit failed'

########                    
# List #
########    
@view_config(route_name='group', renderer='templates/group/list.pt',
             permission='edit_group')
def view_list(request):
    rows = DBSession.query(Group).order_by('group_name')
    return dict(rows=rows)
    

#######    
# Add #
#######
def form_validator(form, value):
    def err_name():
        raise colander.Invalid(form,
            'Group {name} already used by Group ID {id}'.format(
                name=value['group_name'], id=found.id))
                
    if 'id' in form.request.matchdict:
        gid = form.request.matchdict['id']
        q = DBSession.query(Group).filter_by(id=gid)
        group = q.first()
    else:
        group = None
    q = DBSession.query(Group).filter(Group.group_name.ilike(
            value['group_name']))
    found = q.first()
    if group:
        if found and found.id != group.id:
            err_name()
    elif found:
        err_name()


PERMS = ['edit_user', 'edit_group']
PERMISSIONS_DESC = 'Available is {perms}.'.format(perms=', '.join(PERMS))

class AddSchema(colander.Schema):
    group_name = colander.SchemaNode(colander.String())
    description = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    widget=widget.TextAreaWidget(rows=5))
    permissions = colander.SchemaNode(colander.String(),
                    description=PERMISSIONS_DESC)                    


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema.request = request
    return Form(schema, buttons=('save', 'cancel'))
       
def save(values, row=None):
    if not row:
        row = Group()
    row.group_name = values['group_name'].title()
    row.description = values['description']
    DBSession.add(row)
    DBSession.flush()
    old_perms = get_group_perm_names(row.id)
    new_perms = []
    for perm_name in values['permissions'].split(','):
        perm_name = perm_name.strip().lower()
        if not perm_name:
            continue
        new_perms.append(perm_name)
        q = DBSession.query(GroupPermission).filter_by(
                group_id=row.id, perm_name=perm_name)
        gp = q.first()
        if not gp:
            gp = GroupPermission(group_id=row.id, perm_name=perm_name)
            DBSession.add(gp)
            DBSession.flush()
    for perm_name in old_perms:
        if perm_name not in new_perms:
            DBSession.query(GroupPermission).filter_by(group_id=row.id,
                perm_name=perm_name).delete()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, row)
    msg = 'Group {name} has been saved.'.format(name=row.group_name)
    request.session.flash(msg)
        
def route_list(request):
    return HTTPFound(location=request.route_url('group'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='group-add', renderer='templates/group/add.pt',
             permission='edit_group')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('group-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(Group).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User group ID {id} not found.'.format(id=request.matchdict['id'])
    request.session.flash(msg, 'error')
    return route_list(request)

def get_group_perm_names(gid):
    r = []
    q = DBSession.query(GroupPermission).filter_by(group_id=gid).\
            order_by('perm_name')
    for row in q:
        r.append(row.perm_name)
    return r
    
@view_config(route_name='group-edit', renderer='templates/group/edit.pt',
             permission='edit_group')
def view_edit(request):
    row = query_id(request).first()
    if not row:
        return id_not_found(request)
    form = get_form(request, EditSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_EDIT_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('group-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values = dict_to_str(values)
    values['permissions'] = ', '.join(get_group_perm_names(row.id))
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='group-delete',
             renderer='templates/group/delete.pt',
             permission='edit_group')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'Group ID {id} {name} has been deleted.'.format(
                    id=row.id, name=row.group_name)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())
