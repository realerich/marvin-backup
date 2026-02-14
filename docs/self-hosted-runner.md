# 🏃 自托管 GitHub Actions Runner 配置指南

## 快速开始

### 1. 在 GitHub 上注册 Runner

访问: https://github.com/realerich/marvin-backup/settings/actions/runners

点击 "New self-hosted runner"，选择 Linux -> x64，获取配置 token。

### 2. 服务器端安装

```bash
# 创建目录
mkdir -p /opt/github-runner && cd /opt/github-runner

# 下载最新 runner (替换为最新版本)
RUNNER_VERSION="2.311.0"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 解压
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 安装依赖
sudo ./bin/installdependencies.sh

# 配置 runner (替换 <TOKEN> 为从 GitHub 获取的 token)
./config.sh --url https://github.com/realerich/marvin-backup --token <TOKEN> --name "marvin-runner" --labels "self-hosted,marvin"

# 安装为系统服务
sudo ./svc.sh install
sudo ./svc.sh start
```

### 3. 配置为 Docker 运行 (可选)

```bash
# 使用官方 Docker 镜像
docker run -d \
  --name github-runner \
  -e REPO_URL="https://github.com/realerich/marvin-backup" \
  -e RUNNER_TOKEN="<TOKEN>" \
  -e RUNNER_NAME="docker-runner" \
  -e LABELS="docker,self-hosted" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  myoung34/github-runner:latest
```

### 4. 工作流中使用自托管 Runner

```yaml
jobs:
  deploy:
    runs-on: self-hosted  # 使用自托管 runner
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to local server
        run: |
          # 这里可以执行服务器本地命令
          echo "Running on $(hostname)"
```

## 安全建议

1. **隔离环境**: 在隔离的容器或 VM 中运行
2. **最小权限**: Runner 使用专用低权限用户
3. **定期更新**: 及时更新 runner 版本
4. **监控日志**: 定期检查 runner 日志

## 故障排除

```bash
# 查看 runner 状态
sudo systemctl status actions.runner.realerich-marvin-backup.*

# 查看日志
journalctl -u actions.runner.realerich-marvin-backup.* -f

# 重新配置
./config.sh remove
./config.sh --url https://github.com/realerich/marvin-backup --token <TOKEN>
```
