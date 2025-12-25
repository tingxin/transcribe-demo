# 🚀 快速开始指南

## 5分钟快速部署

### 1️⃣ 安装依赖 (1分钟)
```bash
pip3 install pandas requests boto3 python-dotenv
```

### 2️⃣ 配置AWS (2分钟)
```bash
# 安装AWS CLI
pip3 install awscli

# 配置凭证
aws configure
# 输入: Access Key, Secret Key, Region (us-east-1), Format (json)
```

### 3️⃣ 配置项目 (1分钟)
```bash
# 复制配置文件
cp .env.example .env

# 编辑配置（只需修改这两行）
S3_BUCKET=your-bucket-name
S3_FOLDER_PREFIX=audio-transcripts/
```

### 4️⃣ 测试运行 (1分钟)
```bash
python3 test_transcribe.py
```

## ✅ 成功标志

看到以下输出表示配置成功：
```
INFO - AWS凭证验证成功
INFO - 转录完成！
INFO - 带标签的转录预览 ===
[客服]: Hola buenos días...
```

## 🎯 开始批量处理

```bash
python3 transcribe_audio.py
```

## 📁 查看结果

- `test_results/test_transcript.txt` - 测试结果
- `transcripts/transcript_*.txt` - 批量结果

## 🔧 常用命令

```bash
# 查看缓存
python3 manage_cache.py info

# 清理缓存
python3 manage_cache.py clean

# 处理指定数量文件（在.env中设置LIMIT=5）
```

## ❓ 遇到问题？

1. **AWS凭证错误**: 运行 `aws sts get-caller-identity` 检查
2. **S3权限不足**: 确认桶名正确，有读写权限
3. **转录失败**: 检查音频文件URL是否有效

详细说明请查看 [SETUP_GUIDE.md](SETUP_GUIDE.md)