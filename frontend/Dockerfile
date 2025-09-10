# 构建阶段
FROM node:18-alpine AS build

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY scriptCut ./scriptCut

# 构建应用
WORKDIR /app/scriptCut
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建文件到nginx目录
COPY --from=build /app/scriptCut/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 10001

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]