from email.utils import parseaddr
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import webhelpers.paginate
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ..models import (
    DBSession,
    User,
    UserGroup,
    Group,
    )


SESS_ADD_FAILED = 'user add failed'
SESS_EDIT_FAILED = 'user edit failed'

########                    
# List #
########    
@view_config(route_name='user', renderer='templates/user/list.pt',
             permission='edit_user')
def view_list(request):
    rows = DBSession.query(User).filter(User.id > 0)
    count = rows.count()
    rows = rows.order_by('email')
    page_url = webhelpers.paginate.PageURL_WebOb(request)
    rows = webhelpers.paginate.Page(rows,
                page=int(request.params.get('page', 1)),
                item_count=count,
                items_per_page=10,
                url=page_url)
    return dict(rows=rows, count=count)
    

#######    
# Add #
#######
def email_validator(node, value):
    name, email = parseaddr(value)
    if not email or email.find('@') < 0:
        raise colander.Invalid(node, 'Invalid email format')

def group_validator(node, value):
    for name in value.split(','):
        name = name.strip()
        if not name:
            continue
        q = DBSession.query(Group).filter(Group.group_name.ilike(name))
        found = q.first()
        if not found:
            msg = 'Invalid group {name}, available is {available}'.format(
                    name=name,
                    available=', '.join(get_group_names()))
            raise colander.Invalid(node, msg)

def form_validator(form, value):
    def err_email():
        raise colander.Invalid(form,
            'Email {email} already used by user ID {user_id}'.format(
                email=value['email'], user_id=found.id))

    def err_name():
        raise colander.Invalid(form,
            'User name {user_name} already used by ID {user_id}'.format(
                user_name=value['user_name'], user_id=found.id))
                
    if 'id' in form.request.matchdict:
        uid = form.request.matchdict['id']
        q = DBSession.query(User).filter_by(id=uid)
        user = q.first()
    else:
        user = None
    q = DBSession.query(User).filter_by(email=value['email'])
    found = q.first()
    if user:
        if found and found.id != user.id:
            err_email()
    elif found:
        err_email()
    if 'user_name' in value: # optional
        found = User.get_by_name(value['user_name'])
        if user:
            if found and found.id != user.id:
                err_name()
        elif found:
            err_name()

@colander.deferred
def deferred_status(node, kw):
    values = kw.get('status_list', [])
    return widget.SelectWidget(values=values)
    
STATUS = (
    (1, 'Active'),
    (0, 'Inactive'),
    )    


class AddSchema(colander.Schema):
    email = colander.SchemaNode(colander.String(),
                                validator=email_validator)
    user_name = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop)
    status = colander.SchemaNode(
                    colander.String(),
                    widget=deferred_status)
    password = colander.SchemaNode(
                    colander.String(),
                    widget=widget.PasswordWidget(),
                    missing=colander.drop)
    group = colander.SchemaNode(colander.String(),
                validator=group_validator,
                description='More than one separated by commas.')


class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
                    

def get_form(request, class_form):
    schema = class_form(validator=form_validator)
    schema = schema.bind(status_list=STATUS)
    schema.request = request
    return Form(schema, buttons=('save','cancel'))
    
def save(values, user, row=None):
    if not row:
        row = User()
    row.from_dict(values)
    if values['password']:
        row.password = values['password']
    DBSession.add(row)
    DBSession.flush()
    old_groups = get_user_group_ids(row)
    new_groups = []
    for group_name in values['group'].split(','):
        group_name = group_name.strip()
        if not group_name:
            continue
        q = DBSession.query(Group).filter(Group.group_name.ilike(group_name))
        g = q.first()
        new_groups.append(g.id)
        q = DBSession.query(UserGroup).filter_by(user_id=row.id, group_id=g.id)
        ug = q.first()
        if not ug:
            ug = UserGroup(user_id=row.id, group_id=g.id)
            DBSession.add(ug)
            DBSession.flush()
    for group_id in old_groups:
        if group_id not in new_groups:
            DBSession.query(UserGroup).filter_by(user_id=row.id,
                group_id=group_id).delete()
    return row
    
def save_request(values, request, row=None):
    if 'id' in request.matchdict:
        values['id'] = request.matchdict['id']
    row = save(values, request.user, row)
    request.session.flash('User {email} has been saved.'.format(
        email=row.email))
        
def route_list(request):
    return HTTPFound(location=request.route_url('user'))
    
def session_failed(request, session_name):
    r = dict(form=request.session[session_name])
    del request.session[session_name]
    return r
    
@view_config(route_name='user-add', renderer='templates/user/add.pt',
             permission='edit_user')
def view_add(request):
    form = get_form(request, AddSchema)
    if request.POST:
        if 'save' in request.POST:
            controls = request.POST.items()
            try:
                c = form.validate(controls)
            except ValidationFailure, e:
                request.session[SESS_ADD_FAILED] = e.render()               
                return HTTPFound(location=request.route_url('user-add'))
            save_request(dict(controls), request)
        return route_list(request)
    elif SESS_ADD_FAILED in request.session:
        return session_failed(request, SESS_ADD_FAILED)
    return dict(form=form.render())

########
# Edit #
########
def query_id(request):
    return DBSession.query(User).filter_by(id=request.matchdict['id'])
    
def id_not_found(request):    
    msg = 'User ID %s not found.' % request.matchdict['id']
    request.session.flash(msg, 'error')
    return route_list(request)

def get_user_group_names(user):
    r = []
    for group_id in UserGroup.get_by_user(user):
        q = DBSession.query(Group).filter_by(id=group_id)
        g = q.first()
        r.append(g.group_name)
    return r
    
def get_user_group_ids(user):
    r = []
    for group_id in UserGroup.get_by_user(user):
        r.append(group_id)
    return r    
    
def get_group_names():
    r = []
    for g in DBSession.query(Group).order_by('group_name'):
        r.append(g.group_name)
    return r

@view_config(route_name='user-edit', renderer='templates/user/edit.pt',
             permission='edit_user')
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
                return HTTPFound(location=request.route_url('user-edit',
                                  id=row.id))
            save_request(dict(controls), request, row)
        return route_list(request)
    elif SESS_EDIT_FAILED in request.session:
        return session_failed(request, SESS_EDIT_FAILED)
    values = row.to_dict()
    values['group'] = ', '.join(get_user_group_names(row))
    return dict(form=form.render(appstruct=values))

##########
# Delete #
##########    
@view_config(route_name='user-delete', renderer='templates/user/delete.pt',
             permission='edit_user')
def view_delete(request):
    q = query_id(request)
    row = q.first()
    if not row:
        return id_not_found(request)
    form = Form(colander.Schema(), buttons=('delete','cancel'))
    if request.POST:
        if 'delete' in request.POST:
            msg = 'User ID {user_id} {email} has been deleted.'.format(
                user_id=row.id, email=row.email)
            q.delete()
            DBSession.flush()
            request.session.flash(msg)
        return route_list(request)
    return dict(row=row,
                 form=form.render())

