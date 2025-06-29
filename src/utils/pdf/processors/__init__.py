"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Prozessor-Module für verschiedene Dokumenttypen
"""

from .ni43101 import NI43101Processor
from .environmental import EnvironmentalReportProcessor
from .financial import FinancialReportProcessor
from .technical import TechnicalReportProcessor

__all__ = [
    'NI43101Processor',
    'EnvironmentalReportProcessor',
    'FinancialReportProcessor',
    'TechnicalReportProcessor'
]