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

    vente_assurance = fields.Boolean("Ventes Par Assurances", help="Syntheses des Ventes par Assurances")

    tarifaire = fields.Many2One("product.price_list", "Tarifaire", help="Nombre de patients pour un tarifaire. Ceci ne se base que sur des factures postées et payées. Tarifaire à synthétiser")
    all_tarifaire = fields.Boolean("Tous les tarifaires", help="Nombre de patients pour un tarifaire. Ceci ne se base que sur des factures postées et payées. Synthèses de tous les tarifaires utilisés")

    product = fields.Many2One("product.product", "Produit", help="Produit à synthétiser")
    all_product = fields.Boolean("Tous les produits", help="Synthèses de tous les produits vendus")

    metriques = fields.Boolean("Valeurs Uniques", help="Valeurs Uniques Autour des Factures")

    validation = fields.Boolean("Validation des Services", help="Synthèse des validations par services")


class GenerateResultsReports(Wizard):
    'Generation des Rapports En Totalité'
    __name__ = 'rapports.refresh.all'

    start = StateView('elements.refresh.init',
        'z_all_synthesis.view_element_actualisation', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Actualisation', 'actualisation_element', 'tryton-ok',
                True),
            ])
    
    actualisation_element = StateTransition()

    def transition_actualisation_element(self):

        if self.start.vente_assurance:
            self.is_vente_assurance(self.start.date_debut, self.start.date_fin)

        if self.start.tarifaire and not self.start.all_tarifaire:
            self.is_tarifaire(self.start.date_debut, self.start.date_fin)
        elif self.start.all_tarifaire and not self.start.tarifaire:
            self.is_all_tarifaire(self.start.date_debut, self.start.date_fin)

        if self.start.product and not self.start.all_product:
            self.is_product(self.start.date_debut, self.start.date_fin)
        elif self.start.all_product and not self.start.product:
            self.is_all_product(self.start.date_debut, self.start.date_fin) 

        if self.start.metriques:
            self.is_metriques(self.start.date_debut, self.start.date_fin)      

        if self.start.validation:
            self.is_validation(self.start.date_debut, self.start.date_fin)    
        
        return 'end'


    def is_product(self, start_date, end_date):
        """
        This method is used to synthesize the sales of a specific product
        between the given start and end dates.
        """

        Produits_Sur_Peride = Pool().get("ventes.produits.periode")
        Produits_Sur_Peride.delete(Produits_Sur_Peride.search([]))

        Product = Pool().get("product.product")
        Invoices = Pool().get("account.invoice")

        Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted'])])

        listes_factures = []
        for Facture in Factures:
            if Facture.number not in listes_factures:
                listes_factures.append(Facture.number)
        
        for Facture in Factures:
            if Facture.reference in listes_factures:
                listes_factures.remove(Facture.reference)
                try :
                    listes_factures.remove(Facture.number)
                except ValueError:
                    pass
            else:
                factures_ref = Invoices.search([('number', '=', Facture.reference)])
                if factures_ref:
                    try :
                        listes_factures.remove(Facture.reference)
                        nbr_factures_creditees += 1
                    except ValueError:
                        pass
        
        if not self.start.product:
            return
        
        product = Product(self.start.product.id)

        nbr = 0
        total_vente = float(0)
        elt = {}
        for facture_number in listes_factures:
            facture = Invoices.search([('number', '=', facture_number)], limit=1)
            for line in facture[0].lines:
                if line.product.id == product.id:
                    nbr += 1
                    total_vente += float(line.montant_produit())*float(line.quantity)

        elt['produit_name'] = product
        elt['nbr'] = nbr
        elt['total_vente'] = total_vente
        
        Produits_Sur_Peride.create([elt])


    def is_all_product(self, start_date, end_date):
        """
        This method is used to synthesize the sales of all products
        between the given start and end dates.
        """

        Produits_Sur_Peride = Pool().get("ventes.produits.periode")
        Produits_Sur_Peride.delete(Produits_Sur_Peride.search([]))

        Product = Pool().get("product.product")
        Invoices = Pool().get("account.invoice")

        Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted'])])

        listes_factures = []
        for Facture in Factures:
            if Facture.number not in listes_factures:
                listes_factures.append(Facture.number)
        
        for Facture in Factures:
            if Facture.reference in listes_factures:
                listes_factures.remove(Facture.reference)
                try :
                    listes_factures.remove(Facture.number)
                except ValueError:
                    pass
            else:
                factures_ref = Invoices.search([('number', '=', Facture.reference)])
                if factures_ref:
                    try :
                        listes_factures.remove(Facture.reference)
                        nbr_factures_creditees += 1
                    except ValueError:
                        pass
        dict_produit = {}
        for facture_number in listes_factures:
            facture = Invoices.search([('number', '=', facture_number)], limit=1)
            for line in facture[0].lines:
                if line.product.id in dict_produit:
                    dict_produit[line.product.id]['nbr'] += 1
                    dict_produit[line.product.id]['total_vente'] += float(line.montant_produit())*float(line.quantity)
                else:
                    dict_produit[line.product.id] = {
                        'produit_name': line.product,
                        'nbr': 1,
                        'total_vente': float(line.montant_produit())*float(line.quantity)
                    }

        list_of_save_elements = list(dict_produit.values())
        Produits_Sur_Peride.create(list_of_save_elements)

        return True
    

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
                try :
                    listes_factures.remove(Facture.number)
                except ValueError:
                    pass
            else:
                factures_ref = Invoices.search([('number', '=', Facture.reference)])
                if factures_ref:
                    try :
                        listes_factures.remove(Facture.reference)
                        nbr_factures_creditees += 1
                    except ValueError:
                        pass

        dict_assurance = {}
        nbr_facture = Decimal(0)
        for facture_number in listes_factures:
            facture = Invoices.search([('number', '=', facture_number)], limit=1)

            if not facture:
                continue
            try :
                assurance = facture[0].health_service.insurance_plan.company
            except AttributeError :
                assurance = Party.search([('name', 'ilike', 'CLIENTS PDMD')], limit=1)
                assurance = assurance[0]

            if assurance.id in dict_assurance:
                dict_assurance[assurance.id]['total_vente'] += facture[0].montant_assurance
                nbr_facture += 1
                dict_assurance[assurance.id]['nb_facture'] = nbr_facture
            else:
                dict_assurance[assurance.id] = {
                    'assurance_name': assurance.name,  # nom réel du champ Many2One
                    'total_vente': facture[0].montant_assurance,
                    'nb_facture': 1  # Initialisation du nombre de factures
                }

        list_of_save_elements = list(dict_assurance.values())
        Ventes_Assurance.create(list_of_save_elements)


    def is_metriques(self, start_date, end_date):
        """
        This method is used to synthesize unique values around invoices
        between the given start and end dates.
        """

        Metriques = Pool().get("ventes.metriques")
        Metriques.delete(Metriques.search([]))

        Invoices = Pool().get("account.invoice")

        Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted'])])

        nbr_factures_assurance = 0
        nbr_factures_normales = 0
        nbr_factures_postees = 0
        nbr_factures_payees = 0
        nbr_factures_creditees = 0

        listes_factures = []
        for Facture in Factures:
            if Facture.number not in listes_factures:
                listes_factures.append(Facture.number)
        
        for Facture in Factures:
            if Facture.reference in listes_factures:
                nbr_factures_creditees += 1
                listes_factures.remove(Facture.reference)
                try :
                    listes_factures.remove(Facture.number)
                except ValueError:
                    pass
            else:
                factures_ref = Invoices.search([('number', '=', Facture.reference)])
                if factures_ref:
                    try :
                        listes_factures.remove(Facture.reference)
                        nbr_factures_creditees += 1
                    except ValueError:
                        pass


        for Facture in listes_factures:
            facture = Invoices.search([('number', '=', Facture)], limit=1)
            Facture = facture[0]
            if Facture.health_service and Facture.health_service.insurance_plan:
                nbr_factures_assurance += 1
            
            if Facture.health_service and not Facture.health_service.insurance_plan:
                nbr_factures_normales += 1
            
            if Facture.state == 'posted':
                nbr_factures_postees += 1
            
            if Facture.state == 'paid':
                nbr_factures_payees += 1
                

        metriques_data = {
            'nbr_factures_assurance': nbr_factures_assurance,
            'nbr_factures_postees': nbr_factures_postees,
            'nbr_factures_payees': nbr_factures_payees,
            'nbr_factures_creditees': nbr_factures_creditees,
            'nbr_factures_normales' : nbr_factures_normales
        }

        Metriques.create([metriques_data])


    def is_validation(self, start_date, end_date):
        """
        This method is used to synthesize the validation of services
        between the given start and end dates.
        """

        Validation_Services = Pool().get("validations.services")
        Validation_Services.delete(Validation_Services.search([]))

        Validations_Examens = Pool().get("all_syntheses")
        validations_Cotations = Pool().get("syntheses_cotation")

        date_debut = datetime.combine(start_date, time.min)
        date_fin = datetime.combine(end_date, time.max)

        V_E = Validations_Examens.search([('date_emm', '>=',  date_debut), ('date_result', '<=', date_fin)])
        V_C = validations_Cotations.search([('date_service', '>=', start_date), ('date_service', '<=', end_date)])

        dict_elt = {}
        nbr_validate_lab = 0
        nbr_no_validate_lab = 0
        pourcentage_lab = float(0)

        nbr_validate_img = 0
        nbr_no_validate_img = 0
        pourcentage_img = float(0)

        nbr_validate_exp = 0
        nbr_no_validate_exp = 0
        pourcentage_exp = float(0)

        nbr_validate_cot = 0
        nbr_no_validate_cot = 0
        pourcentage_cot = float(0)

        for elt in V_C:
            if elt.correct :
                nbr_validate_cot += 1
            else :
                nbr_no_validate_cot += 1
        
        for elt in V_E:
            if elt.service_examen == "lab" :
                if elt.correct:
                    nbr_validate_lab += 1
                else :
                    nbr_no_validate_lab +=1 
            if elt.service_examen == "img" :
                if elt.correct:
                    nbr_validate_img += 1
                else :
                    nbr_no_validate_img += 1
            if elt.service_examen == 'exp' :
                if elt.correct:
                    nbr_validate_exp += 1
                else:
                    nbr_no_validate_exp += 1
        
        pourcentage_exp += nbr_validate_exp / (nbr_validate_exp + nbr_no_validate_exp)
        pourcentage_img += nbr_validate_img / (nbr_validate_img + nbr_no_validate_img)
        pourcentage_lab += nbr_validate_lab / (nbr_validate_lab + nbr_no_validate_lab)
        pourcentage_cot += nbr_validate_cot / (nbr_validate_cot + nbr_no_validate_cot)

        dict_elt["lab"]={
            "service_name" : "Laboratoire",
            "nbr_validate" : nbr_validate_lab,
            "nbr_no_validate" : nbr_no_validate_lab,
            "pourcentage" : pourcentage_lab
        }

        dict_elt["img"]={
            "service_name" : "Imagerie",
            "nbr_validate" : nbr_validate_img,
            "nbr_no_validate" : nbr_no_validate_img,
            "pourcentage" : pourcentage_img
        }

        dict_elt["exp"]={
            "service_name" : "Exploration",
            "nbr_validate" : nbr_validate_exp,
            "nbr_no_validate" : nbr_no_validate_exp,
            "pourcentage" : pourcentage_exp
        }

        dict_elt['cotation']={
            "service_name" : "Cotation",
            "nbr_validate" : nbr_validate_cot,
            "nbr_no_validate" : nbr_no_validate_cot,
            "pourcentage" : pourcentage_cot
        }

        list_of_save_elements = []
        list_of_save_elements.extend(list(dict_elt.values()))

        Validation_Services.create(list_of_save_elements)

        return True


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
    

    def is_tarifaire(self, start_date, end_date):
        """
        CETTE MÉTHODE EST UTILISÉE POUR AVOIR LE NOMBRE DE PATIENT SUR UNE PÉRIODE DONNÉE
        AYANT FAIT LA CAMPAGNE SELECTIONNÉE
        """

        Patients_Tarifaire = Pool().get("patients.tarifaire")
        Patients_Tarifaire.delete(Patients_Tarifaire.search([]))

        Invoices = Pool().get("account.invoice")

        # Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted']), ("party.sale_price_list", "=", self.start.tarifaire)])

        Factures = Invoices.search([('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('state', 'in', ['paid', 'posted'])])

        listes_factures = []
        for Facture in Factures:
            if Facture.number not in listes_factures:
                listes_factures.append(Facture.number)
        
        for Facture in Factures:
            if Facture.reference in listes_factures:
                listes_factures.remove(Facture.reference)
                try :
                    listes_factures.remove(Facture.number)
                except ValueError:
                    pass
            else:
                factures_ref = Invoices.search([('number', '=', Facture.reference)])
                if factures_ref:
                    try :
                        listes_factures.remove(Facture.reference)
                        nbr_factures_creditees += 1
                    except ValueError:
                        pass

        nbr_patients = set()
        for facture_number in listes_factures:

            facture = Invoices.search([
                ('number', '=', facture_number)
            ], limit=1)

            if not facture:
                continue

            f = facture[0]

            if not f.party.sale_price_list:
                continue

            if facture[0].party.sale_price_list.id == self.start.tarifaire.id:
                nbr_patients.add(facture[0].party.id)

        elt = {
            'tarifaire_name': self.start.tarifaire,
            'nbr_patients': len(nbr_patients)
        }

        Patients_Tarifaire.create([elt])

        return True


    def is_all_tarifaire(self, start_date, end_date):
        """
        Calcule le nombre total de patients pour CHAQUE tarifaire (price_list)
        sur une période donnée, puis enregistre les résultats dans
        patients.tarifaire.
        """

        Invoice = Pool().get("account.invoice")
        PriceList = Pool().get("product.price_list")
        PatientsTarifaire = Pool().get("patients.tarifaire")

        # Reset table
        PatientsTarifaire.delete(PatientsTarifaire.search([]))

        # Récupérer tous les tarifaires existants
        tarifaires = PriceList.search([])

        for tarifaire in tarifaires:

            # -----------------------
            # 1. FACTURES DU TARIFAIRE
            # -----------------------
            factures = Invoice.search([
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", end_date),
                ("state", "in", ["paid", "posted"]),
            ])

            # -----------------------
            # 2. LISTE DES NUMÉROS UNIQUES (anti doublons + crédit/débit)
            # -----------------------
            liste_nums = []
            for f in factures:
                if f.number not in liste_nums:
                    liste_nums.append(f.number)

            # Gestion des références croisées (crédit/débit)
            for f in factures:
                # Cas où la référence existe dans la liste → facture créditée ou annulée
                if f.reference in liste_nums:
                    try:
                        liste_nums.remove(f.reference)
                    except ValueError:
                        pass
                    try:
                        liste_nums.remove(f.number)
                    except ValueError:
                        pass
                else:
                    # Si la référence correspond à une facture existante, supprimer
                    fact_ref = Invoice.search([("number", "=", f.reference)], limit=1)
                    if fact_ref:
                        try:
                            liste_nums.remove(f.reference)
                        except ValueError:
                            pass

            # -----------------------
            # 3. CALCUL DES PATIENTS UNIQUES
            # -----------------------
            dict_tarifaire = {}

            for numero in liste_nums:

                facture = Invoice.search([("number", "=", numero)], limit=1)
                if not facture:
                    continue

                f = facture[0]

                if f.party.sale_price_list == None:
                    continue

                tarifaire_id = f.party.sale_price_list.id

                # Initialiser si nécessaire
                if tarifaire_id not in dict_tarifaire:
                    dict_tarifaire[tarifaire_id] = {
                        'tarifaire_name': f.party.sale_price_list,     # Many2One accepté dans create()
                        'patients_set': set(),              # on stocke les patients uniques
                    }

                # Ajouter patient
                dict_tarifaire[tarifaire_id]['patients_set'].add(f.party.id)
        # -----------------------
        # 4. ENREGISTREMENT DU RÉSULTAT
        # -----------------------
        save_list = []
        for item in dict_tarifaire.values():
            save_list.append({
                'tarifaire_name': item['tarifaire_name'],
                'nbr_patients': len(item['patients_set'])
            })

        PatientsTarifaire.create(save_list)

        return True


