from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
import colander
from deform import (
    Form,
    widget,
    ValidationFailure,
    )
from ...models.pospbb import (
    PosPbbDBSession,
    )
from ...models.pospbb.pembayaran_sppt import (
    PosPembayaranSppt,
    )

from ...models.pbb import (
    PbbDBSession,
    nop, NOP, bayar
    )
from ...models.pbb.pembayaran_sppt import (
    PembayaranSppt,
    )
    
    
from sqlalchemy import func, String
from sqlalchemy.sql.expression import between

from datatables import ColumnDT, DataTables    
from ...tools import dict_to_str
from datetime import datetime

def _DTupper(chain):
    ret = chain.upper()
    if ret:
        return ret
    else:
        return chain


def _DTdate(chain):
    ret = chain.strftime('%d-%m-%Y')
    if ret:
        return ret
    else:
        return chain

import locale        
def _DTnumber(chain):
    ret = locale.format("%d", chain, grouping=True)
    if ret:
        return ret
    else:
        return chain
        
########                    
# List #
########    
@view_config(route_name='pbb-rekon-realisasi-pospbb', renderer='templates/realisasi-pospbb/list.pt')
def view_list(request):
    #rows = DBSession.query(Group).order_by('group_name')
    return dict(module='Rekonsiliasi',
                tanggal="07-09-2015" #datetime.now()..strftime('%d-%m-%Y')
                )

def get_columns():
    columns = []
    columns.append(ColumnDT('id',mData='id'))
    columns.append(ColumnDT('nop',mData='nop'))
    columns.append(ColumnDT('thn_pajak_sppt',mData='thn_pajak_sppt'))
    columns.append(ColumnDT('pembayaran_sppt_ke',mData='pembayaran_sppt_ke'))
    columns.append(ColumnDT('denda_sppt',mData='denda_sppt', filter=_DTnumber))
    columns.append(ColumnDT('jml_sppt_yg_dibayar',mData='jml_sppt_yg_dibayar', filter=_DTnumber))
    columns.append(ColumnDT('tgl_pembayaran_sppt',mData='tgl_pembayaran_sppt', filter=_DTdate))
    query = PosPbbDBSession.query(func.concat(PosPembayaranSppt.kd_propinsi,
                         PosPembayaranSppt.kd_dati2,PosPembayaranSppt.kd_kecamatan,
                         PosPembayaranSppt.kd_kelurahan,PosPembayaranSppt.kd_blok,
                         PosPembayaranSppt.no_urut, PosPembayaranSppt.kd_jns_op, 
                         PosPembayaranSppt.thn_pajak_sppt, PosPembayaranSppt.pembayaran_sppt_ke).label('id'),
                         func.concat(PosPembayaranSppt.kd_propinsi,
                         PosPembayaranSppt.kd_dati2,PosPembayaranSppt.kd_kecamatan,
                         PosPembayaranSppt.kd_kelurahan,PosPembayaranSppt.kd_blok,
                         PosPembayaranSppt.no_urut, PosPembayaranSppt.kd_jns_op).label('nop'),
                         PosPembayaranSppt.thn_pajak_sppt, PosPembayaranSppt.pembayaran_sppt_ke, 
                         PosPembayaranSppt.denda_sppt, PosPembayaranSppt.jml_sppt_yg_dibayar,
                         PosPembayaranSppt.tgl_pembayaran_sppt)    
    return columns, query
    
