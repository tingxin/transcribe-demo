# 音频转录脚本设置说明

## 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

## 2. AWS配置

### 方法1: 使用AWS CLI配置
```bash
# 安装AWS CLI
pip3 install awscli

# 配置AWS凭证
aws configure
```

输入你的：
- AWS Access Key ID
- AWS Secret Access Key  
- Default region name (建议使用 us-east-1)
- Default output format (json)

### 方法2: 使用环境变量
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 方法3: 使用IAM角色 (如果在EC2上运行)
无需额外配置，脚本会自动使用实例的IAM角色。

## 3. 使用现有S3存储桶

如果你没有创建新桶的权限，可以使用现有的S3桶中的文件夹：

```bash
# 检查现有桶的访问权限
aws s3 ls s3://your-existing-bucket/

# 可选：创建专用文件夹（如果有权限）
aws s3api put-object --bucket your-existing-bucket --key audio-transcripts/
```

**注意**: 确保你对现有桶有以下权限：
- `s3:PutObject` - 上传文件
- `s3:GetObject` - 读取文件  
- `s3:ListBucket` - 列出桶内容

## 4. 配置环境变量

复制环境变量模板文件并编辑：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，设置你的配置：

```bash
# AWS S3 配置
S3_BUCKET=your-existing-bucket-name
S3_FOLDER_PREFIX=audio-transcripts/
AWS_REGION=us-east-1

# 处理配置
CSV_FILE=call.csv
LIMIT=5
```

**参数说明**:
- `S3_BUCKET`: 你现有的S3存储桶名称
- `S3_FOLDER_PREFIX`: 在桶中使用的文件夹前缀（可以为空）
- `AWS_REGION`: AWS区域
- `CSV_FILE`: CSV文件路径
- `LIMIT`: 处理的文件数量限制（设置为空表示处理所有文件）

## 5. 运行脚本

```bash
python3 transcribe_audio.py
```

## 6. 输出文件

脚本会创建以下目录和文件：

- `downloaded_audio/` - 下载的音频文件
- `transcripts/` - 转录结果
  - `transcript_X.json` - 完整的转录结果（包含说话人信息）
  - `transcript_X.txt` - 纯文本转录结果

## 7. 所需AWS权限

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
            "Resource": "arn:aws:s3:::your-existing-bucket/audio-transcripts/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-existing-bucket"
        }
    ]
}
```

## 8. 注意事项

- AWS Transcribe按使用量收费，请注意成本
- 大文件转录可能需要较长时间
- 脚本会自动处理网络错误和重试
- 建议先用小批量数据测试（设置LIMIT参数）
- 转录结果使用美国西班牙语模型，适合墨西哥西班牙语