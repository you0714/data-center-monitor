-- 数据中心运行监控数据库
-- 创建监控库
CREATE DATABASE IF NOT EXISTS `data_center_monitor` 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `data_center_monitor`;

-- 主机信息字典表
-- 存储主机基础信息，便于关联和查询
CREATE TABLE IF NOT EXISTS `host_info` (
    `host_id` VARCHAR(50) NOT NULL COMMENT '主机唯一标识',
    `host_name` VARCHAR(100) DEFAULT NULL COMMENT '主机名称',
    `ip_address` VARCHAR(50) DEFAULT NULL COMMENT '主机IP地址',
    `status` ENUM('online', 'offline', 'maintenance') DEFAULT 'online' COMMENT '主机状态',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    PRIMARY KEY (`host_id`),
    INDEX `idx_host_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='主机信息字典表';

-- 磁盘指标主表
-- 存储磁盘监控的详细指标数据
CREATE TABLE IF NOT EXISTS `disk_metrics` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `ts` DATETIME NOT NULL COMMENT '采集时间（标准日期时间格式）',
    `host_id` VARCHAR(50) NOT NULL COMMENT '主机ID，关联host_info表',
    `type` VARCHAR(20) NOT NULL COMMENT '指标类型（disk）',
    `mod` VARCHAR(50) NOT NULL COMMENT '磁盘模块名称（如sda_write, sda_util）',
    `value` DECIMAL(15,4) NOT NULL COMMENT '指标数值',
    `tag` VARCHAR(50) NOT NULL COMMENT '指标分类标签',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    PRIMARY KEY (`id`),
    INDEX `idx_ts` (`ts`),
    INDEX `idx_host_id` (`host_id`),
    INDEX `idx_mod` (`mod`),
    INDEX `idx_tag` (`tag`),
    INDEX `idx_host_ts` (`host_id`, `ts`),
    CONSTRAINT `fk_disk_host` FOREIGN KEY (`host_id`) REFERENCES `host_info`(`host_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='磁盘指标主表';

-- 初始化主机数据
-- 根据数据文件中提取的主机列表进行初始化
INSERT IGNORE INTO `host_info` (`host_id`, `host_name`) VALUES
('host001', '主机001'),
('host002', '主机002'),
('host003', '主机003'),
('host004', '主机004'),
('host005', '主机005'),
('host006', '主机006'),
('host007', '主机007'),
('host008', '主机008'),
('host009', '主机009'),
('host010', '主机010'),
('host011', '主机011'),
('host012', '主机012'),
('host013', '主机013'),
('host014', '主机014'),
('host015', '主机015'),
('host016', '主机016'),
('host017', '主机017'),
('host018', '主机018'),
('host019', '主机019'),
('host020', '主机020');