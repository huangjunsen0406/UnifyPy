# macOS Permissions Configuration Guide

This document provides a comprehensive guide to configuring macOS permissions for applications packaged with UnifyPy. It explains how to properly set up privacy permissions and entitlements to ensure your application works correctly on macOS.

## Table of Contents

- [Overview](#overview)
- [Configuration Structure](#configuration-structure)
- [Available Permissions](#available-permissions)
  - [Device Permissions](#device-permissions)
  - [Network Permissions](#network-permissions)
  - [File Access Permissions](#file-access-permissions)
  - [Personal Information Permissions](#personal-information-permissions)
  - [System Permissions](#system-permissions)
- [Entitlements Mapping](#entitlements-mapping)
- [Sandboxed vs Non-Sandboxed Applications](#sandboxed-vs-non-sandboxed-applications)
- [Development Mode](#development-mode)
- [Configuration Examples](#configuration-examples)
- [Best Practices](#best-practices)

## Overview

macOS applications require explicit permission declarations to access sensitive system resources. UnifyPy automatically generates the necessary `entitlements.plist` and updates `Info.plist` based on your configuration, ensuring your application can access the required resources while maintaining security best practices.

## Configuration Structure

Permissions are configured in the `platforms.macos` section of your `build.json` file:

```json
{
  "platforms": {
    "macos": {
      "sandboxed": false,
      "microphone_usage_description": "This app needs microphone access to record audio",
      "camera_usage_description": "This app needs camera access to capture photos"
    }
  }
}
```

## Available Permissions

### Device Permissions

#### Microphone Access

```json
{
  "microphone_usage_description": "This app needs microphone access to record audio"
}
```

- **Info.plist Key**: `NSMicrophoneUsageDescription`
- **Entitlement (Non-Sandboxed)**: `com.apple.security.device.audio-input`
- **Entitlement (Sandboxed)**: `com.apple.security.device.microphone`
- **Use Case**: Audio recording, voice input, VoIP applications

#### Camera Access

```json
{
  "camera_usage_description": "This app needs camera access to capture photos"
}
```

- **Info.plist Key**: `NSCameraUsageDescription`
- **Entitlement**: `com.apple.security.device.camera`
- **Use Case**: Photo/video capture, video conferencing

#### Screen Capture

```json
{
  "screen_capture_usage_description": "This app needs to capture your screen for recording"
}
```

- **Info.plist Key**: `NSScreenCaptureUsageDescription`
- **Entitlement**: `com.apple.security.device.screen-capture`
- **Use Case**: Screen recording, screenshot tools, remote desktop

#### Speech Recognition

```json
{
  "speech_recognition_usage_description": "This app uses speech recognition for voice commands"
}
```

- **Info.plist Key**: `NSSpeechRecognitionUsageDescription`
- **Entitlement**: `com.apple.security.device.speech-recognition`
- **Use Case**: Voice assistants, dictation features

#### Bluetooth Access

```json
{
  "bluetooth_always_usage_description": "This app needs Bluetooth to connect to devices",
  "bluetooth_peripheral_usage_description": "This app needs to act as a Bluetooth peripheral"
}
```

- **Info.plist Keys**: `NSBluetoothAlwaysUsageDescription`, `NSBluetoothPeripheralUsageDescription`
- **Entitlement**: `com.apple.security.device.bluetooth`
- **Use Case**: Wireless device communication, IoT applications

### Network Permissions

#### Local Network Access

```json
{
  "local_network_usage_description": "This app needs local network access to discover devices"
}
```

- **Info.plist Key**: `NSLocalNetworkUsageDescription`
- **Entitlements**:
  - `com.apple.security.network.client` (Outgoing connections)
  - `com.apple.security.network.server` (Incoming connections)
- **Use Case**: Local device discovery, network services, peer-to-peer communication

### File Access Permissions

#### Desktop, Documents, and Downloads Folders

```json
{
  "desktop_folder_usage_description": "This app needs access to your Desktop to save files",
  "documents_folder_usage_description": "This app needs access to your Documents folder",
  "downloads_folder_usage_description": "This app needs access to your Downloads folder"
}
```

- **Info.plist Keys**: `NSDesktopFolderUsageDescription`, `NSDocumentsFolderUsageDescription`, `NSDownloadsFolderUsageDescription`
- **Entitlements**:
  - `com.apple.security.files.user-selected.read-write` (Desktop, Documents)
  - `com.apple.security.files.downloads.read-write` (Downloads)
- **Use Case**: File management applications, document editors

#### Network and Removable Volumes

```json
{
  "network_volumes_usage_description": "This app needs access to network volumes",
  "removable_volumes_usage_description": "This app needs access to removable storage"
}
```

- **Info.plist Keys**: `NSNetworkVolumesUsageDescription`, `NSRemovableVolumesUsageDescription`
- **Entitlement**: `com.apple.security.files.user-selected.read-write`
- **Use Case**: Backup applications, file synchronization

#### Photo Library

```json
{
  "photo_library_usage_description": "This app needs to access your photos",
  "photo_library_add_usage_description": "This app needs to add photos to your library"
}
```

- **Info.plist Keys**: `NSPhotoLibraryUsageDescription`, `NSPhotoLibraryAddUsageDescription`
- **Entitlement**: `com.apple.security.assets.pictures.read-write`
- **Use Case**: Photo editing, image management

#### Music Library

```json
{
  "music_usage_description": "This app needs to access your music library"
}
```

- **Info.plist Key**: `NSAppleMusicUsageDescription`
- **Entitlement**: `com.apple.security.assets.music.read-only`
- **Use Case**: Music players, audio analysis

### Personal Information Permissions

#### Location Services

```json
{
  "location_usage_description": "This app needs your location",
  "location_when_in_use_usage_description": "This app needs your location while in use",
  "location_always_and_when_in_use_usage_description": "This app needs continuous location access"
}
```

- **Info.plist Keys**: `NSLocationUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSLocationAlwaysAndWhenInUseUsageDescription`
- **Entitlement**: `com.apple.security.personal-information.location`
- **Use Case**: Maps, navigation, location-based services

#### Contacts

```json
{
  "contacts_usage_description": "This app needs access to your contacts"
}
```

- **Info.plist Key**: `NSContactsUsageDescription`
- **Entitlement**: `com.apple.security.personal-information.addressbook`
- **Use Case**: Communication apps, CRM systems

#### Calendar and Reminders

```json
{
  "calendars_usage_description": "This app needs access to your calendar",
  "calendars_write_only_access_usage_description": "This app needs to create calendar events",
  "calendars_full_access_usage_description": "This app needs full calendar access",
  "reminders_usage_description": "This app needs access to your reminders",
  "reminders_full_access_usage_description": "This app needs full access to your reminders"
}
```

- **Info.plist Keys**: `NSCalendarsUsageDescription`, `NSCalendarsWriteOnlyAccessUsageDescription`, `NSCalendarsFullAccessUsageDescription`, `NSRemindersUsageDescription`, `NSRemindersFullAccessUsageDescription`
- **Entitlement**: `com.apple.security.personal-information.calendars`
- **Use Case**: Scheduling apps, task management

### System Permissions

#### AppleScript and Automation

```json
{
  "apple_events_usage_description": "This app needs to control other applications"
}
```

- **Info.plist Key**: `NSAppleEventsUsageDescription`
- **Entitlement**: `com.apple.security.automation.apple-events`
- **Special Configuration**: You can specify scripting targets:

```json
{
  "apple_events_usage_description": "This app needs to control other applications",
  "scripting_targets": {
    "com.apple.finder": ["com.apple.events.appleevents"],
    "com.apple.systemevents": ["com.apple.events.appleevents"]
  }
}
```

- **Use Case**: Automation tools, workflow applications

#### Accessibility

```json
{
  "accessibility_usage_description": "This app needs accessibility access to automate tasks"
}
```

- **Info.plist Key**: `NSAccessibilityUsageDescription`
- **Use Case**: Automation tools, assistive technologies

#### System Administration

```json
{
  "system_administration_usage_description": "This app needs system administration privileges"
}
```

- **Info.plist Key**: `NSSystemAdministrationUsageDescription`
- **Entitlement**: `com.apple.security.temporary-exception.files.absolute-path.read-write`
- **Use Case**: System utilities, administrative tools

## Entitlements Mapping

UnifyPy automatically maps permission descriptions to the appropriate entitlements:

| Permission Description | Info.plist Key | Entitlement(s) | Notes |
|---|---|---|---|
| Microphone | `NSMicrophoneUsageDescription` | `com.apple.security.device.audio-input` (non-sandboxed)<br>`com.apple.security.device.microphone` (sandboxed) | Different entitlements for sandboxed vs non-sandboxed |
| Camera | `NSCameraUsageDescription` | `com.apple.security.device.camera` | Same for all apps |
| Screen Capture | `NSScreenCaptureUsageDescription` | `com.apple.security.device.screen-capture` | Requires macOS 10.15+ |
| Location | `NSLocationUsageDescription` | `com.apple.security.personal-information.location` | Multiple Info.plist variants available |
| Network | `NSLocalNetworkUsageDescription` | `com.apple.security.network.client`<br>`com.apple.security.network.server` | Server entitlement added if needed |

## Sandboxed vs Non-Sandboxed Applications

### Non-Sandboxed (Default)

```json
{
  "platforms": {
    "macos": {
      "sandboxed": false
    }
  }
}
```

- More flexible permissions
- Can access broader system resources
- Uses `com.apple.security.device.audio-input` for microphone
- Suitable for most desktop applications

### Sandboxed (Mac App Store)

```json
{
  "platforms": {
    "macos": {
      "sandboxed": true
    }
  }
}
```

- Required for Mac App Store distribution
- More restricted environment
- Uses `com.apple.security.device.microphone` for microphone
- Requires explicit file access permissions
- Automatically adds: `com.apple.security.app-sandbox = true`

## Development Mode

Enable development mode for testing unsigned applications:

```bash
python main.py . --config build.json --development
```

Development mode automatically adds:

- `com.apple.security.get-task-allow` (Debugging)
- `com.apple.security.cs.allow-jit` (JIT compilation for Python)
- `com.apple.security.cs.allow-unsigned-executable-memory` (Python runtime)
- `com.apple.security.cs.disable-library-validation` (Dynamic libraries)
- `com.apple.security.cs.allow-dyld-environment-variables` (Environment variables)
- Enhanced file system access permissions
- AppleScript automation permissions

## Configuration Examples

### Example 1: Video Conferencing Application

```json
{
  "name": "MyVideoChat",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "microphone_usage_description": "MyVideoChat needs microphone access to transmit your voice during calls",
      "camera_usage_description": "MyVideoChat needs camera access to transmit your video during calls",
      "local_network_usage_description": "MyVideoChat needs local network access to discover and connect to other devices"
    }
  }
}
```

### Example 2: Screen Recording Tool

```json
{
  "name": "ScreenRecorder",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "screen_capture_usage_description": "ScreenRecorder needs to capture your screen to create recordings",
      "microphone_usage_description": "ScreenRecorder needs microphone access to record audio commentary",
      "downloads_folder_usage_description": "ScreenRecorder needs access to your Downloads folder to save recordings"
    }
  }
}
```

### Example 3: Photo Editing Application

```json
{
  "name": "PhotoEditor",
  "platforms": {
    "macos": {
      "sandboxed": true,
      "photo_library_usage_description": "PhotoEditor needs to access your photos for editing",
      "photo_library_add_usage_description": "PhotoEditor needs to save edited photos to your library",
      "desktop_folder_usage_description": "PhotoEditor needs access to your Desktop to save exported files",
      "documents_folder_usage_description": "PhotoEditor needs access to your Documents folder to save projects"
    }
  }
}
```

### Example 4: Automation Tool

```json
{
  "name": "AutomationTool",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "apple_events_usage_description": "AutomationTool needs to control other applications to automate tasks",
      "accessibility_usage_description": "AutomationTool needs accessibility access to interact with UI elements",
      "scripting_targets": {
        "com.apple.finder": ["com.apple.events.appleevents"],
        "com.apple.systemevents": ["com.apple.events.appleevents"],
        "com.apple.Safari": ["com.apple.events.appleevents"]
      }
    }
  }
}
```

## Best Practices

### 1. **Provide Clear and Specific Descriptions**

Users are more likely to grant permissions when they understand why they're needed:

❌ Bad: `"This app needs camera access"`

✅ Good: `"MyVideoChat needs camera access to transmit your video during video calls"`

### 2. **Request Only Necessary Permissions**

Only request permissions that your application actually uses. Requesting unnecessary permissions can:
- Reduce user trust
- Cause Mac App Store rejection
- Trigger security warnings

### 3. **Choose the Correct Sandbox Mode**

- Use `sandboxed: true` if distributing through Mac App Store
- Use `sandboxed: false` for direct distribution or if you need broader system access

### 4. **Test with Development Mode First**

Always test your application with `--development` flag first to ensure all runtime requirements are met before creating production builds.

### 5. **Handle Permission Denials Gracefully**

Your application should handle cases where users deny permissions:
- Provide clear error messages
- Offer alternative functionality
- Allow users to enable permissions later through System Settings

### 6. **Keep Descriptions User-Friendly**

- Write in the user's language (consider localization)
- Use simple, non-technical language
- Focus on benefits to the user, not technical implementation

### 7. **Document Required Permissions**

Include a list of required permissions in your application's documentation so users know what to expect.

### 8. **Regular Permission Audits**

Periodically review your permission requests:
- Remove permissions that are no longer needed
- Update descriptions to reflect current functionality
- Check for new permission types that might be more appropriate

### 9. **Consider Progressive Permission Requests**

Instead of requesting all permissions upfront, request them when the functionality is first used. This provides better context to users.

### 10. **Test on Multiple macOS Versions**

Permission systems evolve across macOS versions. Test your application on:
- Latest macOS version
- Minimum supported macOS version
- Common versions in your user base

---

For more information about UnifyPy configuration, see the main [README](README_EN.md).

For issues or questions, please visit the [GitHub repository](https://github.com/huangjunsen0406/UnifyPy).
