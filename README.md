# 数据中心运行监控大屏

## 项目概述
![数据中心监控大屏完整界面](./assets/dashboard_full.png)

本项目基于 disk_tsar.dat 明细数据，实现数据中心运行监控大屏，包含以下组件：

1. **ETL脚本** - 读取日志、清洗数据、转换时间戳、批量写入MySQL
2. **Flask后端** - 提供5个API接口，端口5000
3. **前端可视化** - ECharts监控大屏，自适应PC+移动端

## 文件结构

```
├── disk_tsar.dat          # 原始数据文件
├── create_table.sql       # MySQL建表语句
├── etl_disk.py            # ETL脚本
├── app.py                 # Flask后端服务
├── index.html             # 前端可视化大屏
└── README.md              # 运行说明文档
```

## 运行步骤

### 1. 环境准备

确保已安装以下软件：
- Python 3.6+
- MySQL 5.7+
- 浏览器（Chrome/Firefox/Edge）

### 2. 安装依赖

```bash
# 安装Python依赖
pip install pymysql flask flask-cors
```

### 3. 创建数据库和表

```bash
# 登录MySQL
mysql -u root -p

# 执行建表语句
source /path/to/create_table.sql
```

### 4. 配置数据库连接

修改以下文件中的数据库配置：

**etl_disk.py** 和 **app.py** 中的 `DB_CONFIG`：
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # 修改为你的MySQL密码
    'database': 'data_center_monitor',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}
```

### 5. 运行ETL脚本

```bash
cd /path/to/project
python etl_disk.py
```

### 6. 启动后端服务

```bash
cd /path/to/project
python app.py
```

服务启动后访问地址：http://localhost:5000

### 7. 打开前端大屏

使用浏览器打开 `index.html` 文件，或通过HTTP服务器访问：

```bash
# 使用Python启动简易HTTP服务器（可选）
cd /path/to/project
python -m http.server 8080
```

然后访问：http://localhost:8080/index.html

## API接口列表

| 接口地址 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/api/hosts` | GET | 获取主机列表 |
| `/api/disk/top10` | GET | 获取磁盘使用率TOP10 |
| `/api/disk/latency_trend` | GET | 获取磁盘延迟趋势 |
| `/api/disk/rw_total` | GET | 获取读写扇区总量 |
| `/api/disk/host/<host_id>` | GET | 查询单主机指标 |
| `/api/disk/summary` | GET | 获取汇总统计 |

## Git仓库提交命令

```bash
# 初始化仓库
git init

# 添加文件
git add .

# 提交
git commit -m "feat: 数据中心运行监控大屏完成"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/yourusername/data-center-monitor.git

# 推送
git push -u origin main
```

## 作业提交说明

### 提交内容

1. **代码文件**：
   - `etl_disk.py` - ETL脚本
   - `app.py` - Flask后端服务
   - `index.html` - 前端可视化大屏
   - `create_table.sql` - MySQL建表语句

2. **文档**：
   - `README.md` - 运行说明

### 运行截图

建议提交以下截图：
- 前端大屏整体展示
- 各图表数据展示
- API接口测试结果

## 技术栈

- **后端**: Python 3 + Flask 2.x
- **数据库**: MySQL 5.7+
- **前端**: HTML5 + ECharts 5.x
- **ETL**: Python + pymysql

## 功能特性

1. **数据清洗** - 自动处理脏数据，毫秒时间戳转换
2. **批量写入** - 高效批量插入MySQL
3. **实时监控** - 前端每30秒自动刷新
4. **响应式设计** - 自适应PC和移动端
5. **可视化图表** - 柱状图、折线图、饼图

## 注意事项

1. 确保MySQL服务正常运行
2. 修改数据库密码配置
3. 前端需要网络访问ECharts CDN
4. ETL脚本首次运行可能需要较长时间，具体取决于数据量