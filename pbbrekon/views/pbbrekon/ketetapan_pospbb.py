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
from ...models.pospbb.sppt import (
    PosSppt,
    )

from ...models.pbb import (
    PbbDBSession,
    nop, NOP, bayar
    )
from ...models.pbb.sppt import (
    Sppt,
    )
    
    
from sqlalchemy import func, String, tuple_
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
@view_config(route_name='pbb-rekon-ketetapan-pospbb', renderer='templates/ketetapan-pospbb/list.pt')
def view_list(request):
    #rows = DBSession.query(Group).order_by('group_name')
    return dict(module='Rekonsiliasi',
                #tanggal="07-09-2015" 
                tanggal=datetime.now().strftime('%d-%m-%Y')
                )

def get_columns():
    columns = []
    columns.append(ColumnDT('id',                       mData='id'))
    columns.append(ColumnDT('nop',                      mData='nop'))
    columns.append(ColumnDT('thn_pajak_sppt',           mData='thn_pajak_sppt'))
    columns.append(ColumnDT('pbb_yg_harus_dibayar_sppt',mData='pbb_yg_harus_dibayar_sppt', filter=_DTnumber))
    columns.append(ColumnDT('tgl_cetak_sppt',           mData='tgl_cetak_sppt',            filter=_DTdate))
    columns.append(ColumnDT('status_pembayaran_sppt',   mData='status_pembayaran_sppt'))
    
    query = PosPbbDBSession.query(func.concat(PosSppt.kd_propinsi,
                                              PosSppt.kd_dati2,
                                              PosSppt.kd_kecamatan,
                                              PosSppt.kd_kelurahan,
                                              PosSppt.kd_blok,
                                              PosSppt.no_urut, 
                                              PosSppt.kd_jns_op, 
                                              PosSppt.thn_pajak_sppt).label('id'),
                                  func.concat(PosSppt.kd_propinsi,
                                              PosSppt.kd_dati2,
                                              PosSppt.kd_kecamatan,
                                              PosSppt.kd_kelurahan,
                                              PosSppt.kd_blok,
                                              PosSppt.no_urut, 
                                              PosSppt.kd_jns_op).label('nop'),
                                  PosSppt.thn_pajak_sppt, 
                                  PosSppt.pbb_yg_harus_dibayar_sppt,
                                  PosSppt.tgl_cetak_sppt,
                                  PosSppt.status_pembayaran_sppt)    
    return columns, query

########                    
# ACT #
########      
@view_config(route_name='pbb-rekon-ketetapan-pospbb-act', renderer='json')
def view_grid(request):
    req = request
    ses = req.session
    params   = req.params
    url_dict = req.matchdict 
    # if not 'logged' in ses or   not ses['logged'] or ses['userid']!='sa':
        # url = self.request.resource_url(self.context, '')
        # self.d['msg'] = ""
        # return self.d
    date_from = 'date_from' in req.params and req.params['date_from']\
                                or datetime.now().strftime('%d-%m-%Y') #"07-09-2015"
    date_to   = 'date_to' in req.params and req.params['date_to'] or date_from
    ddate_from = datetime.strptime(date_from,'%d-%m-%Y')
    ddate_to   = datetime.strptime(date_to,'%d-%m-%Y')

    if url_dict['act'] == 'grid':
        columns, query = get_columns()
        
        qry = query.filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rowTable = DataTables(req.GET, PosSppt, qry, columns)
        return rowTable.output_result()

    elif url_dict['act'] == 'rekon':
        query = PosPbbDBSession.query(PosSppt.kd_propinsi,
                                      PosSppt.kd_dati2,
                                      PosSppt.kd_kecamatan,
                                      PosSppt.kd_kelurahan,
                                      PosSppt.kd_blok,
                                      PosSppt.no_urut, 
                                      PosSppt.kd_jns_op, 
                                      PosSppt.thn_pajak_sppt).\
                    filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rows = query.all()
    
        queryPbb = PbbDBSession.query(Sppt.kd_propinsi,
                                      Sppt.kd_dati2,
                                      Sppt.kd_kecamatan,
                                      Sppt.kd_kelurahan,
                                      Sppt.kd_blok,
                                      Sppt.no_urut, 
                                      Sppt.kd_jns_op, 
                                      Sppt.thn_pajak_sppt).\
                    filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rowPbbs = queryPbb.all()
        rowNotFound = []
        if len(rows) != len(rowPbbs):
            rowNotFound = list(set(rows) - set(rowPbbs))
        #print "**DEBUG**", len(rows), len(rowPbbs)
        
        columns,query = get_columns()
        qry = query.filter(tuple_(PosSppt.kd_propinsi,
                                  PosSppt.kd_dati2,
                                  PosSppt.kd_kecamatan,
                                  PosSppt.kd_kelurahan,
                                  PosSppt.kd_blok,
                                  PosSppt.no_urut, 
                                  PosSppt.kd_jns_op, 
                                  PosSppt.thn_pajak_sppt).in_(rowNotFound))
                    
        rowTable = DataTables(req.GET, PosSppt, qry, columns)
        return rowTable.output_result()
        
    elif url_dict['act'] == 'update':
        bayar.set_raw(req.params['id'])
        query = PosPbbDBSession.query(PosSppt).\
                    filter_by(kd_propinsi    = bayar['kd_propinsi'],
                              kd_dati2       = bayar['kd_dati2'],
                              kd_kecamatan   = bayar['kd_kecamatan'],
                              kd_kelurahan   = bayar['kd_kelurahan'],
                              kd_blok        = bayar['kd_blok'],
                              no_urut        = bayar['no_urut'], 
                              kd_jns_op      = bayar['kd_jns_op'], 
                              thn_pajak_sppt = bayar['thn_pajak_sppt'])
        row = query.first()
        if row:
            rowPbb = Sppt()
            rowPbb.kd_propinsi               = unicode(row.kd_propinsi)
            rowPbb.kd_dati2                  = unicode(row.kd_dati2)
            rowPbb.kd_kecamatan              = unicode(row.kd_kecamatan)
            rowPbb.kd_kelurahan              = unicode(row.kd_kelurahan)
            rowPbb.kd_blok                   = unicode(row.kd_blok)
            rowPbb.no_urut                   = unicode(row.no_urut) 
            rowPbb.kd_jns_op                 = unicode(row.kd_jns_op)
            rowPbb.thn_pajak_sppt            = unicode(row.thn_pajak_sppt)
            rowPbb.kd_kantor                 = unicode(row.kd_kantor)
            rowPbb.kd_kanwil                 = unicode(row.kd_kanwil)
            rowPbb.kd_tp                     = unicode(row.kd_tp)
            rowPbb.pbb_yg_harus_dibayar_sppt = row.pbb_yg_harus_dibayar_sppt
            rowPbb.status_pembayaran_sppt    = unicode(row.status_pembayaran_sppt)
            rowPbb.tgl_cetak_sppt            = row.tgl_cetak_sppt
            rowPbb.nip_pencetak_sppt         = unicode(row.nip_pencetak_sppt)
            try:
                PbbDBSession.add(rowPbb)
                PbbDBSession.flush()
            except:
                return dict(status=0,message='Gagal %s' %bayar.get_raw())
        return dict(status=1,message='Sukses')                

