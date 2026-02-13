# GitHub Secrets 和 Actions 操作指南

## 第一部分：配置 Secrets（密码保险箱）

### 为什么要用 Secrets？
- **安全**：密码不写在代码里，防止泄露
- **灵活**：不同环境（开发/生产）用不同配置
- **标准化**：GitHub官方推荐方式

### 操作步骤（图文）

**Step 1: 打开仓库设置**
```
1. 访问 https://github.com/realerich/marvin-backup
2. 点击顶部菜单栏的 "Settings"（设置）
3. 左侧边栏点击 "Secrets and variables" → "Actions"
```

**Step 2: 添加 Secrets**
```
4. 点击绿色按钮 "New repository secret"
5. 填写 Name 和 Value：

   Name: RDS_HOST
   Value: pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com
   
6. 点击 "Add secret"
7. 重复上述步骤，添加其余4个：

   RDS_PORT = 5432
   RDS_DB = marvin_db
   RDS_USER = marvin
   RDS_PASSWORD = Crimson@13
```

**Step 3: 验证配置**
添加完成后，页面会显示5个Secrets（值被隐藏为 ***）

---

## 第二部分：Workflow（自动化工作流）

### 什么是 Workflow？
就像定时任务，但运行在GitHub服务器上：
- 每天自动检查RDS是否正常
- 自动备份数据库
- 自动发通知（可选）

### 操作步骤

**Step 1: 创建 Workflow 文件**
```
1. 在仓库页面，点击 "Add file" → "Create new file"
2. 文件路径输入：.github/workflows/backup-verify.yml
3. 文件名前面有个点，这是隐藏目录
```

**Step 2: 粘贴以下代码**
```yaml
name: Daily Backup Verification

on:
  schedule:
    - cron: '0 4 * * *'  # 每天凌晨4点
  workflow_dispatch:  # 允许手动触发

jobs:
  backup-verify:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Install PostgreSQL client
      run: |
        sudo apt-get update
        sudo apt-get install -y postgresql-client
        
    - name: Test RDS Connection
      env:
        PGPASSWORD: ${{ secrets.RDS_PASSWORD }}
      run: |
        echo "Testing connection to RDS..."
        psql -h ${{ secrets.RDS_HOST }} -U ${{ secrets.RDS_USER }} -d ${{ secrets.RDS_DB }} -c "SELECT COUNT(*) FROM persons;"
        echo "✅ RDS连接正常"
        
    - name: Backup Database
      env:
        PGPASSWORD: ${{ secrets.RDS_PASSWORD }}
      run: |
        pg_dump -h ${{ secrets.RDS_HOST }} -U ${{ secrets.RDS_USER }} -d ${{ secrets.RDS_DB }} > marvin_backup_$(date +%Y%m%d).sql
        ls -lh marvin_backup_*.sql
        
    - name: Upload Backup
      uses: actions/upload-artifact@v4
      with:
        name: database-backup
        path: marvin_backup_*.sql
        retention-days: 7
```

**Step 3: 提交文件**
```
4. 滚动到页面底部
5. 填写提交信息："Add daily backup workflow"
6. 选择 "Commit directly to the master branch"
7. 点击 "Commit new file"
```

---

## 第三部分：验证 Workflow 运行

**Step 1: 查看 Actions 页面**
```
1. 点击仓库顶部菜单 "Actions"
2. 会看到 "Daily Backup Verification" 工作流
3. 点击它
```

**Step 2: 手动触发测试**
```
4. 点击右侧 "Run workflow" 按钮
5. 选择分支 master
6. 点击 "Run workflow"
7. 等待1-2分钟，查看运行结果
```

**成功标志：**
- 绿色 ✅ 表示成功
- 能看到 "RDS连接正常" 的输出
- 有备份文件生成

---

## 快速检查清单

配置完成后，请确认：

- [ ] 5个 Secrets 已添加（RDS_HOST, RDS_PORT, RDS_DB, RDS_USER, RDS_PASSWORD）
- [ ] Workflow 文件已创建（.github/workflows/backup-verify.yml）
- [ ] 手动触发测试成功（绿色 ✅）

---

## 常见问题

**Q: Secrets 添加后看不到值，正常吗？**
A: 正常，GitHub会隐藏为 ***，这是安全特性

**Q: Workflow 运行失败怎么办？**
A: 点击失败的运行记录，查看日志，通常是：
   - Secrets 名称拼写错误
   - RDS白名单未配置
   - 网络连接问题

**Q: 可以修改定时时间吗？**
A: 可以，修改 cron: '0 4 * * *' 
   - 4 表示凌晨4点（UTC时间）
   - 北京时间 = UTC+8，所以是中午12点
   - 如果要北京时间凌晨4点，改为 '0 20 * * *'
