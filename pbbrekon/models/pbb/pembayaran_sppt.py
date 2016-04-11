from ..pbb import PbbBase, pbb_schema
from sqlalchemy import(
    Column,
    String,
    Integer,
    BigInteger,
    Date
)
class PembayaranSppt(PbbBase):
    __tablename__  = 'pembayaran_sppt'
    __table_args__ = {'extend_existing':True, 'schema' : pbb_schema, 
                      'autoload':True
                      }
    # kd_propinsi   = Column(String(2), primary_key=True)
    # kd_dati2      = Column(String(2), primary_key=True)
    # kd_kecamatan  = Column(String(3), primary_key=True)
    # kd_kelurahan  = Column(String(3), primary_key=True)
    # kd_blok       = Column(String(3), primary_key=True)
    # no_urut       = Column(String(4), primary_key=True)
    # kd_jns_op     = Column(String(1), primary_key=True)
    # thn_pajak_sppt= Column(String(4), primary_key=True)
    # pembayaran_sppt_ke = Column(Integer, primary_key=True)
    # kd_kantor   = Column(String(2), primary_key=True)
    # kd_kanwil   = Column(String(2), primary_key=True)
    # kd_tp       = Column(String(2), primary_key=True)
    # denda_sppt  = Column(BigInteger)
    # jml_sppt_yg_dibayar = Column(BigInteger)
    # tgl_pembayaran_sppt = Column(Date)
    # nip_rekam_byr_sppt  = Column(String(18))
    # tgl_rekam_byr_sppt  = Column(Date)
