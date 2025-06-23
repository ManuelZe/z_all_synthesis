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
import json
import requests
from trytond.i18n import gettext
from trytond.model import Workflow, ModelView, ModelSQL, fields, \
    sequence_ordered, Unique, DeactivableMixin, dualmethod, DictSchemaMixin
from trytond.model.exceptions import AccessError
from trytond.pyson import PYSONEncoder
from trytond.report import Report
from trytond.wizard import Wizard, StateView, StateTransition, StateAction, \
    Button
from trytond import backend
from trytond.pyson import If, Eval, Bool
from trytond.tools import reduce_ids, grouped_slice, firstline
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.rpc import RPC
from trytond.config import config
from trytond.modules.product import round_price

import requests
import json

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.modules.account.tax import TaxableMixin
from trytond.modules.product import price_digits
from trytond.modules.health.core import get_health_professional

class Account_Invoice_Summary(ModelSQL, ModelView):
    "Table Principale pour les éléments de la recherche dans les factures."
    __name__ = "account.invoice.summary"

    start_date = fields.DateTime("Date de début", required=True)
    end_date = fields.DateTime("Date de fin", required=True)


class Classement_Assurance_vente(ModelSQL, ModelView):
    "Classement des ventes Totale par Assurance"
    __name__ = "ventes.assurances"

    assurance_name = fields.Char("Assurance")
    total_vente = fields.Float("Total des ventes.")

class Account_Invoice_KPI(ModelSQL, ModelView):
    "Table pour les résultats des racherches de Account Invoice Summary"
    __name__ = "account.invoice.kpis"

    summary_id = fields.Many2One("account.invoice.summary", "Sommaire")
    value_numeric = fields.BigInteger("Valeur Numérique")
    value_text = fields.Text("Valeur Textuelle")
    value_json = fields.Text("Valeur JSON des éléments")