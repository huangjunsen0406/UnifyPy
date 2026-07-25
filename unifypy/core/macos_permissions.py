#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
macOS config key → Info.plist NS*UsageDescription mapping.

Single source of truth for privacy/permission description keys used by:
- EntitlementsGenerator
- InfoPlistUpdater
- PyInstallerConfigBuilder
- MacOSPostProcessor
"""

from typing import Dict

# CONFIG_TO_PLIST_MAPPING: config key -> NS*UsageDescription
# Union of maps previously duplicated in entitlements_generator,
# info_plist_updater, config_builder, and post_processor.
CONFIG_TO_PLIST_MAPPING = {
    # Media devices
    "microphone_usage_description": "NSMicrophoneUsageDescription",
    "camera_usage_description": "NSCameraUsageDescription",
    "audio_usage_description": "NSAudioUsageDescription",
    "screen_capture_usage_description": "NSScreenCaptureUsageDescription",
    "speech_recognition_usage_description": "NSSpeechRecognitionUsageDescription",
    # Location
    "location_usage_description": "NSLocationUsageDescription",
    "location_when_in_use_usage_description": "NSLocationWhenInUseUsageDescription",
    "location_always_and_when_in_use_usage_description": (
        "NSLocationAlwaysAndWhenInUseUsageDescription"
    ),
    # Personal information
    "contacts_usage_description": "NSContactsUsageDescription",
    "calendars_usage_description": "NSCalendarsUsageDescription",
    "calendars_write_only_access_usage_description": (
        "NSCalendarsWriteOnlyAccessUsageDescription"
    ),
    "calendars_full_access_usage_description": "NSCalendarsFullAccessUsageDescription",
    "reminders_usage_description": "NSRemindersUsageDescription",
    "reminders_full_access_usage_description": "NSRemindersFullAccessUsageDescription",
    # Photos / media libraries
    "photo_library_usage_description": "NSPhotoLibraryUsageDescription",
    "photo_library_add_usage_description": "NSPhotoLibraryAddUsageDescription",
    "music_usage_description": "NSAppleMusicUsageDescription",
    # Connectivity
    "bluetooth_always_usage_description": "NSBluetoothAlwaysUsageDescription",
    "bluetooth_peripheral_usage_description": "NSBluetoothPeripheralUsageDescription",
    "local_network_usage_description": "NSLocalNetworkUsageDescription",
    # System / automation
    "apple_events_usage_description": "NSAppleEventsUsageDescription",
    "system_administration_usage_description": "NSSystemAdministrationUsageDescription",
    "accessibility_usage_description": "NSAccessibilityUsageDescription",
    # Folder access
    "desktop_folder_usage_description": "NSDesktopFolderUsageDescription",
    "documents_folder_usage_description": "NSDocumentsFolderUsageDescription",
    "downloads_folder_usage_description": "NSDownloadsFolderUsageDescription",
    "network_volumes_usage_description": "NSNetworkVolumesUsageDescription",
    "removable_volumes_usage_description": "NSRemovableVolumesUsageDescription",
    # Health / motion / home / Siri / TV (config_builder extras)
    "motion_usage_description": "NSMotionUsageDescription",
    "health_share_usage_description": "NSHealthShareUsageDescription",
    "health_update_usage_description": "NSHealthUpdateUsageDescription",
    "home_kit_usage_description": "NSHomeKitUsageDescription",
    "siri_usage_description": "NSSiriUsageDescription",
    "tv_provider_usage_description": "NSVideoSubscriberAccountUsageDescription",
    # File provider
    "file_provider_presence_usage_description": "NSFileProviderPresenceUsageDescription",
    "file_provider_domain_usage_description": "NSFileProviderDomainUsageDescription",
}  # type: Dict[str, str]
