#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据中心运行监控大屏 - Flask后端服务
提供主机列表、磁盘使用率TOP10、磁盘延迟趋势、读写扇区总量、单主机指标查询等API
"""

# 修正：统一在头部导入所有flask工具
from flask import Flask, jsonify, render_template
from flask_cors import CORS
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)
CORS(app)  # 允许跨域访问

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Yxr@20050714',
    'database': 'data_center_monitor',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def get_db_connection():
    """
    获取数据库连接
    """
    return pymysql.connect(**DB_CONFIG)

# 首页路由移到所有接口外面，正常注册
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/hosts', methods=['GET'])
def get_host_list():
    """
    API: 获取主机列表
    返回所有主机的基本信息
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "SELECT host_id, host_name, ip_address, status FROM host_info ORDER BY host_id"
        cursor.execute(sql)
        hosts = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': hosts
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取主机列表失败: {str(e)}',
            'data': []
        })

@app.route('/api/disk/top10', methods=['GET'])
def get_disk_util_top10():
    """
    API: 获取磁盘使用率TOP10
    返回使用率最高的前10个磁盘
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询最新的磁盘使用率数据，取TOP10，mod加反引号
        sql = """
            SELECT host_id, `mod`, value, ts 
            FROM disk_metrics 
            WHERE tag = 'disk_util_percent' 
            ORDER BY ts DESC, value DESC 
            LIMIT 10
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取磁盘使用率TOP10失败: {str(e)}',
            'data': []
        })

@app.route('/api/disk/latency_trend', methods=['GET'])
def get_disk_latency_trend():
    """
    API: 获取磁盘延迟趋势
    返回最近一段时间的平均延迟数据，按时间分组
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询延迟指标，mod全部加反引号
        sql = """
            SELECT 
                DATE_FORMAT(ts, '%Y-%m-%d %H:%i') as time,
                AVG(CASE WHEN `mod` LIKE '%await' THEN value ELSE NULL END) as avg_await,
                AVG(CASE WHEN `mod` LIKE '%svctm' THEN value ELSE NULL END) as avg_svctm
            FROM disk_metrics 
            WHERE tag = 'disk_latency_ms' 
            GROUP BY DATE_FORMAT(ts, '%Y-%m-%d %H:%i')
            ORDER BY time DESC
            LIMIT 60
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取磁盘延迟趋势失败: {str(e)}',
            'data': []
        })

@app.route('/api/disk/rw_total', methods=['GET'])
def get_disk_rw_total():
    """
    API: 获取读写扇区总量
    返回各主机的读写扇区统计
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 统计各主机读写扇区总量，mod加反引号
        sql = """
            SELECT 
                host_id,
                SUM(CASE WHEN `mod` LIKE '%read' THEN value ELSE 0 END) as read_total,
                SUM(CASE WHEN `mod` LIKE '%write' THEN value ELSE 0 END) as write_total
            FROM disk_metrics 
            WHERE tag = 'disk_rw_sectors' 
            GROUP BY host_id
            ORDER BY (read_total + write_total) DESC
        """
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取读写扇区总量失败: {str(e)}',
            'data': []
        })

@app.route('/api/disk/host/<host_id>', methods=['GET'])
def get_host_metrics(host_id):
    """
    API: 获取单主机磁盘指标
    参数：host_id - 主机ID
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 查询指定主机的所有磁盘指标，mod加反引号
        sql = """
            SELECT ts, `mod`, value, tag 
            FROM disk_metrics 
            WHERE host_id = %s 
            ORDER BY ts DESC, `mod`
            LIMIT 100
        """
        cursor.execute(sql, (host_id,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': results
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取主机{host_id}指标失败: {str(e)}',
            'data': []
        })

@app.route('/api/disk/summary', methods=['GET'])
def get_disk_summary():
    """
    API: 获取磁盘指标汇总统计
    返回总体统计信息用于顶部卡片展示
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取主机数量
        cursor.execute("SELECT COUNT(*) as host_count FROM host_info")
        host_count = cursor.fetchone()['host_count']
        
        # 获取磁盘指标总数
        cursor.execute("SELECT COUNT(*) as metric_count FROM disk_metrics")
        metric_count = cursor.fetchone()['metric_count']
        
        # 获取平均磁盘使用率
        cursor.execute("SELECT AVG(value) as avg_util FROM disk_metrics WHERE tag = 'disk_util_percent'")
        avg_util = cursor.fetchone()['avg_util'] or 0
        
        # 获取平均延迟
        cursor.execute("SELECT AVG(value) as avg_latency FROM disk_metrics WHERE tag = 'disk_latency_ms'")
        avg_latency = cursor.fetchone()['avg_latency'] or 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'host_count': host_count,
                'metric_count': metric_count,
                'avg_util': round(float(avg_util), 2),
                'avg_latency': round(float(avg_latency), 2)
            }
        })
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取汇总统计失败: {str(e)}',
            'data': {}
        })

if __name__ == '__main__':
    print("===== Flask后端服务启动 =====")
    print("服务端口: 5000")
    print("API接口:")
    print("  - GET /api/hosts          # 主机列表")
    print("  - GET /api/disk/top10     # 磁盘使用率TOP10")
    print("  - GET /api/disk/latency_trend  # 磁盘延迟趋势")
    print("  - GET /api/disk/rw_total  # 读写扇区总量")
    print("  - GET /api/disk/host/<host_id> # 单主机指标查询")
    print("  - GET /api/disk/summary   # 汇总统计")
    print("  - GET /                   # 监控大屏首页")
    app.run(host='0.0.0.0', port=5000, debug=True)