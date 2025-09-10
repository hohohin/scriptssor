# Scriptssor 部署指南

## 项目概述

Scriptssor 是一个文本驱动的视频编辑工具，采用前后端分离架构：
- **后端**: Python FastAPI + 腾讯云语音识别（部署在 Render）
- **前端**: React + Vite（静态部署）

## 部署前准备

### 1. 环境变量配置

在 Render 控制台中设置以下环境变量：

#### 后端服务 (scriptssor-backend)
```bash
# 腾讯云语音识别配置
TENCENT_SECRET_ID=your_tencent_secret_id
TENCENT_SECRET_KEY=your_tencent_secret_key

# 应用配置
PORT=10000
ENVIRONMENT=production
```

#### 前端服务 (scriptssor-frontend)
```bash
# API地址配置
VITE_API_BASE_URL=https://scriptssor.onrender.com
PORT=10001
```

### 2. 腾讯云语音识别服务

1. 注册腾讯云账号
2. 开通语音识别服务
3. 创建子用户并获取 `SecretId` 和 `SecretKey`
4. 确保账户余额充足

## 部署步骤

### 第一步：部署后端到 Render

#### 方法一：使用 Render Blueprint（推荐）

1. **推送代码到 GitHub**
   ```bash
   git add .
   git commit -m "Update deployment configuration"
   git push origin main
   ```

2. **在 Render 控制台创建服务**
   - 登录 [Render 控制台](https://dashboard.render.com/)
   - 点击 "New +" → "Blueprint"
   - 连接你的 GitHub 仓库
   - Render 会自动检测 `render.yaml` 文件

3. **配置环境变量**
   - 在服务设置中添加环境变量
   - 设置磁盘存储（10GB 用于临时文件）

#### 方法二：手动创建服务

1. **创建 Web Service**
   - 类型：Web Service
   - 环境：Docker
   - 仓库：https://github.com/hohohin/scriptssor.git
   - Docker Context: `.`
   - Dockerfile: `Dockerfile`

2. **配置环境变量**
   ```bash
   PORT=10000
   TENCENT_SECRET_ID=your_secret_id
   TENCENT_SECRET_KEY=your_secret_key
   ```

3. **配置磁盘**
   - 挂载路径：`/app/temp`
   - 大小：10GB

### 第二步：构建和部署前端

#### 方法一：GitHub Pages（推荐）

1. **构建前端**
   ```bash
   ./build-frontend.sh
   ```

2. **部署到 GitHub Pages**
   ```bash
   ./deploy-gh-pages.sh
   ```

3. **配置 GitHub Pages**
   - 进入仓库设置 → Pages
   - Source 选择 "gh-pages branch"
   - 等待几分钟后访问：https://hohohin.github.io/scriptssor/

#### 方法二：其他静态托管服务

**Netlify**
```bash
# 构建前端
./build-frontend.sh

# 拖拽 dist 文件夹到 Netlify
# 或连接 GitHub 仓库自动部署
```

**Vercel**
```bash
# 构建前端
./build-frontend.sh

# 部署到 Vercel
vercel --prod dist/
```

## 服务配置

### 后端服务配置（Render）
- **端口**: 10000
- **健康检查**: `/`
- **磁盘存储**: 10GB (用于临时文件和导出)
- **实例类型**: Standard (推荐)

### 前端配置（静态托管）
- **构建输出**: `dist/` 目录
- **API地址**: 自动配置为后端Render地址

## 访问应用

部署完成后，你可以通过以下地址访问：

- **前端应用**: 
  - GitHub Pages: https://hohohin.github.io/scriptssor/
  - Netlify/Vercel: 根据你的配置
- **后端API**: https://scriptssor.onrender.com
- **API文档**: https://scriptssor.onrender.com/docs

## 监控和日志

1. **监控服务状态**
   - 在 Render 控制台查看服务状态
   - 检查 CPU、内存使用情况

2. **查看日志**
   - 使用 Render 的日志功能
   - 实时查看应用日志

3. **错误处理**
   - 设置错误告警
   - 监控磁盘使用情况

## 故障排除

### 常见问题

1. **后端服务无法启动**
   - 检查环境变量是否正确设置
   - 查看构建日志确认依赖安装成功
   - 确认腾讯云凭证有效

2. **前端无法连接后端**
   - 检查 `VITE_API_BASE_URL` 配置
   - 确认 CORS 设置正确
   - 验证后端服务运行正常

3. **文件上传失败**
   - 检查磁盘空间是否充足
   - 确认文件大小限制
   - 查看上传目录权限

4. **语音识别失败**
   - 验证腾讯云账户余额
   - 检查 API 凭证
   - 确认网络连接正常

### 调试命令

```bash
# 查看服务状态
curl https://scriptssor.onrender.com/

# 查看 API 文档
curl https://scriptssor.onrender.com/docs

# 测试文件上传
curl -X POST https://scriptssor.onrender.com/upload \
  -F "file=@test.mp4"
```

## 成本优化

### 后端成本（Render）
1. **使用免费套餐**
   - Render 提供免费套餐，适合开发测试
   - 免费额度：512MB RAM， 512MB 存储

2. **自动扩展**
   - 根据访问量配置自动扩展
   - 设置最小实例数量为 0

3. **磁盘清理**
   - 定期清理临时文件
   - 设置文件过期时间

### 前端成本（静态托管）
1. **GitHub Pages**
   - 完全免费
   - 无限流量
   - 自动HTTPS

2. **Netlify**
   - 免费套餐：100GB/月
   - 自动部署和CDN
   - 表单功能

3. **Vercel**
   - 免费套餐：100GB/月
   - 边缘函数
   - 自动HTTPS

## 部署脚本说明

### 自动化脚本

1. **`build-frontend.sh`**
   - 构建生产版本前端
   - 自动设置生产环境API地址
   - 输出到 `dist/` 目录

2. **`deploy-gh-pages.sh`**
   - 自动部署到 GitHub Pages
   - 创建 gh-pages 分支
   - 配置 .nojekyll 文件

### 使用示例

```bash
# 1. 构建前端
./build-frontend.sh

# 2. 部署到 GitHub Pages
./deploy-gh-pages.sh

# 3. 或手动部署到其他平台
# 将 dist/ 目录内容上传到你的静态托管服务
```

## 安全考虑

1. **环境变量**
   - 不要在代码中硬编码敏感信息
   - 使用 Render 的环境变量功能

2. **API 安全**
   - 实现速率限制
   - 使用 HTTPS
   - 验证输入数据

3. **文件安全**
   - 限制文件上传类型
   - 扫描上传文件
   - 设置文件大小限制

## 更新部署

1. **代码更新**
   ```bash
   git add .
   git commit -m "Update application"
   git push origin main
   ```

2. **自动部署**
   - Render 会自动检测 GitHub 更新
   - 自动重新构建和部署

3. **回滚**
   - 在 Render 控制台选择部署版本
   - 一键回滚到之前版本

## 支持

如果遇到问题，请查看：
1. Render 官方文档：https://render.com/docs
2. FastAPI 文档：https://fastapi.tiangolo.com/
3. 项目 GitHub Issues：https://github.com/hohohin/scriptssor/issues