# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from . import z_all_synthesis
from .wizard import generate_report

__all__ = ['register']


def register():
    Pool.register(
        z_all_synthesis.Classement_Assurance_vente,
        z_all_synthesis.Dashboard_General,
        generate_report.Elements_Actualisations,
        module='z_all_synthesis', type_='model')
    Pool.register(
        generate_report.GenerateResultsReports,
        module='z_all_synthesis', type_='wizard')
    Pool.register(
        module='z_all_synthesis', type_='report')
