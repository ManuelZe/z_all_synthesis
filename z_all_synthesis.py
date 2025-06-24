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
import json

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
    
class Dashboard_General(ModelSQL, ModelView):
    "Dashboard General Pour l'app"
    __name__="general.dashboard"

    # Date : Éléments général de la recherche 

    date_debut = fields.Date("Date de Début", required=True)
    date_fin = fields.Date("Date de Fin", required=True)

    # Elément 1 : Etat / Classement Ventes Totale par Assurance

    vente_assurance = fields.Boolean("Ventes Par Assurances", help="Cocher si vous voulez faire une actualisation des ventes par assurance")
    assurance_name = fields.Function(fields.Char("Assurance"), "get_classement_assurance_vente")
    total_vente =  fields.Function(fields.Float("Total des ventes."), "get_classement_assurance_vente")



    def default_date_debut():
        return date.today()
    
    def default_date_fin():
        return date.today()
    
    def get_classement_assurance_vente(self):

        if self.vente_assurance == True :

            list_of_save_elements = []
            listes_factures = []

            Ventes_Assurance = Pool().get("ventes.assurances")
            Ventes_ass = Ventes_Assurance.search([])
            Ventes_Assurance.delete(Ventes_ass)

            Invoices = Pool().get("account.invoice")
            Factures = Invoices.search([('invoice_date', '>=', self.date_debut), ('invoice_date', '<=', self.date_fin), ('state', 'in', ['paid', 'posted'])])

            for Facture in Factures:
                if Facture.number not in listes_factures:
                    listes_factures.append(Facture.number)
            
            for Facture in Factures:
                if Facture.reference in listes_factures:
                    listes_factures.remove(Facture.reference)
                    listes_factures.remove(Facture.number)

            dict_assurance = {}
            for facture_number in listes_factures:
                facture = Invoices.search([('number', '=', facture_number)], limit=1)
                if not facture:
                    continue
                assurance = facture[0].party.sale_price_list
                if assurance.name in dict_assurance:
                    dict_assurance[assurance.id]['total_vente'] += facture[0].montant_assurance
                else:
                    dict_assurance[assurance.id] = {
                        'assurance_name': assurance.name,  # nom réel du champ Many2One
                        'total_vente': facture[0].montant_assurance
                    }

            return dict_assurance



