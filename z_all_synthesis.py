from decimal import Decimal
from collections import defaultdict, namedtuple
from itertools import combinations
from datetime import datetime, date

from sql import Null
from sql.aggregate import Sum
from sql.conditionals import Coalesce, Case
from sql.functions import Round
import time
from datetime import datetime
from trytond.pool import Pool
import requests
from trytond.i18n import gettext
# from trytond.backend.postgresql.table import Table
from trytond.model import Workflow, ModelView, ModelSQL, fields, \
    sequence_ordered, Unique, DeactivableMixin, dualmethod, DictSchemaMixin
from datetime import date
import requests
from trytond.transaction import Transaction
from sql import Select, Join, Literal
from sql import Table
from sql.aggregate import Sum
from sql import alias

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.modules.account.tax import TaxableMixin
from trytond.modules.product import price_digits
from trytond.modules.health.core import get_health_professional

class Classement_Assurance_vente(ModelSQL, ModelView):
    "Classement des ventes Totale par Assurance"
    __name__ = "ventes.assurances"

    assurance_name = fields.Char("Assurance")
    total_vente = fields.Float("Total des ventes.")


    @classmethod
    def table_query(cls):

        SalePriceList = Pool().get('product.price_list')
        spl1 = SalePriceList.__table__()

        Party = Pool().get('party.party')
        party_all1 = Party.__table__()

        PartySalePriceList = Pool().get('party.party.sale_price_list')
        partySPL1 = PartySalePriceList.__table__()

        Invoice = Pool().get('account.invoice')
        invoice = Invoice.__table__()

        print(type(invoice))
        i1 = Invoice.__table__()
        i2 = Invoice.__table__()
        i3 = Invoice.__table__()

        # Jointures croisant facture et avoir
        join_ref = Join(i1, i2, 'LEFT')
        join_ref.condition = i1.number == i2.reference

        join_rev = Join(join_ref, i3, 'LEFT')
        join_rev.condition = join_ref.left.reference == join_rev.right.number

        # JOINTURE ENTRE PARTY_PARTY_SALE_PRICE_LIST ET PRODUCT_PRICE_LIST
        join_ppspl = Join(partySPL1, spl1, 'LEFT')
        join_ppspl.condition = partySPL1.sale_price_list == spl1.id

        # Jointure Party et join_ppspl
        join_part = Join(party_all1, join_ppspl, 'LEFT')
        join_part.condition = party_all1.id == partySPL1.id

        # Jointure entre join_part et invoice maintenant
        join_v = Join(join_rev, join_part, 'LEFT')
        join_v.condition = join_ref.left.party == join_part.left.id
        
        # Clause de base
        where = Literal(True)
        ctx = Transaction().context

        if ctx.get('start_date'):
            where &= i1.invoice_date >= ctx['start_date']
        if ctx.get('end_date'):
            where &= i1.invoice_date <= ctx['end_date']
        where &= i1.state.in_(['paid', 'posted'])

        # Élimination des factures avec relation crédit/avoir
        where &= (i2.id == None)  # i1.number ≠ i2.reference
        where &= (join_rev.right.id == None)  # i1.reference ≠ i3.number

        print(join_ref.left.sale_price_list.name)
        return join_v.select(
            spl1.name,
            Sum(join_ref.left.montant_assurance),
            where=where,
            group_by=[spl1.name]
        )



class Ventes_Assurances_Par_Mois(ModelSQL, ModelView):
    "Classement des ventes d'une seule assurance par mois"
    __name__ = "ventes.assurance.mois"

    assurance_name = fields.Char("Assurance")
    annee = fields.Integer('Année', required=True)

    janvier = fields.Float('Janvier')
    fevrier = fields.Float('Février')
    mars = fields.Float('Mars')
    avril = fields.Float('Avril')
    mai = fields.Float('Mai')
    juin = fields.Float('Juin')
    juillet = fields.Float('Juillet')
    aout = fields.Float('Août')
    septembre = fields.Float('Septembre')
    octobre = fields.Float('Octobre')
    novembre = fields.Float('Novembre')
    decembre = fields.Float('Décembre')

    total_annuel = fields.Function(fields.Float('Total Annuel'), 'get_total')

    def get_total(self, names):
        result = {}
        for record in self:
            total = (
                (record.janvier or 0) + (record.fevrier or 0) + (record.mars or 0) +
                (record.avril or 0) + (record.mai or 0) + (record.juin or 0) +
                (record.juillet or 0) + (record.aout or 0) + (record.septembre or 0) +
                (record.octobre or 0) + (record.novembre or 0) + (record.decembre or 0)
            )
            result[record.id] = total
        return result
    


