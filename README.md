# 音频转录系统

一个完整的音频转录解决方案，可以从CSV文件中批量下载MP3音频文件，并使用AWS Transcribe服务进行语音转文字，特别针对墨西哥西班牙语进行了优化。

## 🚀 主要功能

- **批量处理**: 从CSV文件批量下载和转录音频文件
- **智能缓存**: 避免重复下载，支持断点续传
- **说话人识别**: 自动区分不同说话人（如客服vs客户）
- **带标签输出**: 清晰标记每段话的说话人
- **多种格式**: 支持JSON和格式化文本输出
- **自定义标签**: 可自定义说话人名称
- **成本控制**: 支持限制处理数量，避免意外费用

## 📋 环境要求

- Python 3.7+
- AWS账户和相应权限
- 现有的S3存储桶（或创建新桶的权限）

## 🛠️ 快速开始

### 1. 安装依赖

```bash
git clone <repository>
cd audio-transcription
pip3 install -r requirements.txt
```

### 2. 配置AWS凭证

```bash
# 方法1: 使用AWS CLI（推荐）
pip3 install awscli
aws configure

# 方法2: 设置环境变量
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 3. 配置项目参数

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

配置示例：
```bash
# AWS S3 配置
S3_BUCKET=your-existing-bucket-name
S3_FOLDER_PREFIX=audio-transcripts/
AWS_REGION=us-east-1

# 处理配置
CSV_FILE=call.csv
LIMIT=5

# 说话人标签配置
SPEAKER_0_LABEL=客服
SPEAKER_1_LABEL=客户
```

### 4. 测试运行

```bash
# 测试单个文件
python3 test_transcribe.py

# 批量处理
python3 transcribe_audio.py
```

## 📁 项目结构

```
project/
├── transcribe_audio.py      # 主转录脚本
├── test_transcribe.py       # 测试脚本
├── manage_cache.py          # 缓存管理工具
├── requirements.txt         # 依赖包列表
├── .env                     # 配置文件
├── call.csv                 # 音频URL数据
├── downloaded_audio/        # 音频文件缓存
├── transcripts/            # 批量转录结果
├── test_audio/             # 测试音频文件
└── test_results/           # 测试转录结果
```

## 📊 输出格式

### JSON格式 (`transcript_X.json`)
```json
{
  "transcript": "完整的原始转录文本...",
  "labeled_transcript": "[客服]: 您好...\n[客户]: 我想咨询...",
  "speaker_segments": [...],
  "full_result": {...}
}
```

### 文本格式 (`transcript_X.txt`)
```
=== 带标签的转录文本（推荐用于分析） ===
[客服]: Hola buenos días señor Jonathan gracias por tomar la llamada...
[客户]: De hecho yo les escribí ahí en la aplicación...

=== 原始完整转录文本 ===
Hola buenos días señor Jonathan gracias por tomar la llamada...

=== 按说话人分段（详细时间） ===
[客服] [00:00.00 - 00:15.23]: Hola buenos días señor Jonathan...
```

## 🔧 高级功能

### 缓存管理
```bash
# 查看缓存信息
python3 manage_cache.py info

# 清理7天前的缓存
python3 manage_cache.py clean 7

# 清空所有缓存
python3 manage_cache.py clear
```

### 自定义说话人标签
在`.env`文件中配置：
```bash
SPEAKER_0_LABEL=销售代表
SPEAKER_1_LABEL=潜在客户
SPEAKER_2_LABEL=经理
```

### 批量处理控制
```bash
# 处理前5个文件（测试用）
LIMIT=5

# 处理所有文件
LIMIT=

# 指定CSV文件
CSV_FILE=my_audio_list.csv
```

## 🔐 AWS权限配置

确保你的AWS用户或角色具有以下权限：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "transcribe:StartTranscriptionJob",
                "transcribe:GetTranscriptionJob",
                "transcribe:ListTranscriptionJobs"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket/audio-transcripts/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-bucket"
        }
    ]
}
```

## 🐛 故障排除

### 常见问题

**AWS凭证错误**
```bash
# 检查配置
aws sts get-caller-identity

# 重新配置
aws configure
```

**S3权限不足**
- 确保有桶的读写权限
- 检查IAM策略配置
- 验证桶名称正确

**转录任务失败**
- 检查音频文件格式（支持MP3, WAV等）
- 确保文件大小不超过限制
- 检查网络连接

**带标签转录为空**
- 检查AWS Transcribe说话人识别功能
- 查看日志中的调试信息
- 尝试不同的音频文件

### 调试模式
修改脚本中的日志级别：
```python
logging.basicConfig(level=logging.DEBUG)
```

## 💰 成本控制

### AWS Transcribe定价
- 按分钟计费
- 建议先用小批量测试
- 使用`LIMIT`参数控制处理数量

### 优化建议
- 使用缓存避免重复下载
- 合理设置缓存清理周期
- 监控AWS使用量

## 🌍 语言支持

- **主要语言**: 墨西哥西班牙语
- **识别模型**: 美国西班牙语 (es-US)
- **功能**: 说话人识别、声道分离
- **输出**: UTF-8编码，支持西班牙语字符

## 📈 性能优化

### 处理速度
- 并发下载音频文件
- 智能缓存系统
- 断点续传支持

### 资源使用
- 自动清理临时文件
- 可配置的缓存策略
- 内存优化的流式处理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果遇到问题或需要帮助：

1. 查看故障排除部分
2. 检查日志输出
3. 提交 Issue 描述问题
4. 提供错误日志和配置信息

---

**注意**: 请确保遵守AWS服务条款和相关法律法规，特别是关于音频数据处理和隐私保护的规定。