@view_config(route_name='pbb-rekon-realisasi-pospbb-act', renderer='json')
def view_grid(request):
    req = request
    ses = req.session
    params = req.params
    url_dict = req.matchdict 
    # if not 'logged' in ses or   not ses['logged'] or ses['userid']!='sa':
        # url = self.request.resource_url(self.context, '')
        # self.d['msg'] = ""
        # return self.d

    if url_dict['act'] == 'grid':
        date_from = 'date_from' in req.params and req.params['date_from']\
                                    or "07-09-2015" #datetime.now().strftime('%d-%m-%Y')
        date_to   = 'date_to' in req.params and req.params['date_to'] or date_from
        ddate_from = datetime.strptime(date_from,'%d-%m-%Y')
        ddate_to   = datetime.strptime(date_to,'%d-%m-%Y')
        columns, query = get_columns()
        qry = query.filter(PosPembayaranSppt.tgl_pembayaran_sppt.between(ddate_from,ddate_to))
        rowTable = DataTables(req.GET, PosPembayaranSppt, qry, columns)
        return rowTable.output_result()

    elif url_dict['act'] == 'rekon':
        date_from = 'date_from' in req.params and req.params['date_from'] or datetime.now().strftime('%d-%m-%Y')
        date_to   = 'date_to' in req.params and req.params['date_to'] or date_from
        ddate_from = datetime.strptime(date_from,'%d-%m-%Y')
        ddate_to   = datetime.strptime(date_to,'%d-%m-%Y')
        
        query = PosPbbDBSession.query(PosPembayaranSppt).\
                    filter(PosPembayaranSppt.tgl_pembayaran_sppt.between(ddate_from,ddate_to))
        rows = query.all()
        rowNotFound = []
        for row in rows:
            queryPbb = PbbDBSession.query(PembayaranSppt).\
                                      filter_by(kd_propinsi  = row.kd_propinsi,
                                                kd_dati2     = row.kd_dati2,
                                                kd_kecamatan = row.kd_kecamatan,
                                                kd_kelurahan = row.kd_kelurahan,
                                                kd_blok      = row.kd_blok,
                                                no_urut      = row.no_urut, 
                                                kd_jns_op    = row.kd_jns_op, 
                                                thn_pajak_sppt = row.thn_pajak_sppt,
                                                pembayaran_sppt_ke = row.pembayaran_sppt_ke)
            rowPbb = queryPbb.first()
            if not rowPbb:
                rowNotFound.append("".join([row.kd_propinsi,
                                         row.kd_dati2,
                                         row.kd_kecamatan,
                                         row.kd_kelurahan,
                                         row.kd_blok,
                                         row.no_urut, 
                                         row.kd_jns_op,
                                         row.thn_pajak_sppt,
                                         str(row.pembayaran_sppt_ke)]))
        print "**DEBUG** ", rowNotFound
        columns,query = get_columns()
        qry = query.filter(func.concat(PosPembayaranSppt.kd_propinsi,
                                PosPembayaranSppt.kd_dati2,PosPembayaranSppt.kd_kecamatan,
                                PosPembayaranSppt.kd_kelurahan,PosPembayaranSppt.kd_blok,
                                PosPembayaranSppt.no_urut, PosPembayaranSppt.kd_jns_op, 
                                PosPembayaranSppt.thn_pajak_sppt, PosPembayaranSppt.pembayaran_sppt_ke.cast(String)).in_(rowNotFound))
                    
        rowTable = DataTables(req.GET, PosPembayaranSppt, qry, columns)
        return rowTable.output_result()
    elif url_dict['act'] == 'update':
        
        bayar.set_raw(req.params['id'])
        
        query = PosPbbDBSession.query(PosPembayaranSppt).\
                    filter_by(kd_propinsi     = bayar['kd_propinsi'],
                              kd_dati2        = bayar['kd_dati2'],
                              kd_kecamatan    = bayar['kd_kecamatan'],
                              kd_kelurahan    = bayar['kd_kelurahan'],
                              kd_blok         = bayar['kd_blok'],
                              no_urut         = bayar['no_urut'], 
                              kd_jns_op       = bayar['kd_jns_op'], 
                              thn_pajak_sppt  = bayar['thn_pajak_sppt'],
                              pembayaran_sppt_ke = bayar['pembayaran_sppt_ke'])
        row = query.first()
        if row:
          rowPbb = PembayaranSppt()
          rowPbb.kd_propinsi  = unicode(row.kd_propinsi)
          rowPbb.kd_dati2     = unicode(row.kd_dati2)
          rowPbb.kd_kecamatan = unicode(row.kd_kecamatan)
          rowPbb.kd_kelurahan = unicode(row.kd_kelurahan)
          rowPbb.kd_blok      = unicode(row.kd_blok)
          rowPbb.no_urut      = unicode(row.no_urut) 
          rowPbb.kd_jns_op    = unicode(row.kd_jns_op)
          rowPbb.thn_pajak_sppt = unicode(row.thn_pajak_sppt)
          rowPbb.pembayaran_sppt_ke = row.pembayaran_sppt_ke
          rowPbb.kd_kantor = unicode(row.kd_kantor)
          rowPbb.kd_kanwil = unicode(row.kd_kanwil)
          rowPbb.kd_tp = unicode(row.kd_tp)
          rowPbb.denda_sppt = row.denda_sppt
          rowPbb.jml_sppt_yg_dibayar = row.jml_sppt_yg_dibayar
          rowPbb.tgl_pembayaran_sppt = row.tgl_pembayaran_sppt
          rowPbb.nip_rekam_byr_sppt = unicode(row.nip_rekam_byr_sppt)
          try:
              PbbDBSession.add(rowPbb)
              PbbDBSession.flush()
          except:
              return dict(status=0,message='Gagal %s' %bayar.get_raw())
        return dict(status=1,message='Sukses')                