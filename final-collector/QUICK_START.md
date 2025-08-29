# 🚀 Quick Start - 微服务 OpenTelemetry 配置

## 核心信息
- **Collector 端点**: `http://localhost:4326`
- **协议**: OTLP HTTP
- **状态**: 已就绪，等待连接

## 最简配置

### 环境变量 (通用)
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4326
OTEL_SERVICE_NAME=your-service-name
```

### Spring Boot (application.yml)
```yaml
management:
  otlp:
    tracing:
      endpoint: http://localhost:4326/v1/traces
  tracing:
    sampling:
      probability: 1.0
```

### Python
```python
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4326
# 然后正常使用 OpenTelemetry 库
```

### Go
```go
otlptracehttp.WithEndpoint("http://localhost:4326")
```

### Node.js
```javascript
url: 'http://localhost:4326/v1/traces'
```

## 启动步骤
1. 启动 Collector: `.\final-collector.exe --config=config.yml`
2. 配置微服务指向 `localhost:4326`
3. 发送请求测试
4. 观察 Collector 控制台输出

## 验证成功
看到这样的日志表示成功：
```
info tailsamplingprocessor Received traces batch
info debugexporter TracesExporter {"traces": 1}
```

就这么简单！🎯
