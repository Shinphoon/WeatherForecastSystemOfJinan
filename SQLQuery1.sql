
USE 济南天气;
GO

--1.用户表 user 用户登录注册
IF OBJECT_ID(N'user', N'U') IS NOT NULL
DROP TABLE sys_user;
GO
CREATE TABLE sys_user(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    nickname VARCHAR(50) NULL,
    phone VARCHAR(20) NULL UNIQUE,
    avatar VARCHAR(255) NULL,
    last_lng DECIMAL(10,6) NULL,
    last_lat DECIMAL(10,6) NULL,
    last_address VARCHAR(200) NULL,
    push_enable TINYINT NOT NULL DEFAULT 1,
    status TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT GETDATE(),
    update_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

-- 2.验证码表 verify_code
IF OBJECT_ID(N'verify_code', N'U') IS NOT NULL
DROP TABLE verify_code;
GO
CREATE TABLE verify_code(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(10) NOT NULL,
    type TINYINT NOT NULL,
    expire_time DATETIME NOT NULL,
    used TINYINT NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--3.用户地理位置 user_location
IF OBJECT_ID(N'user_location', N'U') IS NOT NULL
DROP TABLE user_location;
GO
CREATE TABLE user_location(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    lng DECIMAL(10,6) NOT NULL,
    lat DECIMAL(10,6) NOT NULL,
    province VARCHAR(50) NULL,
    city VARCHAR(50) NULL,
    district VARCHAR(50) NULL,
    address VARCHAR(200) NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--4.气象站点 weather_station
IF OBJECT_ID(N'weather_station', N'U') IS NOT NULL
DROP TABLE weather_station;
GO
CREATE TABLE weather_station(
    station_id VARCHAR(30) PRIMARY KEY,
    station_name VARCHAR(80) NOT NULL,
    station_type TINYINT NOT NULL,
    province VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    lng DECIMAL(10,6) NOT NULL,
    lat DECIMAL(10,6) NOT NULL,
    altitude DECIMAL(8,2) NULL,
    status TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT GETDATE(),
    update_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--5.天气实况 weather_real
IF OBJECT_ID(N'weather_real', N'U') IS NOT NULL
DROP TABLE weather_real;
GO
CREATE TABLE weather_real(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    station_id VARCHAR(30) NOT NULL,
    obs_time DATETIME NOT NULL,
    temp DECIMAL(5,2) NULL,
    feels_like DECIMAL(5,2) NULL,
    humidity INT NULL,
    wind_dir VARCHAR(20) NULL,
    wind_speed DECIMAL(5,2) NULL,
    wind_level INT NULL,
    pressure DECIMAL(8,2) NULL,
    rain DECIMAL(6,2) NULL,
    visibility INT NULL,
    weather_text VARCHAR(50) NULL,
    data_source VARCHAR(50) NOT NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--6.24小时历史天气 weather_history_24h
IF OBJECT_ID(N'weather_history_24h', N'U') IS NOT NULL
DROP TABLE weather_history_24h;
GO
CREATE TABLE weather_history_24h(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    station_id VARCHAR(30) NOT NULL,
    obs_time DATETIME NOT NULL,
    temp DECIMAL(5,2) NULL,
    humidity INT NULL,
    rain DECIMAL(6,2) NULL,
    wind_speed DECIMAL(5,2) NULL,
    pressure DECIMAL(8,2) NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--7.天气预报 weather_forecast
IF OBJECT_ID(N'weather_forecast', N'U') IS NOT NULL
DROP TABLE weather_forecast;
GO
CREATE TABLE weather_forecast(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    area_code VARCHAR(30) NOT NULL,
    forecast_type TINYINT NOT NULL, --1短临 2-24h 3-7天 4‑15天
    forecast_time DATETIME NOT NULL,
    target_time DATETIME NOT NULL,
    temp_max DECIMAL(5,2) NULL,
    temp_min DECIMAL(5,2) NULL,
    humidity INT NULL,
    wind_dir VARCHAR(20) NULL,
    wind_speed VARCHAR(20) NULL,
    wind_level VARCHAR(20) NULL,
    rain_prob INT NULL,
    weather_day VARCHAR(50) NULL,
    weather_night VARCHAR(50) NULL,
    data_source VARCHAR(50) NOT NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--8.气象预警 weather_alert
IF OBJECT_ID(N'weather_alert', N'U') IS NOT NULL
DROP TABLE weather_alert;
GO
CREATE TABLE weather_alert(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    alert_id VARCHAR(100) NOT NULL UNIQUE,
    publish_org VARCHAR(100) NOT NULL,
    publish_time DATETIME NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_level VARCHAR(20) NOT NULL,
    affected_area VARCHAR(200) NULL,
    alert_content TEXT NOT NULL,
    start_time DATETIME NULL,
    end_time DATETIME NULL,
    status TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--9.气候资料 weather_climate
IF OBJECT_ID(N'weather_climate', N'U') IS NOT NULL
DROP TABLE weather_climate;
GO
CREATE TABLE weather_climate(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    area_code VARCHAR(30) NOT NULL,
    stat_year INT NULL,
    stat_month INT NULL,
    avg_temp DECIMAL(5,2) NULL,
    max_temp DECIMAL(5,2) NULL,
    min_temp DECIMAL(5,2) NULL,
    total_rain DECIMAL(8,2) NULL,
    sunshine_hour DECIMAL(6,2) NULL,
    remark TEXT NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--10.水文信息 hydrology_info
IF OBJECT_ID(N'hydrology_info', N'U') IS NOT NULL
DROP TABLE hydrology_info;
GO
CREATE TABLE hydrology_info(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    station_name VARCHAR(80) NOT NULL,
    obs_time DATETIME NOT NULL,
    water_level DECIMAL(8,2) NULL,
    flow DECIMAL(10,2) NULL,
    warning_level DECIMAL(8,2) NULL,
    remark VARCHAR(500) NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--11.交通消息 traffic_info
IF OBJECT_ID(N'traffic_info', N'U') IS NOT NULL
DROP TABLE traffic_info;
GO
CREATE TABLE traffic_info(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    traffic_type TINYINT NOT NULL, --1地铁 2市内铁路
    line_name VARCHAR(50) NOT NULL,
    publish_time DATETIME NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status TINYINT NOT NULL DEFAULT 1,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--12.天气报告 weather_report
IF OBJECT_ID(N'weather_report', N'U') IS NOT NULL
DROP TABLE weather_report;
GO
CREATE TABLE weather_report(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_title VARCHAR(200) NOT NULL,
    source VARCHAR(100) NOT NULL,
    publish_date DATE NOT NULL,
    content TEXT NULL,
    file_url VARCHAR(255) NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--13.气象图层 weather_layer 雷达、云图、矢量图
IF OBJECT_ID(N'weather_layer', N'U') IS NOT NULL
DROP TABLE weather_layer;
GO
CREATE TABLE weather_layer(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    layer_code VARCHAR(50) NOT NULL,
    layer_name VARCHAR(100) NOT NULL,
    obs_time DATETIME NOT NULL,
    resource_url VARCHAR(255) NOT NULL,
    min_lng DECIMAL(10,6) NULL,
    max_lng DECIMAL(10,6) NULL,
    min_lat DECIMAL(10,6) NULL,
    max_lat DECIMAL(10,6) NULL,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO

--14.推送记录 push_record
IF OBJECT_ID(N'push_record', N'U') IS NOT NULL
DROP TABLE push_record;
GO
CREATE TABLE push_record(
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    user_id BIGINT NOT NULL,
    push_title VARCHAR(200) NOT NULL,
    push_content TEXT NOT NULL,
    push_type TINYINT NOT NULL, --1预警推送 2天气提醒
    push_status TINYINT NOT NULL DEFAULT 0,
    create_time DATETIME NOT NULL DEFAULT GETDATE()
);
GO
