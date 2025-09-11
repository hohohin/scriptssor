# Chrome Web Store 上传指南

## 准备工作

### 1. Chrome 开发者账户注册
- 访问 [Chrome Web Store 开发者控制台](https://chrome.google.com/webstore/devconsole/)
- 支付一次性注册费 $5.00
- 完成开发者协议

### 2. 扩展文件准备
所有必需文件已准备在 `browser-extension-store/` 目录中：

```
browser-extension-store/
├── manifest.json          # 扩展清单
├── popup.html            # 弹窗界面
├── popup.js              # 弹窗逻辑
├── background.js         # 后台服务
├── content-script.js     # 内容脚本
├── content-script.css    # 内容样式
├── welcome.html          # 欢迎页面
└── icons/                # 图标文件夹
    ├── icon16.svg
    ├── icon32.svg
    ├── icon48.svg
    └── icon128.svg
```

## 上传步骤

### 步骤 1: 打包扩展
1. 访问 [Chrome 扩展打包工具](chrome://extensions/)
2. 开启"开发者模式"
3. 点击"打包扩展程序"
4. 选择 `browser-extension-store` 文件夹作为扩展根目录
5. 选择私钥文件（可选，首次打包会自动生成）
6. 点击"打包扩展程序"

### 步骤 2: 上传到 Chrome Web Store
1. 登录 [Chrome Web Store 开发者控制台](https://chrome.google.com/webstore/devconsole/)
2. 点击"新建商品"
3. 上传生成的 `.crx` 文件或选择"上传 ZIP 文件"
4. 填写商品信息：

#### 商店信息
- **商品名称**: ScriptSor Audio Converter
- **商品描述**: Convert video files to WAV format locally before uploading to ScriptSor video editor
- **详细描述**: 
  ```
  ScriptSor Audio Converter is a powerful Chrome extension that allows you to convert video files to WAV format locally in your browser before uploading to ScriptSor. This reduces upload time by 90% and protects your privacy by keeping video files on your computer.
  
  Key Features:
  • Local video-to-audio conversion using Web Audio API
  • Support for all major video formats (MP4, AVI, MOV, MKV, etc.)
  • Privacy-first approach - videos never leave your computer
  • Seamless integration with ScriptSor web app
  • Drag-and-drop interface with progress tracking
  • Automatic upload to ScriptSor after conversion
  
  Perfect for content creators, video editors, and anyone who wants to save time and bandwidth when working with ScriptSor video editing platform.
  ```

- **类别**: 生产工具 > 其他工具
- **语言**: English

#### 图标和截图
- **图标**: 使用 `icons/icon128.svg`
- **截图**: 准备以下截图：
  - 1280x800 - 主界面截图
  - 1280x800 - 转换过程截图
  - 1280x800 - 完成状态截图

#### 隐私政策
```
Privacy Policy for ScriptSor Audio Converter

Last Updated: [Current Date]

Information Collection:
This extension does not collect any personal information or user data. All video processing is done locally in the user's browser.

Data Usage:
- Video files are processed locally and never sent to external servers
- No telemetry or analytics data is collected
- No user tracking or monitoring

Permissions Used:
- activeTab: To interact with the current tab
- scripting: To inject content scripts
- storage: To save user preferences
- downloads: To enable file download functionality
- host permissions: To communicate with ScriptSor servers

Contact:
For privacy concerns, contact: [Your Email Address]
```

### 步骤 3: 提交审核
1. 完成所有必填字段
2. 上传至少一张截图
3. 同意开发者协议
4. 点击"提交审核"

### 步骤 4: 等待审核
- 审核通常需要 3-7 个工作日
- 审核期间扩展处于"待审核"状态
- 如有问题，Google 会发送邮件通知

## 审核通过后

### 1. 获取扩展 URL
- 审核通过后，扩展会获得唯一的 Chrome Web Store URL
- 格式: `https://chrome.google.com/webstore/detail/scriptsor-audio-converter/[extension-id]`

### 2. 更新前端链接
修改 `frontend/scriptCut/src/App.jsx` 中的链接：

```javascript
// 将这行：
window.open('/browser-extension/install.html', '_blank');

// 改为：
window.open('https://chrome.google.com/webstore/detail/scriptsor-audio-converter/[extension-id]', '_blank');
```

### 3. 推广扩展
- 在网站上添加 Chrome Web Store 徽章
- 在社交媒体上分享扩展链接
- 收集用户反馈和评价

## 维护和更新

### 更新扩展
1. 修改扩展代码
2. 更新 `manifest.json` 中的版本号
3. 重新打包扩展
4. 在开发者控制台上传新版本
5. 提交审核

### 错误修复
- 监控用户反馈
- 及时修复 bug
- 快速发布安全更新

## 注意事项

### Chrome Web Store 政策
- 遵守 Chrome 扩展开发政策
- 不包含恶意代码或隐私侵犯行为
- 提供准确的扩展描述和功能说明

### 用户隐私
- 明确说明数据收集和使用方式
- 提供隐私政策链接
- 最小化权限请求

### 技术要求
- 扩展必须功能完整
- 提供良好的用户体验
- 适配最新的 Chrome 版本

## 联系支持

如果在上传过程中遇到问题：
1. 查看开发者控制台的帮助文档
2. 检查扩展是否符合所有政策要求
3. 联系 Chrome Web Store 支持团队

## 成功标志

✅ 扩展成功上传到 Chrome Web Store  
✅ 用户可以直接从商店安装扩展  
✅ 扩展在商店中可见且可搜索  
✅ 用户评价和下载量稳步增长  
✅ 前端链接正确指向商店页面