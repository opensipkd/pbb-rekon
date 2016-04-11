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

PosPbbDBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
PosPbbBase = declarative_base()
pospbb_schema = "public"

#import pembayaran_sppt