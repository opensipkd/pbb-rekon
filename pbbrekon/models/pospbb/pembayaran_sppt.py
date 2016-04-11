from ..pospbb import PosPbbBase, pospbb_schema

class PosPembayaranSppt(PosPbbBase):
    __tablename__  = 'pembayaran_sppt'
    __table_args__ = {'extend_existing':True, 'schema' : pospbb_schema, 
                      'autoload':True}

