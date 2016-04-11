from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    )
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy import engine_from_config
#import transaction
from ...os_tools import FixLength
PbbDBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
PbbBase = declarative_base()
pbb_schema = "BANJAR"

NOP = [
    ['kd_propinsi', 2, 'N'],
    ['kd_dati2', 2, 'N'],
    ['kd_kecamatan', 3, 'N'],
    ['kd_kelurahan', 3, 'N'],
    ['kd_blok', 3, 'N'],
    ['no_urut', 4, 'N'],
    ['kd_jns_op', 1, 'N'],
    ]

BAYAR=NOP
BAYAR.append(['thn_pajak_sppt',4,'N'])
BAYAR.append(['pembayaran_sppt_ke',1,'N'])
    
nop = FixLength(NOP)
bayar = FixLength(BAYAR)
#init_model()
