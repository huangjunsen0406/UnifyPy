# macOS应用打包指南

本文档提供在macOS平台上打包Python应用程序的详细指南，包括打包过程、注意事项以及常见问题的解决方案。

## 目录

- [环境准备](#环境准备)
- [基本打包流程](#基本打包流程)
- [签名与公证](#签名与公证)
- [无开发者证书的解决方案](#无开发者证书的解决方案)
- [配置示例](#配置示例)
- [常见问题](#常见问题)

## 环境准备

在macOS上打包Python应用，需要准备以下环境：

1. **Python环境**：
   - 建议使用Python 3.7+
   - 使用虚拟环境隔离项目依赖：`python -m venv venv`

2. **PyInstaller**：
   ```bash
   pip install pyinstaller>=6.1.0
   ```

3. **create-dmg**（用于创建DMG安装镜像）：
   ```bash
   brew install create-dmg
   ```

4. **其他依赖**：
   - Xcode命令行工具：`xcode-select --install`
   - 如需签名：Apple开发者证书

## 基本打包流程

### 1. 使用配置文件

创建`build.json`配置文件：

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "entry": "main.py",
  "hooks": "hooks",
  "platform_specific": {
    "macos": {
      "additional_pyinstaller_args": "--windowed --add-data assets:assets --add-data models:models",
      "app_bundle_name": "我的应用.app",
      "bundle_identifier": "com.example.myapp",
      "sign_bundle": false,
      "create_dmg": true
    }
  }
}
```

### 2. 执行打包命令

```bash
python3 main.py 项目路径 --config build.json
```

### 3. 输出文件

成功打包后，将在以下位置生成文件：

- 应用程序包：`项目路径/dist/我的应用.app`
- DMG镜像文件：`项目路径/installer/我的应用-1.0.0.dmg`

## 签名与公证

在macOS上分发应用程序，最好经过签名和公证，以避免安全警告。

### 应用签名

1. **获取开发者证书**：
   - 加入Apple开发者计划（付费）
   - 在苹果开发者网站创建证书

2. **配置签名选项**：
   ```json
   "macos": {
     "sign_bundle": true,
     "identity": "Developer ID Application: 你的名称 (Team ID)"
   }
   ```

3. **公证应用**：
   完成打包后，使用以下命令提交公证：
   ```bash
   xcrun altool --notarize-app --primary-bundle-id "com.example.myapp" --username "你的AppleID" --password "app-specific-password" --file "应用路径.dmg"
   ```

4. **检查公证状态**：
   ```bash
   xcrun altool --notarization-info [UUID] --username "你的AppleID" --password "app-specific-password"
   ```

5. **给DMG添加公证标记**：
   ```bash
   xcrun stapler staple "应用路径.dmg"
   ```

## 无开发者证书的解决方案

如果没有Apple开发者证书，但需要分发应用给他人测试，可以采用以下方法：

### 1. 使用自签名证书

1. 打开"钥匙串访问"
2. 选择菜单：钥匙串访问 > 证书助理 > 创建证书
3. 输入证书名称（如"TestCert"）
4. 身份类型选择"自签名根证书"
5. 证书类型选择"代码签名"
6. 完成创建后在配置中使用：
   ```json
   "identity": "TestCert"
   ```

### 2. 跳过签名步骤

在配置中设置：
```json
"sign_bundle": false
```

此方法打包的应用会触发macOS的安全警告，用户需要：
1. 右键点击应用 > 打开（不要双击）
2. 在弹出的对话框中选择"打开"

### 3. 使用ZIP替代DMG

如果DMG镜像文件在分发时遇到问题，可以将应用程序包直接压缩为ZIP文件：

```bash
# 创建ZIP文件
ditto -c -k --keepParent "dist/我的应用.app" "installer/我的应用.zip"
```

在配置中设置：
```json
"create_dmg": false,
"create_zip": true
```

### 4. 为用户提供安装说明

为测试用户提供以下指南：

```
macOS安全限制解决方法：

方法一（推荐）：
1. 右键点击应用而不是双击
2. 从菜单中选择"打开"
3. 点击"打开"按钮

方法二（临时关闭安全限制）：
1. 打开系统偏好设置 > 安全性与隐私
2. 点击"通用"选项卡
3. 点击左下角的锁图标并输入密码
4. 选择"任何来源"（或点击"仍要打开"）

方法三（使用终端）：
1. 打开终端
2. 运行命令：xattr -d com.apple.quarantine /Applications/应用名称.app
```

## 配置示例

### 基本配置（无签名）

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "entry": "main.py",
  "platform_specific": {
    "macos": {
      "additional_pyinstaller_args": "--windowed --add-data assets:assets",
      "sign_bundle": false,
      "create_dmg": true
    }
  }
}
```

### 带签名配置

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "entry": "main.py",
  "platform_specific": {
    "macos": {
      "additional_pyinstaller_args": "--windowed --add-data assets:assets",
      "app_bundle_name": "我的应用.app",
      "bundle_identifier": "com.example.myapp",
      "sign_bundle": true,
      "identity": "Developer ID Application: 你的名称 (XXXXXXXXXX)",
      "entitlements": "path/to/entitlements.plist",
      "create_dmg": true
    }
  }
}
```

## 常见问题

### 1. 应用打开时出现"无法验证开发者"警告

**解决方案**：
- 右键点击应用，选择"打开"
- 第一次会提示警告，选择"打开"即可
- 第二次启动将不再提示

### 2. 应用无法找到资源文件

**解决方案**：
- 确保在PyInstaller命令中正确指定了--add-data参数
- macOS中使用冒号(:)作为路径分隔符，而不是分号(;)
- 示例：`--add-data assets:assets`

### 3. "macOS无法验证此应用不包含恶意软件"警告

**解决方案**：
- 需要进行代码签名和公证
- 或者用户可使用命令：`xattr -d com.apple.quarantine /Applications/应用名称.app`

### 4. 依赖库问题（dylib无法加载）

**解决方案**：
- 确保使用PyInstaller的--collect-all参数收集所有依赖
- 例如：`--collect-all numpy`
- 或使用hook脚本正确处理动态库依赖

### 5. macOS版本兼容性问题

**解决方案**：
- 在与目标macOS版本相同或更低的系统上构建
- 使用PyInstaller的--target-architecture参数指定目标架构
- 例如：`--target-architecture x86_64` 或 `--target-architecture universal2` 