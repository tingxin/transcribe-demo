# 详细安装配置指南

## 📋 系统要求

### 操作系统
- Linux (推荐 Ubuntu 18.04+)
- macOS 10.14+
- Windows 10+ (需要WSL或Git Bash)

### Python环境
- Python 3.7 或更高版本
- pip 包管理器
- 虚拟环境 (推荐)

### AWS要求
- 有效的AWS账户
- 配置了适当权限的IAM用户或角色
- 访问现有S3存储桶或创建新桶的权限

## 🔧 详细安装步骤

### 步骤1: 准备Python环境

#### 检查Python版本
```bash
python3 --version
# 应该显示 Python 3.7.x 或更高版本
```

#### 创建虚拟环境（推荐）
```bash
# 创建虚拟环境
python3 -m venv transcribe-env

# 激活虚拟环境
# Linux/macOS:
source transcribe-env/bin/activate
# Windows:
transcribe-env\Scripts\activate

# 升级pip
pip install --upgrade pip
```

### 步骤2: 下载项目文件

```bash
# 如果使用Git
git clone <repository-url>
cd audio-transcription

# 或者下载ZIP文件并解压
# 确保所有Python文件都在同一目录下
```

### 步骤3: 安装Python依赖

```bash
# 安装所有依赖包
pip install -r requirements.txt

# 验证安装
pip list | grep -E "(pandas|requests|boto3|python-dotenv)"
```

#### 依赖包详细说明
- **pandas (>=1.3.0)**: 用于处理CSV文件和数据操作
- **requests (>=2.25.0)**: 用于HTTP请求和文件下载
- **boto3 (>=1.26.0)**: AWS SDK，用于S3和Transcribe服务
- **python-dotenv (>=0.19.0)**: 用于加载环境变量配置

### 步骤4: 配置AWS凭证

#### 方法1: AWS CLI配置（推荐）

```bash
# 安装AWS CLI
pip install awscli

# 配置凭证
aws configure

# 输入以下信息：
# AWS Access Key ID: [你的访问密钥ID]
# AWS Secret Access Key: [你的秘密访问密钥]
# Default region name: us-east-1
# Default output format: json

# 验证配置
aws sts get-caller-identity
```

#### 方法2: 环境变量配置

```bash
# 临时设置（当前会话有效）
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_DEFAULT_REGION=us-east-1

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE' >> ~/.bashrc
echo 'export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' >> ~/.bashrc
echo 'export AWS_DEFAULT_REGION=us-east-1' >> ~/.bashrc
source ~/.bashrc
```

#### 方法3: IAM角色（EC2实例）

如果在EC2实例上运行，可以使用IAM角色：

1. 在AWS控制台创建IAM角色
2. 附加必要的权限策略
3. 将角色分配给EC2实例
4. 无需额外配置，脚本会自动使用角色凭证

### 步骤5: 配置S3存储桶

#### 检查现有桶权限
```bash
# 列出可访问的桶
aws s3 ls

# 检查特定桶的权限
aws s3 ls s3://your-bucket-name/

# 测试上传权限
echo "test" | aws s3 cp - s3://your-bucket-name/test.txt
aws s3 rm s3://your-bucket-name/test.txt
```

#### 创建专用文件夹（可选）
```bash
# 在现有桶中创建文件夹
aws s3api put-object --bucket your-bucket-name --key audio-transcripts/

# 或者使用cp命令创建空文件夹
aws s3 cp /dev/null s3://your-bucket-name/audio-transcripts/.keep
```

### 步骤6: 配置项目参数

#### 复制配置模板
```bash
cp .env.example .env
```

#### 编辑配置文件
```bash
# 使用你喜欢的编辑器
nano .env
# 或
vim .env
# 或
code .env
```

#### 详细配置说明

```bash
# ===== AWS S3 配置 =====
# 必填：你的S3存储桶名称
S3_BUCKET=my-company-audio-bucket

# 可选：桶内文件夹前缀，用于组织文件
# 示例：audio-transcripts/ 会将文件存储在 s3://bucket/audio-transcripts/audio/
S3_FOLDER_PREFIX=audio-transcripts/

# AWS区域，建议使用us-east-1（成本较低）
AWS_REGION=us-east-1

# ===== 处理配置 =====
# CSV文件路径（相对于脚本目录）
CSV_FILE=call.csv

# 处理文件数量限制（用于测试和成本控制）
# 设置为空或删除此行表示处理所有文件
LIMIT=5

# ===== 缓存配置 =====
# 缓存文件保留天数，超过此时间的文件会被自动清理
CACHE_MAX_AGE_DAYS=7

# ===== 说话人标签配置 =====
# 自定义说话人标签，用于输出中的标识
SPEAKER_0_LABEL=客服代表
SPEAKER_1_LABEL=客户
```

