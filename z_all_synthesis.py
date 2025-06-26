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
from trytond.model import Workflow, ModelView, ModelSQL, fields, \
    sequence_ordered, Unique, DeactivableMixin, dualmethod, DictSchemaMixin
from datetime import date
import requests
from trytond.transaction import Transaction
from sql import Select, Join, Literal, Table
from sql.aggregate import Sum

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

        invoice = Pool().get('account.invoice').__table__()

        i1 = invoice.alias('i1')
        i2 = invoice.alias('i2')

        # Jointures croisant facture et avoir
        join_ref = Join(i1, i2, 'LEFT')
        join_ref.condition = i1.number == i2.reference

        join_rev = Join(join_ref, invoice.alias('i3'), 'LEFT')
        join_rev.condition = join_ref.left.reference == join_rev.right.number

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

        return join_rev.select(
            join_ref.left.sale_price_list.name.as_('assurance_name'),
            Sum(join_ref.left.montant_assurance).as_('total_vente'),
            where=where,
            group_by=[join_ref.left.sale_price_list.name]
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
    