########                    
# CSV #
########          
@view_config(route_name='pbb-rekon-ketetapan-pospbb-csv', renderer='csv')
def view_csv(request):
    req = request
    ses = req.session
    params = req.params
    url_dict = req.matchdict 
    # if not 'logged' in ses or   not ses['logged'] or ses['userid']!='sa':
        # url = self.request.resource_url(self.context, '')
        # self.d['msg'] = ""
        # return self.d
        
    date_from = 'date_from' in req.params and req.params['date_from']\
                                or datetime.now().strftime('%d-%m-%Y') #"07-09-2015"
    date_to   = 'date_to' in req.params and req.params['date_to'] or date_from
    ddate_from = datetime.strptime(date_from,'%d-%m-%Y')
    ddate_to   = datetime.strptime(date_to,'%d-%m-%Y')
    
    if url_dict['csv'] == 'rekon':
        query = PosPbbDBSession.query(PosSppt.kd_propinsi,
                                      PosSppt.kd_dati2,
                                      PosSppt.kd_kecamatan,
                                      PosSppt.kd_kelurahan,
                                      PosSppt.kd_blok,
                                      PosSppt.no_urut, 
                                      PosSppt.kd_jns_op, 
                                      PosSppt.thn_pajak_sppt).\
                    filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rows = query.all()

        queryPbb = PbbDBSession.query(Sppt.kd_propinsi,
                                      Sppt.kd_dati2,
                                      Sppt.kd_kecamatan,
                                      Sppt.kd_kelurahan,
                                      Sppt.kd_blok,
                                      Sppt.no_urut, 
                                      Sppt.kd_jns_op, 
                                      Sppt.thn_pajak_sppt).\
                    filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
                    
        rowPbbs = queryPbb.all()
        rowNotFound = []
        if len(rows) != len(rowPbbs):
            rowNotFound = list(set(rows) - set(rowPbbs))
        
        columns,query = get_columns()
        qry = query.filter(tuple_(PosSppt.kd_propinsi,
                                  PosSppt.kd_dati2,
                                  PosSppt.kd_kecamatan,
                                  PosSppt.kd_kelurahan,
                                  PosSppt.kd_blok,
                                  PosSppt.no_urut, 
                                  PosSppt.kd_jns_op, 
                                  PosSppt.thn_pajak_sppt).in_(rowNotFound))
        
        r = qry.first()
        header = r.keys()
        query = qry.all()
        rows = []
        for item in query:
            rows.append(list(item))


        # override attributes of response
        filename = 'rekon%s%s.csv' %(date_from, date_to)
        self.request.response.content_disposition = 'attachment;filename=' + filename

        return {
          'header': header,
          'rows'  : rows,
        }        
        
    elif url_dict['csv'] == 'transaksi':
        columns, query = get_columns()
        
        qry = query.filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        r = qry.first()
        
        header = r.keys()
        query = qry.all()
        rows = []
        for item in query:
            rows.append(list(item))

        # override attributes of response
        filename = 'transaksi%s%s.csv' %(date_from, date_to)
        req.response.content_disposition = 'attachment;filename=' + filename

        return {
          'header': header,
          'rows'  : rows,
        }        
        