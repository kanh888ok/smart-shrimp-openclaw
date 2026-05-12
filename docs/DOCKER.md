# 🐳 Docker 部署指南

## 📋 前置要求

### **1. 安装 Docker**

**Windows / macOS**:
- 下载 [Docker Desktop](https://www.docker.com/products/docker-desktop)
- 安装并启动 Docker Desktop

**Linux**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### **2. 验证安装**
```bash
docker --version
docker-compose --version
```

---

## 🚀 快速开始

### **方式一：使用启动脚本（推荐）**

**Windows**:
```cmd
docker-start.bat
```

**Linux / macOS**:
```bash
chmod +x docker-start.sh
./docker-start.sh
```

### **方式二：手动启动**

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

---

## 📊 访问服务

启动成功后，在浏览器中访问：

**Dashboard**: http://localhost:8501

---

## 📝 常用命令

### **服务管理**

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务的日志
docker-compose logs -f dashboard
```

### **数据管理**

```bash
# 进入容器
docker-compose exec dashboard bash

# 生成示例数据
docker-compose exec dashboard python generate_sample_data.py

# 运行完整分析
docker-compose exec dashboard python run.py

# 查看数据文件
docker-compose exec dashboard ls -lh data/
```

### **容器管理**

```bash
# 查看运行的容器
docker ps

# 停止容器
docker stop shrimp-farming-dashboard

# 删除容器
docker rm shrimp-farming-dashboard

# 删除镜像
docker rmi shrimp-farming-dashboard
```

---

## 🔧 高级用法

### **1. 自定义端口**

修改 `docker-compose.yml`:
```yaml
services:
  dashboard:
    ports:
      - "8080:8501"  # 使用 8080 端口
```

### **2. 持久化数据**

数据已通过 volumes 挂载到本地：
- `./data` → 容器内 `/app/data`
- `./reports` → 容器内 `/app/reports`
- `./logs` → 容器内 `/app/logs`

### **3. 环境变量**

在 `docker-compose.yml` 中添加：
```yaml
services:
  dashboard:
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### **4. 资源限制**

```yaml
services:
  dashboard:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

## 🐛 故障排查

### **1. 端口被占用**

```bash
# 查看端口占用
netstat -ano | findstr :8501  # Windows
lsof -i :8501                 # Linux/macOS

# 更改端口
# 编辑 docker-compose.yml，修改 ports 配置
```

### **2. 容器启动失败**

```bash
# 查看详细日志
docker-compose logs dashboard

# 检查容器状态
docker-compose ps

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

### **3. 数据文件找不到**

```bash
# 确保数据文件在 data/ 目录下
ls -la data/

# 进入容器检查
docker-compose exec dashboard ls -la /app/data/
```

### **4. 中文显示问题**

Docker 镜像已包含中文字体，如果仍有问题：

```bash
# 进入容器安装字体
docker-compose exec dashboard apt-get update
docker-compose exec dashboard apt-get install -y fonts-wqy-microhei
```

---

## 🌐 部署到云端

### **Docker Hub**

```bash
# 构建镜像
docker build -t your-username/shrimp-farming:latest .

# 登录 Docker Hub
docker login

# 推送镜像
docker push your-username/shrimp-farming:latest
```

### **阿里云容器镜像服务**

```bash
# 登录阿里云
docker login --username=your-username registry.cn-hangzhou.aliyuncs.com

# 标记镜像
docker tag shrimp-farming:latest registry.cn-hangzhou.aliyuncs.com/your-namespace/shrimp-farming:latest

# 推送镜像
docker push registry.cn-hangzhou.aliyuncs.com/your-namespace/shrimp-farming:latest
```

### **云服务器部署**

```bash
# 1. 克隆代码
git clone your-repo-url
cd 源代码

# 2. 启动服务
docker-compose up -d

# 3. 配置反向代理（Nginx）
# 参考下面的 Nginx 配置
```

### **Nginx 反向代理配置**

```nginx
# /etc/nginx/sites-available/shrimp-farming
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📦 导出和导入

### **导出镜像**

```bash
# 导出为 tar 文件
docker save shrimp-farming-dashboard:latest -o shrimp-farming.tar

# 压缩
gzip shrimp-farming.tar
```

### **导入镜像**

```bash
# 解压
gunzip shrimp-farming.tar.gz

# 导入
docker load -i shrimp-farming.tar
```

---

## 🔐 安全建议

1. **不要在镜像中包含敏感数据**
   - 使用 `.dockerignore` 排除敏感文件
   - 数据文件通过 volumes 挂载

2. **限制容器权限**
   - 不要使用 root 用户运行
   - 在 Dockerfile 中添加 `USER` 指令

3. **定期更新**
   - 及时更新基础镜像
   - 更新依赖包

4. **使用非测试端口**
   - 生产环境不要使用默认端口
   - 使用防火墙限制访问

---

## 📚 参考资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Streamlit 部署指南](https://docs.streamlit.io/deploy)

---

## 💡 提示

- 首次构建可能需要 5-10 分钟
- 确保至少有 2GB 可用内存
- 生产环境建议使用云服务器（至少 2核4G）

---

**SmartShrimp Team**
**最后更新：2026-03-17**
