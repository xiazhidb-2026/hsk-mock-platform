# HSK Mock Platform - 博主Web端

## 项目介绍
HSK汉语水平模拟考试平台的博主后台管理系统，用于创建题目、组卷、发布和管理试卷。

## 技术栈
- Vue 3 + TypeScript
- Vite
- Pinia (状态管理)
- Vue Router
- Element Plus (UI框架)
- Axios

## 开发指南

### 安装依赖
```bash
cd web
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## 项目结构

```
web/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口
│   ├── assets/            # 静态文件
│   ├── components/        # 公共组件
│   ├── layouts/           # 布局组件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia状态
│   ├── views/             # 页面视图
│   │   ├── dashboard/     # 数据看板
│   │   ├── questions/     # 题目管理
│   │   ├── templates/     # 试卷管理
│   │   ├── analytics/     # 数据分析
│   │   └── settings/      # 个人设置
│   ├── App.vue
│   └── main.ts
├── index.html
├── vite.config.ts
└── package.json
```

## 功能模块

### 1. 数据看板 (Dashboard)
- 总考试次数
- 总用户数
- 平均分/通过率
- 热门试卷排行

### 2. 题目管理 (Questions)
- 题目列表（支持筛选）
- 创建题目
- 批量导入（Excel）
- 题目编辑/删除

### 3. 试卷管理 (Templates)
- 试卷列表
- 创建试卷（拖拽式组卷）
- 发布/下架
- 设置价格

### 4. 数据分析 (Analytics)
- 考试趋势图
- 用户分布
- 收入统计

## API配置

在 `.env.development` 中配置API地址：
```
VITE_API_BASE_URL=http://localhost/api/v1
```

## License

MIT
