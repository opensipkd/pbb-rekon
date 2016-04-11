from ..pbb import PbbBase, pbb_schema

class Sppt(PbbBase):
    __tablename__  = 'sppt'
    __table_args__ = {'extend_existing':True, 'schema' : pbb_schema, 
                      'autoload':True}
                      