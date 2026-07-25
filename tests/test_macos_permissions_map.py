#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shared macOS CONFIG_TO_PLIST_MAPPING is the single source of truth."""

from unifypy.core.macos_permissions import CONFIG_TO_PLIST_MAPPING
from unifypy.platforms.macos.post_processor import CONFIG_TO_PLIST_MAPPING as post_map
from unifypy.pyinstaller.config_builder import CONFIG_TO_PLIST_MAPPING as builder_map
from unifypy.utils.entitlements_generator import EntitlementsGenerator
from unifypy.utils.info_plist_updater import InfoPlistUpdater


def test_shared_map_has_core_keys():
    assert CONFIG_TO_PLIST_MAPPING["microphone_usage_description"] == (
        "NSMicrophoneUsageDescription"
    )
    assert CONFIG_TO_PLIST_MAPPING["camera_usage_description"] == (
        "NSCameraUsageDescription"
    )
    assert CONFIG_TO_PLIST_MAPPING["speech_recognition_usage_description"] == (
        "NSSpeechRecognitionUsageDescription"
    )


def test_consumers_use_shared_map():
    assert EntitlementsGenerator.CONFIG_TO_PLIST_MAPPING is CONFIG_TO_PLIST_MAPPING
    assert InfoPlistUpdater.PERMISSION_MAPPING is CONFIG_TO_PLIST_MAPPING
    assert builder_map is CONFIG_TO_PLIST_MAPPING
    assert post_map is CONFIG_TO_PLIST_MAPPING
