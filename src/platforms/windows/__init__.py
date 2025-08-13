#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows平台打包器
"""

from .inno_setup import InnoSetupPackager
from .msi_packager import MSIPackager

__all__ = ['InnoSetupPackager', 'MSIPackager']