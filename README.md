# HSK Mock Platform
HSK汉语水平模拟考试平台

## 项目结构

```
hsk-mock-platform/
├── docker-compose.yml       # Docker编排
├── nginx/                   # Nginx配置
├── docs/                    # 项目文档
├── services/                # 微服务
│   ├── user-service/       # 用户服务
│   ├── exam-service/       # 考试服务
│   ├── question-service/   # 题库服务
│   └── creator-service/    # 博主服务
├── web/                     # 博主Web端
└── app/                     # Flutter App
```

## 快速开始

### 开发环境

1. 启动所有服务：
```bash
docker-compose up -d
```

2. 访问服务：
- API Gateway: http://localhost
- User Service: http://localhost:8001
- Exam Service: http://localhost:8002
- Question Service: http://localhost:8003
- Creator Service: http://localhost:8004

## 技术栈

- **后端**: Python FastAPI
- **数据库**: PostgreSQL
- **缓存**: Redis
- **网关**: Nginx
- **前端**: Vue3 (Web), Flutter (App)

## License

MIT
