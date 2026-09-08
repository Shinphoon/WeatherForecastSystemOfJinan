# 济南市天气预报可视化系统

## 项目简介

本项目是一个面向济南市天气信息展示与分析的可视化系统，
基于 Vue 构建前端页面，并结合 WebGIS 地图技术实现天气信息的空间可视化。

系统主要用于展示济南市天气状况、天气预报、气象站点、
雷达信息及天气预警等内容，为天气信息的查询和可视化分析提供支持。

## 主要功能

- 济南市天气信息可视化展示
- 天气预报信息查询
- 气象站点地图展示
- 天气雷达信息展示
- 天气预警信息展示
- 用户登录与注册
- WebGIS 地图交互与空间信息展示

## 技术栈

### 前端

- Vue
- Vite
- JavaScript
- HTML
- CSS
- WebGIS

### 后端

- Python

### 数据库

项目相关数据库脚本位于：

`database/SQLQuery1.sql`

## 项目目录

```text
WeatherForecastSystemOfJinan/
├── database/              # 数据库相关文件
│   └── SQLQuery1.sql
│
├── public/                # 公共静态资源
│
├── src/                   # 项目主要源代码
│   ├── api/               # API 请求
│   ├── assets/            # 图片等静态资源
│   ├── backend/           # Python 后端代码
│   ├── components/        # Vue 公共组件
│   ├── map/               # 地图相关代码
│   ├── router/            # Vue 路由
│   ├── views/             # 页面组件
│   ├── App.vue            # 根组件
│   └── main.js            # 前端入口
│
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
└── README.md