from models import (
    User,
    UserGroup,
    )
    
# It is used by RootFactory
def group_finder(login, request):
    u = User.get_by_identity(login)
    if not u or not u.status:
        return # None means logout
    r = []        
    for group_id in UserGroup.get_by_user(u):
        acl_name = 'group:{gid}'.format(gid=group_id)
        r.append(acl_name)
    return r
        
def get_user(request):
    user_id = request.authenticated_userid
    if user_id:
        return User.get_by_identity(user_id)
