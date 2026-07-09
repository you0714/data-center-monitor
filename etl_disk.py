#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据中心运行监控大屏 - ETL脚本
功能：读取disk_tsar.dat日志文件，清洗脏数据，转换时间戳，批量写入MySQL
"""

import os
import re
import pymysql
from datetime import datetime
from pymysql.cursors import DictCursor

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Yxr@20050714',
    'database': 'data_center_monitor',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def create_database_if_not_exists():
    """
    如果数据库不存在，自动创建数据库和表
    """
    try:
        # 先连接MySQL（不带数据库名）
        temp_config = DB_CONFIG.copy()
        del temp_config['database']
        
        conn = pymysql.connect(**temp_config)
        cursor = conn.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
        
        # 读取并执行SQL文件创建表
        with open('create_table.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 切换到新数据库
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # 执行SQL（需要支持多条语句）
        from pymysql.constants import CLIENT
        conn.close()
        
        # 重新连接并执行SQL
        temp_config['database'] = DB_CONFIG['database']
        temp_config['client_flag'] = CLIENT.MULTI_STATEMENTS
        conn = pymysql.connect(**temp_config)
        cursor = conn.cursor()
        cursor.execute(sql_content)
        conn.commit()
        
        cursor.close()
        conn.close()
        print("✓ 数据库和表创建成功")
        
    except Exception as e:
        print(f"创建数据库失败: {e}")
        raise

def connect_db():
    """
    建立MySQL数据库连接
    返回：数据库连接对象
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:  # Unknown database
            print("数据库不存在，正在创建...")
            create_database_if_not_exists()
            return pymysql.connect(**DB_CONFIG)
        else:
            print(f"数据库连接失败: {e}")
            raise
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise

def clean_value(value_str):
    """
    清洗指标值，去除异常字符
    参数：value_str - 原始值字符串
    返回：清洗后的浮点数值
    """
    try:
        # 移除可能的特殊字符，只保留数字和小数点
        cleaned = re.sub(r'[^\d.-]', '', value_str)
        return float(cleaned)
    except (ValueError, TypeError):
        return None

def parse_timestamp(ts_ms):
    """
    将毫秒时间戳转换为标准datetime对象
    参数：ts_ms - 毫秒时间戳字符串
    返回：datetime对象
    """
    try:
        # 转换为整数，处理可能的字符串格式
        ts_int = int(float(ts_ms.strip()))
        # 毫秒转秒
        ts_sec = ts_int // 1000
        return datetime.fromtimestamp(ts_sec)
    except (ValueError, TypeError):
        return None

def validate_record(record):
    """
    验证记录有效性
    参数：record - 记录字典
    返回：布尔值，是否有效
    """
    required_fields = ['ts', 'hostid', 'type', 'mod', 'value', 'tag']
    
    # 检查必填字段
    for field in required_fields:
        if field not in record or not record[field]:
            return False
    
    # 验证时间戳
    if parse_timestamp(record['ts']) is None:
        return False
    
    # 验证指标值
    if clean_value(record['value']) is None:
        return False
    
    # 验证主机ID格式
    if not re.match(r'^host\d{3}$', record['hostid']):
        return False
    
    return True

def read_dat_file(file_path):
    """
    读取.dat日志文件
    参数：file_path - 文件路径
    返回：数据记录列表
    """
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 获取表头
        header = lines[0].strip().split('\t')
        
        # 解析数据行
        for line_num, line in enumerate(lines[1:], start=2):
            line = line.strip()
            if not line:
                continue
            
            fields = line.split('\t')
            if len(fields) != len(header):
                print(f"第{line_num}行字段数量不匹配，跳过")
                continue
            
            record = dict(zip(header, fields))
            
            # 验证记录
            if validate_record(record):
                records.append(record)
            else:
                print(f"第{line_num}行数据无效，跳过")
        
        print(f"成功读取 {len(records)} 条有效记录")
        return records
    
    except FileNotFoundError:
        print(f"文件未找到: {file_path}")
        return []
    except Exception as e:
        print(f"读取文件失败: {e}")
        return []

def transform_data(records):
    """
    转换数据格式
    参数：records - 原始记录列表
    返回：转换后的记录列表
    """
    transformed = []
    for record in records:
        ts = parse_timestamp(record['ts'])
        value = clean_value(record['value'])
        
        transformed.append({
            'ts': ts,
            'host_id': record['hostid'],
            'type': record['type'],
            'mod': record['mod'],
            'value': value,
            'tag': record['tag']
        })
    
    print(f"完成 {len(transformed)} 条数据转换")
    return transformed

def batch_insert(conn, records, batch_size=1000):
    """
    批量插入数据到MySQL
    参数：
        conn - 数据库连接
        records - 记录列表
        batch_size - 每批次插入数量
    """
    if not records:
        print("没有数据需要插入")
        return
    
    cursor = conn.cursor()
    
    # 插入SQL语句
    insert_sql = """
        INSERT INTO disk_metrics (ts, host_id, type, `mod`, value, tag)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    
    total_count = len(records)
    inserted_count = 0
    
    try:
        # 分批插入
        for i in range(0, total_count, batch_size):
            batch = records[i:i+batch_size]
            values = [
                (r['ts'], r['host_id'], r['type'], r['mod'], r['value'], r['tag'])
                for r in batch
            ]
            
            cursor.executemany(insert_sql, values)
            conn.commit()
            
            inserted_count += len(batch)
            print(f"已插入 {inserted_count}/{total_count} 条记录")
        
        print(f"批量插入完成，共插入 {inserted_count} 条记录")
    
    except Exception as e:
        conn.rollback()
        print(f"插入数据失败: {e}")
        raise
    finally:
        cursor.close()

def main():
    """
    主函数：执行ETL流程
    """
    print("===== 数据中心监控ETL脚本启动 =====")
    
    # 1. 读取数据文件
    dat_file_path = os.path.join(os.path.dirname(__file__), 'disk_tsar.dat')
    print(f"正在读取数据文件: {dat_file_path}")
    raw_records = read_dat_file(dat_file_path)
    
    if not raw_records:
        print("没有有效数据，退出")
        return
    
    # 2. 数据转换
    print("正在转换数据格式...")
    transformed_records = transform_data(raw_records)
    
    # 3. 批量写入数据库
    print("正在写入数据库...")
    conn = connect_db()
    try:
        batch_insert(conn, transformed_records)
    finally:
        conn.close()
    
    print("===== ETL流程执行完成 =====")

if __name__ == '__main__':
    main()