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
@view_config(route_name='pbb-rekon-ketetapan-sismiop', renderer='templates/ketetapan-sismiop/list.pt')
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
    
    query = PbbDBSession.query(func.concat(Sppt.kd_propinsi,
                                  func.concat(Sppt.kd_dati2,
                                  func.concat(Sppt.kd_kecamatan,
                                  func.concat(Sppt.kd_kelurahan,
                                  func.concat(Sppt.kd_blok,
                                  func.concat(Sppt.no_urut, 
                                  func.concat(Sppt.kd_jns_op, Sppt.thn_pajak_sppt))))))).label('id'),
                                  func.concat(Sppt.kd_propinsi,
                                  func.concat(Sppt.kd_dati2,
                                  func.concat(Sppt.kd_kecamatan,
                                  func.concat(Sppt.kd_kelurahan,
                                  func.concat(Sppt.kd_blok,
                                  func.concat(Sppt.no_urut, Sppt.kd_jns_op)))))).label('nop'),
                                  Sppt.thn_pajak_sppt, 
                                  Sppt.pbb_yg_harus_dibayar_sppt,
                                  Sppt.tgl_cetak_sppt,
                                  Sppt.status_pembayaran_sppt)    
    return columns, query

########                    
# ACT #
########      
@view_config(route_name='pbb-rekon-ketetapan-sismiop-act', renderer='json')
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
        
        qry = query.filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rowTable = DataTables(req.GET, Sppt, qry, columns)
        return rowTable.output_result()

    elif url_dict['act'] == 'rekon':
        query = PbbDBSession.query(Sppt.kd_propinsi,
                                   Sppt.kd_dati2,
                                   Sppt.kd_kecamatan,
                                   Sppt.kd_kelurahan,
                                   Sppt.kd_blok,
                                   Sppt.no_urut, 
                                   Sppt.kd_jns_op, 
                                   Sppt.thn_pajak_sppt).\
                    filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rows = query.all()
    
        queryPbb = PosPbbDBSession.query(PosSppt.kd_propinsi,
                                         PosSppt.kd_dati2,
                                         PosSppt.kd_kecamatan,
                                         PosSppt.kd_kelurahan,
                                         PosSppt.kd_blok,
                                         PosSppt.no_urut, 
                                         PosSppt.kd_jns_op, 
                                         PosSppt.thn_pajak_sppt).\
                    filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rowPbbs = queryPbb.all()
        rowNotFound = []
        if len(rows) != len(rowPbbs):
            rowNotFound = list(set(rows) - set(rowPbbs))
        #print "**DEBUG**", len(rows), len(rowPbbs)
        
        columns,query = get_columns()
        qry = query.filter(tuple_(Sppt.kd_propinsi,
                                  Sppt.kd_dati2,
                                  Sppt.kd_kecamatan,
                                  Sppt.kd_kelurahan,
                                  Sppt.kd_blok,
                                  Sppt.no_urut, 
                                  Sppt.kd_jns_op, 
                                  Sppt.thn_pajak_sppt).in_(rowNotFound))
                    
        rowTable = DataTables(req.GET, Sppt, qry, columns)
        return rowTable.output_result()
        
    elif url_dict['act'] == 'update':
        bayar.set_raw(req.params['id'])
        query = PbbDBSession.query(Sppt).\
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
            rowPbb = PosSppt()
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
            rowPbb.siklus_sppt               = row.siklus_sppt          
            rowPbb.nm_wp_sppt                = unicode(row and row.nm_wp_sppt or '')
            rowPbb.jln_wp_sppt               = unicode(row and row.jln_wp_sppt or '')
            rowPbb.blok_kav_no_wp_sppt       = unicode(row and row.blok_kav_no_wp_sppt or '')
            rowPbb.rw_wp_sppt                = unicode(row and row.rw_wp_sppt or '')
            rowPbb.rt_wp_sppt                = unicode(row and row.rt_wp_sppt or '')
            rowPbb.kelurahan_wp_sppt         = unicode(row and row.kelurahan_wp_sppt or '')
            rowPbb.kota_wp_sppt              = unicode(row and row.kota_wp_sppt or '')
            rowPbb.kd_pos_wp_sppt            = unicode(row and row.kd_pos_wp_sppt or '')
            rowPbb.npwp_sppt                 = unicode(row and row.npwp_sppt or '')
            rowPbb.no_persil_sppt            = unicode(row and row.no_persil_sppt or '')
            rowPbb.kd_kls_tanah              = unicode(row.kd_kls_tanah)
            rowPbb.thn_awal_kls_tanah        = unicode(row.thn_awal_kls_tanah)
            rowPbb.kd_kls_bng                = unicode(row.kd_kls_bng)
            rowPbb.thn_awal_kls_bng          = unicode(row.thn_awal_kls_bng)
            rowPbb.tgl_jatuh_tempo_sppt      = row.tgl_jatuh_tempo_sppt 
            rowPbb.luas_bumi_sppt            = row.luas_bumi_sppt       
            rowPbb.luas_bng_sppt             = row.luas_bng_sppt        
            rowPbb.njop_bumi_sppt            = row.njop_bumi_sppt       
            rowPbb.njop_bng_sppt             = row.njop_bng_sppt        
            rowPbb.njop_sppt                 = row.njop_sppt            
            rowPbb.njoptkp_sppt              = row.njoptkp_sppt         
            rowPbb.pbb_terhutang_sppt        = row.pbb_terhutang_sppt   
            rowPbb.faktor_pengurang_sppt     = row.faktor_pengurang_sppt
            rowPbb.status_tagihan_sppt       = unicode(row.status_tagihan_sppt)
            rowPbb.status_cetak_sppt         = unicode(row.status_cetak_sppt)
            rowPbb.tgl_terbit_sppt           = row.tgl_terbit_sppt      
            
            try:
                PosPbbDBSession.add(rowPbb)
                PosPbbDBSession.flush()
            except:
                return dict(status=0,message='Gagal %s' %bayar.get_raw())
        return dict(status=1,message='Sukses')                