### 步骤7: 准备CSV数据文件

确保你的CSV文件包含名为"通话录音"的列，其中包含MP3文件的URL。

#### CSV文件格式示例
```csv
催收外呼id,客户号,外呼时间,通话录音,collection_result
1001,12345,2025/12/25 10:30,https://example.com/audio1.mp3,有还款诚意
1002,12346,2025/12/25 11:00,https://example.com/audio2.mp3,无还款诚意
```

#### 验证CSV文件
```bash
# 检查文件是否存在
ls -la call.csv

# 查看文件前几行
head -5 call.csv

# 检查列名
head -1 call.csv | tr ',' '\n' | nl
```

## 🧪 测试安装

### 步骤1: 验证环境配置
```bash
# 测试Python依赖
python3 -c "import pandas, requests, boto3; print('所有依赖包安装成功')"

# 测试AWS凭证
python3 -c "import boto3; print(boto3.Session().get_credentials().access_key[:10] + '...')"

# 测试环境变量加载
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('S3桶:', os.getenv('S3_BUCKET'))"
```

### 步骤2: 运行测试脚本
```bash
# 运行单文件测试
python3 test_transcribe.py

# 预期输出：
# INFO - AWS凭证验证成功
# INFO - 测试配置: ...
# INFO - 步骤1: 下载音频文件
# INFO - 步骤2: 上传到S3
# INFO - 步骤3: 启动AWS Transcribe任务
# INFO - 步骤4: 等待转录完成
# INFO - 步骤5: 下载转录结果
# INFO - 转录完成！
```

### 步骤3: 检查输出文件
```bash
# 检查生成的目录和文件
ls -la test_results/
ls -la test_audio/

# 查看转录结果
cat test_results/test_transcript.txt
```

## 🔍 验证清单

在开始批量处理之前，请确认以下项目：

- [ ] Python 3.7+ 已安装
- [ ] 所有依赖包已安装
- [ ] AWS凭证已正确配置
- [ ] S3桶访问权限已验证
- [ ] .env文件已正确配置
- [ ] CSV文件格式正确
- [ ] 测试脚本运行成功
- [ ] 输出文件格式符合预期

## 🚀 开始批量处理

确认所有测试通过后，可以开始批量处理：

```bash
# 开始批量转录
python3 transcribe_audio.py

# 监控进度
tail -f transcribe.log  # 如果有日志文件

# 检查结果
ls -la transcripts/
```

## 📊 监控和维护

### 查看缓存使用情况
```bash
python3 manage_cache.py info
```

### 定期清理缓存
```bash
# 清理7天前的缓存
python3 manage_cache.py clean 7

# 或设置定时任务
crontab -e
# 添加：0 2 * * * /path/to/python3 /path/to/manage_cache.py clean 7
```

### 监控AWS使用量
```bash
# 查看S3使用量
aws s3 ls s3://your-bucket/audio-transcripts/ --recursive --human-readable --summarize

# 查看Transcribe任务
aws transcribe list-transcription-jobs --status COMPLETED --max-items 10
```

## 🔧 高级配置

### 自定义音频文件格式
如果需要处理其他格式的音频文件，修改脚本中的MediaFormat参数：

```python
# 在start_transcription_job中修改
MediaFormat='wav'  # 或 'mp4', 'flac' 等
```

### 调整转录参数
```python
# 修改转录设置
Settings={
    'ShowSpeakerLabels': True,
    'MaxSpeakerLabels': 5,  # 调整最大说话人数量
    'ChannelIdentification': True,
    'ShowAlternatives': True,  # 显示替代转录
    'MaxAlternatives': 2
}
```

### 批量处理优化
```python
# 在main函数中调整并发设置
import concurrent.futures

# 使用线程池处理多个文件
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    # 并发处理逻辑
```

## 🆘 获取帮助

如果遇到问题：

1. **查看日志**: 检查控制台输出和错误信息
2. **验证配置**: 确认所有配置参数正确
3. **测试网络**: 确认可以访问AWS服务
4. **检查权限**: 验证IAM权限设置
5. **查看文档**: 参考AWS Transcribe官方文档
6. **提交Issue**: 在项目仓库中报告问题

### 常用调试命令
```bash
# 检查网络连接
ping transcribe.us-east-1.amazonaws.com

# 测试S3连接
aws s3 ls s3://your-bucket --region us-east-1

# 查看详细错误
python3 test_transcribe.py 2>&1 | tee debug.log
```