from ..pospbb import PosPbbBase, pospbb_schema

class PosSppt(PosPbbBase):
    __tablename__  = 'sppt'
    __table_args__ = {'extend_existing':True, 'schema' : pospbb_schema, 
                      'autoload':True}
                      