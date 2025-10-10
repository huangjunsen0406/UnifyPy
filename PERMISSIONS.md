# macOS 权限配置指南

本文为使用 UnifyPy 打包的应用提供 macOS 权限配置的完整指南。通过配置隐私权限与 Entitlements，可确保应用在 macOS 上既能正常访问所需资源，也符合平台安全最佳实践。

## 目录

- [概述](#概述)
- [配置结构](#配置结构)
- [可用权限](#可用权限)
  - [设备权限](#设备权限)
  - [网络权限](#网络权限)
  - [文件访问权限](#文件访问权限)
  - [个人信息权限](#个人信息权限)
  - [系统权限](#系统权限)
- [Entitlements 映射](#entitlements-映射)
- [沙盒与非沙盒应用](#沙盒与非沙盒应用)
- [开发模式](#开发模式)
- [配置示例](#配置示例)
- [最佳实践](#最佳实践)

## 概述

在 macOS 上，应用访问敏感系统资源必须显式声明权限。UnifyPy 会根据你的配置自动生成 `entitlements.plist` 并更新 `Info.plist`，使应用在保证安全的同时，获得所需访问能力。

## 配置结构

在 `build.json` 的 `platforms.macos` 节点下配置权限：

```json
{
  "platforms": {
    "macos": {
      "sandboxed": false,
      "microphone_usage_description": "此应用需要使用麦克风以录制音频",
      "camera_usage_description": "此应用需要使用摄像头以拍摄照片"
    }
  }
}
```

## 可用权限

### 设备权限

#### 麦克风访问（Microphone Access）

```json
{
  "microphone_usage_description": "此应用需要使用麦克风以录制音频"
}
```

- Info.plist 键：`NSMicrophoneUsageDescription`
- Entitlement（非沙盒）：`com.apple.security.device.audio-input`
- Entitlement（沙盒）：`com.apple.security.device.microphone`
- 适用场景：音频录制、语音输入、VoIP 应用

#### 摄像头访问（Camera Access）

```json
{
  "camera_usage_description": "此应用需要使用摄像头以拍摄照片"
}
```

- Info.plist 键：`NSCameraUsageDescription`
- Entitlement：`com.apple.security.device.camera`
- 适用场景：拍照/录像、视频会议

#### 屏幕捕获（Screen Capture）

```json
{
  "screen_capture_usage_description": "此应用需要捕获屏幕以进行录制"
}
```

- Info.plist 键：`NSScreenCaptureUsageDescription`
- Entitlement：`com.apple.security.device.screen-capture`
- 适用场景：屏幕录制、截屏工具、远程桌面

#### 语音识别（Speech Recognition）

```json
{
  "speech_recognition_usage_description": "此应用使用语音识别以执行语音指令"
}
```

- Info.plist 键：`NSSpeechRecognitionUsageDescription`
- Entitlement：`com.apple.security.device.speech-recognition`
- 适用场景：语音助理、听写功能

#### 蓝牙访问（Bluetooth Access）

```json
{
  "bluetooth_always_usage_description": "此应用需要使用蓝牙以连接设备",
  "bluetooth_peripheral_usage_description": "此应用需要作为蓝牙外设工作"
}
```

- Info.plist 键：`NSBluetoothAlwaysUsageDescription`、`NSBluetoothPeripheralUsageDescription`
- Entitlement：`com.apple.security.device.bluetooth`
- 适用场景：无线设备通信、IoT 应用

### 网络权限

#### 本地网络访问（Local Network Access）

```json
{
  "local_network_usage_description": "此应用需要本地网络访问以发现设备"
}
```

- Info.plist 键：`NSLocalNetworkUsageDescription`
- Entitlements：
  - `com.apple.security.network.client`（出站连接）
  - `com.apple.security.network.server`（入站连接）
- 适用场景：本地设备发现、网络服务、点对点通信

### 文件访问权限

#### 桌面、文稿与下载文件夹

```json
{
  "desktop_folder_usage_description": "此应用需要访问桌面以保存文件",
  "documents_folder_usage_description": "此应用需要访问文稿文件夹",
  "downloads_folder_usage_description": "此应用需要访问下载文件夹"
}
```

- Info.plist 键：`NSDesktopFolderUsageDescription`、`NSDocumentsFolderUsageDescription`、`NSDownloadsFolderUsageDescription`
- Entitlements：
  - `com.apple.security.files.user-selected.read-write`（桌面、文稿）
  - `com.apple.security.files.downloads.read-write`（下载）
- 适用场景：文件管理、文档编辑

#### 网络卷与可移动卷

```json
{
  "network_volumes_usage_description": "此应用需要访问网络卷",
  "removable_volumes_usage_description": "此应用需要访问可移动存储"
}
```

- Info.plist 键：`NSNetworkVolumesUsageDescription`、`NSRemovableVolumesUsageDescription`
- Entitlement：`com.apple.security.files.user-selected.read-write`
- 适用场景：备份应用、文件同步

#### 照片图库（Photo Library）

```json
{
  "photo_library_usage_description": "此应用需要访问您的照片",
  "photo_library_add_usage_description": "此应用需要向图库添加照片"
}
```

- Info.plist 键：`NSPhotoLibraryUsageDescription`、`NSPhotoLibraryAddUsageDescription`
- Entitlement：`com.apple.security.assets.pictures.read-write`
- 适用场景：照片编辑、图片管理

#### 音乐资料库（Music Library）

```json
{
  "music_usage_description": "此应用需要访问您的音乐资料库"
}
```

- Info.plist 键：`NSAppleMusicUsageDescription`
- Entitlement：`com.apple.security.assets.music.read-only`
- 适用场景：音乐播放器、音频分析

### 个人信息权限

#### 定位服务（Location Services）

```json
{
  "location_usage_description": "此应用需要访问您的位置信息",
  "location_when_in_use_usage_description": "此应用在使用时需要访问您的位置信息",
  "location_always_and_when_in_use_usage_description": "此应用需要持续的位置信息访问"
}
```

- Info.plist 键：`NSLocationUsageDescription`、`NSLocationWhenInUseUsageDescription`、`NSLocationAlwaysAndWhenInUseUsageDescription`
- Entitlement：`com.apple.security.personal-information.location`
- 适用场景：地图、导航、基于位置的服务

#### 通讯录（Contacts）

```json
{
  "contacts_usage_description": "此应用需要访问您的联系人"
}
```

- Info.plist 键：`NSContactsUsageDescription`
- Entitlement：`com.apple.security.personal-information.addressbook`
- 适用场景：通信应用、CRM 系统

#### 日历与提醒事项（Calendar and Reminders）

```json
{
  "calendars_usage_description": "此应用需要访问您的日历",
  "calendars_write_only_access_usage_description": "此应用需要创建日历事件",
  "calendars_full_access_usage_description": "此应用需要对日历的完整访问",
  "reminders_usage_description": "此应用需要访问您的提醒事项",
  "reminders_full_access_usage_description": "此应用需要对提醒事项的完整访问"
}
```

- Info.plist 键：`NSCalendarsUsageDescription`、`NSCalendarsWriteOnlyAccessUsageDescription`、`NSCalendarsFullAccessUsageDescription`、`NSRemindersUsageDescription`、`NSRemindersFullAccessUsageDescription`
- Entitlement：`com.apple.security.personal-information.calendars`
- 适用场景：日程安排、任务管理

### 系统权限

#### AppleScript 与自动化（AppleScript and Automation）

```json
{
  "apple_events_usage_description": "此应用需要控制其他应用"
}
```

- Info.plist 键：`NSAppleEventsUsageDescription`
- Entitlement：`com.apple.security.automation.apple-events`
- 可选配置：可指定脚本目标（scripting targets）：

```json
{
  "apple_events_usage_description": "此应用需要控制其他应用",
  "scripting_targets": {
    "com.apple.finder": ["com.apple.events.appleevents"],
    "com.apple.systemevents": ["com.apple.events.appleevents"]
  }
}
```

- 适用场景：自动化工具、工作流应用

#### 辅助功能（Accessibility）

```json
{
  "accessibility_usage_description": "此应用需要辅助功能权限以自动化任务"
}
```

- Info.plist 键：`NSAccessibilityUsageDescription`
- 适用场景：自动化工具、辅助技术

#### 系统管理（System Administration）

```json
{
  "system_administration_usage_description": "此应用需要系统管理权限"
}
```

- Info.plist 键：`NSSystemAdministrationUsageDescription`
- Entitlement：`com.apple.security.temporary-exception.files.absolute-path.read-write`
- 适用场景：系统工具、管理类工具

## Entitlements 映射

UnifyPy 会将权限描述自动映射到相应的 Entitlements：

| 权限描述 | Info.plist 键 | Entitlement | 备注 |
|---|---|---|---|
| 麦克风 | `NSMicrophoneUsageDescription` | `com.apple.security.device.audio-input`（非沙盒）<br>`com.apple.security.device.microphone`（沙盒） | 沙盒与非沙盒使用不同 Entitlement |
| 摄像头 | `NSCameraUsageDescription` | `com.apple.security.device.camera` | 适用于所有应用 |
| 屏幕捕获 | `NSScreenCaptureUsageDescription` | `com.apple.security.device.screen-capture` | 需要 macOS 10.15+ |
| 定位 | `NSLocationUsageDescription` | `com.apple.security.personal-information.location` | 提供多种 Info.plist 变体 |
| 网络 | `NSLocalNetworkUsageDescription` | `com.apple.security.network.client`<br>`com.apple.security.network.server` | 视需求添加 server Entitlement |

## 沙盒与非沙盒应用

### 非沙盒（默认）

```json
{
  "platforms": {
    "macos": {
      "sandboxed": false
    }
  }
}
```

- 权限更灵活
- 可访问更广泛的系统资源
- 麦克风使用 `com.apple.security.device.audio-input`
- 适用于多数桌面应用的直接分发

### 沙盒（Mac App Store）

```json
{
  "platforms": {
    "macos": {
      "sandboxed": true
    }
  }
}
```

- Mac App Store 分发所必需
- 运行环境更受限
- 麦克风使用 `com.apple.security.device.microphone`
- 需要显式的文件访问权限
- 将自动添加：`com.apple.security.app-sandbox = true`

## 开发模式

启用开发模式以测试未签名应用：

```bash
python main.py . --config build.json --development
```

开发模式会自动添加：

- `com.apple.security.get-task-allow`（调试）
- `com.apple.security.cs.allow-jit`（Python 的 JIT 编译）
- `com.apple.security.cs.allow-unsigned-executable-memory`（Python 运行时）
- `com.apple.security.cs.disable-library-validation`（动态库）
- `com.apple.security.cs.allow-dyld-environment-variables`（动态链接器环境变量）
- 增强的文件系统访问权限
- AppleScript 自动化权限

## 配置示例

### 示例 1：视频会议应用

```json
{
  "name": "MyVideoChat",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "microphone_usage_description": "MyVideoChat 需要麦克风权限以在通话中传输你的声音",
      "camera_usage_description": "MyVideoChat 需要摄像头权限以在通话中传输你的视频",
      "local_network_usage_description": "MyVideoChat 需要本地网络访问以发现并连接其他设备"
    }
  }
}
```

### 示例 2：屏幕录制工具

```json
{
  "name": "ScreenRecorder",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "screen_capture_usage_description": "ScreenRecorder 需要捕获屏幕以创建录制",
      "microphone_usage_description": "ScreenRecorder 需要麦克风权限以录制解说音频",
      "downloads_folder_usage_description": "ScreenRecorder 需要访问下载文件夹以保存录制文件"
    }
  }
}
```

### 示例 3：照片编辑应用

```json
{
  "name": "PhotoEditor",
  "platforms": {
    "macos": {
      "sandboxed": true,
      "photo_library_usage_description": "PhotoEditor 需要访问你的照片以进行编辑",
      "photo_library_add_usage_description": "PhotoEditor 需要将编辑后的照片保存到图库",
      "desktop_folder_usage_description": "PhotoEditor 需要访问桌面以保存导出文件",
      "documents_folder_usage_description": "PhotoEditor 需要访问文稿以保存项目"
    }
  }
}
```

### 示例 4：自动化工具

```json
{
  "name": "AutomationTool",
  "platforms": {
    "macos": {
      "sandboxed": false,
      "apple_events_usage_description": "AutomationTool 需要控制其他应用以自动化任务",
      "accessibility_usage_description": "AutomationTool 需要辅助功能权限以与界面元素交互",
      "scripting_targets": {
        "com.apple.finder": ["com.apple.events.appleevents"],
        "com.apple.systemevents": ["com.apple.events.appleevents"],
        "com.apple.Safari": ["com.apple.events.appleevents"]
      }
    }
  }
}
```

## 最佳实践

### 1. 清晰且具体的描述

用户更愿意授予他们理解用途的权限：

❌ 不佳：`"此应用需要摄像头权限"`

✅ 良好：`"MyVideoChat 需要摄像头权限以在视频通话中传输你的视频"`

### 2. 仅请求必要的权限

只请求应用实际使用到的权限。请求不必要的权限可能会：
- 降低用户信任
- 导致 Mac App Store 审核被拒
- 触发安全警告

### 3. 选择正确的沙盒模式

- 通过 Mac App Store 分发时使用 `sandboxed: true`
- 直接分发或需要更广系统访问时使用 `sandboxed: false`

### 4. 先使用开发模式进行测试

先用 `--development` 运行，确保运行时需求满足，再进行生产构建。

### 5. 优雅处理权限被拒绝

当用户拒绝权限时，应用应：
- 提供明确的错误提示
- 提供替代功能
- 支持引导用户稍后在系统设置中开启

### 6. 面向用户、易于理解

- 使用用户的语言（可考虑本地化）
- 避免过度技术化的表述
- 以用户收益为中心，而非实现细节

### 7. 文档化所需权限

在应用文档中列出所需权限，让用户有预期。

### 8. 定期审查权限

定期检查权限请求：
- 删除不再需要的权限
- 更新描述以反映当前功能
- 检查是否有更合适的新权限类型

### 9. 渐进式请求权限

避免在首次启动时一次性请求全部权限。应在首次使用相关功能时再请求，对用户更有上下文。

### 10. 在多个 macOS 版本上测试

权限机制在不同 macOS 版本上可能不同。建议测试：
- 最新的 macOS 版本
- 最低支持的 macOS 版本
- 你的用户群体常用的版本

---

更多 UnifyPy 配置说明，参见主 [README](README.md)。

如有问题或疑问，请访问 [GitHub 仓库](https://github.com/huangjunsen0406/UnifyPy)。

