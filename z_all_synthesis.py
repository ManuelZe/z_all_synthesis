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
from sql import Literal, Cast
from sql.functions import Now

from trytond.model import fields
from trytond.pool import PoolMeta
from trytond.modules.account.tax import TaxableMixin
from trytond.modules.product import price_digits
from trytond.modules.health.core import get_health_professional

class Classement_Assurance_vente(ModelSQL, ModelView):
    "Classement des ventes Totale par Assurance"
    __name__ = "ventes.assurances"

    _rec_name = "Ventes Assurances"
    _history = False

    assurance_name = fields.Char("Assurance")
    total_vente = fields.Float("Total des ventes.")
    nb_facture = fields.Integer("Nombre de Factures")


class Produits_Sur_Periode(ModelSQL, ModelView):
    "Classement des produits vendus sur une période"
    __name__ = "ventes.produits.periode"

    produit_name = fields.Many2One("product.product", "Produit", required=True)
    nbr = fields.Integer("Nombre de ventes", required=True)
    total_vente = fields.Float("Total des ventes", required=True)


class Nombre_Patients_Par_Tarifaire(ModelSQL, ModelView):
    "Nombre de patients par tarifaire"
    __name__ = "patients.tarifaire"

    tarifaire_name = fields.Many2One("product.price_list", "Tarifaire", required=True)
    nbr_patients = fields.Integer("Nombre de patients", required=True)


class Metriques(ModelSQL, ModelView):
    "Les valeurs Uniques Autour des Factures"
    __name__ = "ventes.metriques"

    nbr_factures_assurance = fields.Integer("Nombre de Factures Assurance")
    nbr_factures_normales = fields.Integer("Nombre de Factures Normales")
    nbr_factures_postees = fields.Integer("Nombre de Factures Postées")
    nbr_factures_payees = fields.Integer("Nombre de Factures Payées")
    nbr_factures_creditees = fields.Integer("Nombre de Factures Créditées")


class Validation_Services(ModelSQL, ModelView):
    "Syntheses Des Validations Par Services"
    __name__ = "validations.services"

    service_name = fields.Char("Service", required=True)
    nbr_validate = fields.Integer("Nombre Validé", required=True)
    nbr_no_validate = fields.Integer("Nombre Non Validé", required=True)
    pourcentage = fields.Float("Pourcentage", required=True)


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
    


