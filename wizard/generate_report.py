# -*- coding: utf-8 -*-
##############################################################################
#
#    GNU Health: The Free Health and Hospital Information System
#    Copyright (C) 2008-2022 Luis Falcon <lfalcon@gnusolidario.org>
#    Copyright (C) 2011-2022 GNU Solidario <health@gnusolidario.org>
#
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import re
from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateTransition, StateView, Button, StateAction
from trytond.pool import Pool
from trytond.pyson import Eval, Not, Bool, PYSONEncoder, Equal, And, Or
from datetime import date, datetime, time
from decimal import Decimal


class Elements_Actualisations(ModelView):
    'Les Élements D\'actualisations du rapports'
    __name__ = 'elements.refresh.init'

    date_debut = fields.Date("Date de Début", required=True)
    date_fin = fields.Date("Date de Fin", required=True)


    @staticmethod
    def default_date_debut():
        return datetime.now()
    
    @staticmethod
    def default_date_fin():
        return datetime.now()

    vente_assurance = fields.Boolean("Ventes Par Assurances", help="Cocher si vous voulez faire une actualisation des ventes par assurance")


class GenerateResultsReports(Wizard):
    'Generation des Rapports En Totalité'
    __name__ = 'rapports.refresh.all'

    start = StateView('elements.refresh.init',
        'z_all_synthesis.view_element_actualisation', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Assurance Vente', 'actualisation_element', 'tryton-ok',
                True),
            ])
    
    actualisation_element = StateTransition()
    # open_ = StateAction('z_all_synthesis.act_syntheses_assurances_form2')
    
    # def do_open_(self, action):
    #     if self.start.vente_assurance :
    #         action['pyson_context'] = PYSONEncoder().encode({
    #         'date_start': self.start.date_debut,
    #         'date_end': self.start.date_fin,
    #         'vente_assurance': self.start.vente_assurance,
    #         })

    #         action['name'] = "Ventes Par Assurance"

    #     return action, {}

    # def transition_open_(self):
    #     return 'end'

    def transition_actualisation_element(self):

        if self.start.vente_assurance:
            self.is_vente_assurance(self.start.date_debut, self.start.date_fin)
        
        return 'end'

    
    def is_vente_assurance(self, start_date, end_date):

        Party = Pool().get("party.party")

        list_of_save_elements = []
        listes_factures = []

        Ventes_Assurance = Pool().get("ventes.assurances")
        Ventes_ass = Ventes_Assurance.search([])
        Ventes_Assurance.delete(Ventes_ass)

        Invoices = Pool().get("account.invoice")
        Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted'])])

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
            try :
                assurance = facture[0].health_service.insurance_plan.company
            except AttributeError :
                assurance = Party.search([('name', 'ilike', '\%CLIENT PDMD')], limit=1)
                assurance = assurance[0]
            if assurance.name in dict_assurance:
                dict_assurance[assurance.id]['total_vente'] += facture[0].montant_assurance
            else:
                dict_assurance[assurance.id] = {
                    'assurance_name': assurance.name,  # nom réel du champ Many2One
                    'total_vente': facture[0].montant_assurance
                }

        list_of_save_elements = list(dict_assurance.values())
        Ventes_Assurance.create(list_of_save_elements)


        

    def syntheses_ventes(records, insurance=True):
        # Exemplaire de sortie de liste 
        # elements2 = ["total_amount", "montant_assurance", "Remise",  "montant_patient-amount_to_pay", "montant_patient", "amount_to_pay"]
        # elements = ["total_amount" , "montant_assurance", "montant_patient", "montant_patient-amount_to_pay", "amount_to_pay"]

        elements = []
        total_amount = Decimal(0)
        montant_assurance = Decimal(0)
        z_remise2 = Decimal(0)
        net_a_payer = Decimal(0)
        amount_to_pay = Decimal(0)
        difference = Decimal(0)
        total_amount2 = Decimal(0)

        for record in records:
            if record.health_service :
                if bool(record.health_service.insurance_plan) != insurance:
                    continue
                total_amount += record.untaxed_amount or Decimal(0)
                montant_assurance += record.montant_assurance or Decimal(0)
                z_remise2 += record.health_service.z_remise2 or Decimal(0)
                net_a_payer += record.montant_patient or Decimal(0)
                amount_to_pay += record.amount_to_pay or Decimal(0)
                total_amount2 += Decimal(record.untaxed_amount or 0) + Decimal(record.montant_assurance or 0)
        
        difference = net_a_payer - amount_to_pay
        
        elements.extend([
            total_amount,
            montant_assurance,
            z_remise2,
            net_a_payer,
            difference,
            amount_to_pay,
            total_amount2
        ])
        
        return elements