########                    
# CSV #
########          
@view_config(route_name='pbb-rekon-ketetapan-sismiop-csv', renderer='csv')
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
        query = PbbDBSession.query(Sppt.kd_propinsi,
                                   Sppt.kd_dati2,
                                   Sppt.kd_kecamatan,
                                   Sppt.kd_kelurahan,
                                   Sppt.kd_blok,
                                   Sppt.no_urut, 
                                   Sppt.kd_jns_op, 
                                   Sppt.thn_pajak_sppt).\
                    filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
        rows = query.all()

        queryPbb = PosPbbDBSession.query(PosSppt.kd_propinsi,
                                         PosSppt.kd_dati2,
                                         PosSppt.kd_kecamatan,
                                         PosSppt.kd_kelurahan,
                                         PosSppt.kd_blok,
                                         PosSppt.no_urut, 
                                         PosSppt.kd_jns_op, 
                                         PosSppt.thn_pajak_sppt).\
                    filter(PosSppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
                    
        rowPbbs = queryPbb.all()
        rowNotFound = []
        if len(rows) != len(rowPbbs):
            rowNotFound = list(set(rows) - set(rowPbbs))
        
        columns,query = get_columns()
        qry = query.filter(tuple_(Sppt.kd_propinsi,
                                  Sppt.kd_dati2,
                                  Sppt.kd_kecamatan,
                                  Sppt.kd_kelurahan,
                                  Sppt.kd_blok,
                                  Sppt.no_urut, 
                                  Sppt.kd_jns_op, 
                                  Sppt.thn_pajak_sppt).in_(rowNotFound))
        
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
        
        qry = query.filter(Sppt.tgl_cetak_sppt.between(ddate_from,ddate_to))
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
        