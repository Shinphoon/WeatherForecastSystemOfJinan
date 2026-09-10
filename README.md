# 济南市天气实况与天气预报可视化系统

## 项目简介

本项目是一个面向济南市及周边地区的天气信息 WebGIS 可视化系统，基于 Vue 3 构建前端界面，使用 FastAPI 提供后端服务，并结合 SQL Server 数据库实现用户、气象站等数据的持久化管理。

系统目前已实现天气实况、天气预报、国家气象站地图、天气雷达、用户登录注册、个人设置、管理员管理以及微信公众号文章展示等功能。

项目以移动端页面为主要设计目标，可用于 WebGIS、气象信息可视化及前后端综合课程设计。

---

## 主要功能

### 天气实况

- 国家气象站实时天气查询
- 温度、湿度、气压等气象要素展示
- 风向与风速展示
- 实况气象数据图表
- 地图气象站选择
- 支持动态加载数据库中的气象站

### 天气预报

- 短时天气预报
- 未来 2 小时天气预报
- 未来 24 小时天气预报
- 多气象站切换查询
- 天气预报数据可视化

### WebGIS 地图

- 国家气象站空间分布
- 气象站点击交互
- 经纬度空间定位
- 济南及周边地区气象站展示
- 雷达组合反射率图像展示

### 用户系统

- 用户注册
- 用户登录
- JWT 身份认证
- 用户信息读取
- 登录状态保持
- 退出登录

### 个人设置

- 默认气象站设置
- 预警推送设置
- 修改登录密码
- 修改绑定手机号
- 浏览器获取当前位置
- 保存最近位置经纬度

### 管理员功能

系统区分普通用户与管理员。

普通用户可以使用天气查询、地图、预报及个人设置功能。

管理员可以进入管理中心，目前包括：

- 国家气象站管理
- 新增国家气象站
- 气象站列表查看
- 微信公众号文章管理

### 微信公众号文章

系统支持展示微信公众号最新文章。

当前采用人工提交微信公众号文章 URL、后端解析文章信息的方式，实现：

- 最新文章 URL 保存
- 文章标题解析
- 作者信息解析
- 封面信息解析
- 发布时间解析
- 首页最新文章展示

---

## 当前气象站

系统目前已接入 11 个国家气象站：

| 站号 | 站名 |
| --- | --- |
| 54727 | 章丘 |
| 54816 | 长清 |
| 54818 | 平阴 |
| 54821 | 济阳 |
| 54823 | 济南 |
| 54828 | 莱芜 |
| 54827 | 泰安 |
| 54826 | 泰山 |
| 54830 | 淄博 |
| 54822 | 邹平 |
| 54829 | 周村 |

气象站信息已经由静态 JSON 配置逐步迁移至 SQL Server 数据库，实现动态读取与管理。

---

## 技术栈

### 前端

- Vue 3
- Vite
- JavaScript
- HTML
- CSS
- Vue Router
- Axios
- WebGIS 地图技术
- Browser Geolocation API

### 后端

- Python
- FastAPI
- Uvicorn
- Pydantic
- python-jose
- bcrypt
- python-dotenv
- HTTP 数据获取与解析

### 数据库

- Microsoft SQL Server
- T-SQL
- pyodbc

数据库目前主要保存：

- 用户账号
- 用户角色
- 手机号
- 用户最近位置
- 推送设置
- 国家气象站信息

---

## 系统架构

```text
Vue 3
  │
  │ Axios
  ▼
Vite Proxy
  │
  ▼
FastAPI
  │
  ├── 天气数据接口
  ├── 用户认证接口
  ├── 气象站接口
  ├── 公众号文章接口
  │
  ▼
SQL Server
```

前端统一通过：

```text
/api
```

访问后端服务。

Vite 开发服务器会将请求代理至：

```text
http://127.0.0.1:8000
```

---

## 项目目录

