# 使用官方 Node.js 镜像作为构建阶段的基础镜像
FROM node:20-alpine as build-stage

WORKDIR /app

# 复制 package.json 和 package-lock.json (如果存在)
COPY package*.json ./

# 安装依赖
RUN npm install --verbose

# 复制前端项目文件
COPY . .

# 构建前端应用
RUN npm run build

# 使用 Nginx 作为生产环境的服务阶段
FROM nginx:stable-alpine AS production-stage

# 复制 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建好的静态文件到 Nginx 默认的静态文件目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露 Nginx 默认端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
