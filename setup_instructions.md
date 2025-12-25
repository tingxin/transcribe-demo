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

## 3. 创建S3存储桶

```bash
# 使用AWS CLI创建存储桶
aws s3 mb s3://your-transcribe-bucket --region us-east-1
```

或者在AWS控制台中手动创建。

## 4. 配置脚本参数

编辑 `transcribe_audio.py` 文件中的配置参数：

```python
# 在main()函数中修改这些参数
CSV_FILE = 'call.csv'  # CSV文件路径
S3_BUCKET = 'your-transcribe-bucket'  # 替换为你的S3存储桶名称
AWS_REGION = 'us-east-1'  # AWS区域
LIMIT = 5  # 限制处理的文件数量，用于测试。设置为None处理所有文件
```

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
            "Resource": "arn:aws:s3:::your-transcribe-bucket/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-transcribe-bucket"
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