```text
jinan-weather
│
├─ src
│  ├─ api
│  │  ├─ auth.js
│  │  └─ weather.js
│  │
│  ├─ components
│  │  ├─ StationMap.vue
│  │  └─ WeatherCard.vue
│  │
│  ├─ views
│  │  ├─ Home.vue
│  │  ├─ Reality.vue
│  │  ├─ Forecast.vue
│  │  ├─ Radar.vue
│  │  ├─ Mine.vue
│  │  ├─ Login.vue
│  │  ├─ Register.vue
│  │  ├─ Security.vue
│  │  ├─ PhoneSetting.vue
│  │  ├─ LocationSetting.vue
│  │  └─ WechatAdmin.vue
│  │
│  ├─ router
│  │  └─ index.js
│  │
│  └─ backend
│     ├─ main.py
│     ├─ auth.py
│     ├─ database.py
│     ├─ qweather_spider.py
│     ├─ forecast_service.py
│     ├─ wechat_service.py
│     └─ wechat_latest.json
│
├─ vite.config.js
├─ package.json
├─ .gitignore
└─ README.md
```

---

## 数据库设计

### sys_user

用于存储用户账号及个人设置。

主要字段包括：

```text
id
username
password
nickname
phone
avatar
role
last_lng
last_lat
last_address
push_enable
status
create_time
update_time
```

其中：

```text
role = user
```

表示普通用户。

```text
role = admin
```

表示系统管理员。

### weather_station

用于保存国家气象站信息。

主要字段包括：

```text
station_id
station_name
station_type
province
city
district
lng
lat
altitude
status
create_time
update_time
```

---

## API 示例

### 获取气象站

```http
GET /weather/stations
```

### 用户注册

```http
POST /auth/register
```

### 用户登录

```http
POST /auth/login
```

### 获取当前用户

```http
GET /auth/me
```

### 修改密码

```http
PUT /auth/password
```

### 修改手机号

```http
PUT /auth/phone
```

### 保存当前位置

```http
PUT /auth/location
```

### 获取微信公众号文章

```http
GET /weather/wechat/latest
```

---

## 本地运行

### 1. 启动后端

进入：

```powershell
cd src\backend
```

激活 Python 虚拟环境：

```powershell
venv\Scripts\activate
```

启动 FastAPI：

```powershell
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

```text
http://127.0.0.1:8000
```

FastAPI API 文档：

```text
http://127.0.0.1:8000/docs
```

### 2. 启动前端

回到项目根目录：

```powershell
npm run dev
```

默认访问：

```text
http://localhost:5173
```

---

## 环境变量

项目中的敏感信息通过 `.env` 保存。

例如：

```env
WECHAT_APP_ID=
WECHAT_APP_SECRET=
WECHAT_ADMIN_PASSWORD=
```

`.env` 已加入 `.gitignore`，请勿将 AppSecret、数据库密码或管理员密码上传至 GitHub。

---

## 当前开发进度

目前已经完成：

- [x] Vue 移动端页面框架
- [x] FastAPI 后端
- [x] 天气实况
- [x] 天气预报
- [x] 雷达图像展示
- [x] 国家站地图
- [x] 多气象站切换
- [x] SQL Server 数据库
- [x] 用户注册与登录
- [x] JWT 身份认证
- [x] 用户角色区分
- [x] 管理员入口
- [x] 动态气象站读取
- [x] 修改密码
- [x] 修改手机号
- [x] 最近位置保存
- [x] 微信公众号文章展示
- [ ] 管理员路由权限保护
- [ ] 管理员后端权限统一认证
- [ ] 气象站数据库新增接口完善
- [ ] 用户意见反馈
- [ ] 关于系统页面
- [ ] 天气预警功能进一步完善

---

## 项目特点

本项目不是单纯的天气页面，而是将：

```text
气象数据
+
WebGIS
+
Vue 前端
+
FastAPI 后端
+
SQL Server 数据库
+
用户权限系统
```

整合到同一个天气信息可视化系统中。

项目目前已经具备较完整的前端、后端、数据库和 WebGIS 综合应用结构，并仍在持续完善。

---

## 项目名称

**济南市天气实况与天气预报可视化系统**

WebGIS Course Design

Version 1.0
