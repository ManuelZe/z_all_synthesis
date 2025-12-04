# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from . import z_all_synthesis
from .wizard import generate_report

__all__ = ['register']


def register():
    Pool.register(
        z_all_synthesis.Classement_Assurance_vente,
        generate_report.Elements_Actualisations,
        z_all_synthesis.Produits_Sur_Periode,
        z_all_synthesis.Metriques,
        z_all_synthesis.Validation_Services,
        z_all_synthesis.Nombre_Patients_Par_Tarifaire,
        module='z_all_synthesis', type_='model')
    Pool.register(
        generate_report.GenerateResultsReports,
        module='z_all_synthesis', type_='wizard')
    Pool.register(
        module='z_all_synthesis', type_='report')
