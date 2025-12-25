#!/usr/bin/env python3
"""
简化版音频转录测试脚本
用于测试单个音频文件的下载和转录
"""

import pandas as pd
import requests
import boto3
import os
import time
import json
from pathlib import Path
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_single_audio():
    """测试单个音频文件的处理流程"""
    
    # 从环境变量读取配置参数
    CSV_FILE = os.getenv('CSV_FILE', 'call.csv')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # 验证必需的配置
    if not S3_BUCKET:
        logger.error("S3_BUCKET 环境变量未设置，请检查.env文件")
        return
    
    logger.info(f"测试配置:")
    logger.info(f"  CSV文件: {CSV_FILE}")
    logger.info(f"  S3桶: {S3_BUCKET}")
    logger.info(f"  S3文件夹前缀: {S3_FOLDER_PREFIX}")
    logger.info(f"  AWS区域: {AWS_REGION}")
    
    try:
        # 读取CSV文件获取第一个音频URL
        df = pd.read_csv(CSV_FILE)
        audio_urls = df[df['通话录音'].notna() & (df['通话录音'] != '')]['通话录音']
        
        if len(audio_urls) == 0:
            logger.error("CSV文件中没有找到有效的音频URL")
            return
        
        # 取第一个URL进行测试
        test_url = audio_urls.iloc[0]
        logger.info(f"测试URL: {test_url}")
        
        # 1. 下载音频文件（使用缓存）
        logger.info("步骤1: 下载音频文件")
        
        # 生成缓存文件名
        import hashlib
        url_hash = hashlib.md5(test_url.encode()).hexdigest()[:8]
        cached_filename = f"test_audio_{url_hash}.mp3"
        
        # 保存到本地
        audio_dir = Path('test_audio')
        audio_dir.mkdir(exist_ok=True)
        local_file = audio_dir / cached_filename
        
        # 检查缓存
        if local_file.exists():
            file_size = local_file.stat().st_size
            if file_size > 0:
                logger.info(f"使用缓存文件: {local_file} (大小: {file_size} 字节)")
            else:
                logger.warning(f"缓存文件为空，重新下载: {local_file}")
                local_file.unlink()
                
        if not local_file.exists():
            logger.info(f"下载新文件: {test_url}")
            response = requests.get(test_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = local_file.stat().st_size
            logger.info(f"音频文件已下载: {local_file} (大小: {file_size} 字节)")
        
        # 验证文件
        if not local_file.exists() or local_file.stat().st_size == 0:
            logger.error("音频文件下载失败或为空")
            return
        
        # 2. 上传到S3（使用文件夹前缀）
        logger.info("步骤2: 上传到S3")
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        s3_key = f"{S3_FOLDER_PREFIX}test-audio/{cached_filename}"
        
        s3_client.upload_file(str(local_file), S3_BUCKET, s3_key)
        s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
        logger.info(f"文件已上传到S3: {s3_uri}")
        
        # 3. 启动转录任务
        logger.info("步骤3: 启动AWS Transcribe任务")
        transcribe_client = boto3.client('transcribe', region_name=AWS_REGION)
        job_name = f"test-transcribe-{int(time.time())}"
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='mp3',
            LanguageCode='es-US',  # 美国西班牙语
            Settings={
                'ShowSpeakerLabels': True,
                'MaxSpeakerLabels': 10,
                'ChannelIdentification': True
            }
        )
        
        logger.info(f"转录任务已启动: {job_name}")
        
        # 4. 等待转录完成
        logger.info("步骤4: 等待转录完成（这可能需要几分钟）")
        
        while True:
            response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            
            status = response['TranscriptionJob']['TranscriptionJobStatus']
            logger.info(f"转录状态: {status}")
            
            if status == 'COMPLETED':
                # 5. 下载转录结果
                logger.info("步骤5: 下载转录结果")
                transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                
                transcript_response = requests.get(transcript_uri)
                transcript_data = transcript_response.json()
                
                # 保存结果
                result_dir = Path('test_results')
                result_dir.mkdir(exist_ok=True)
                
                # 保存完整JSON结果
                with open(result_dir / 'test_transcript.json', 'w', encoding='utf-8') as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=2)
                
                # 保存纯文本结果
                transcript_text = transcript_data['results']['transcripts'][0]['transcript']
                with open(result_dir / 'test_transcript.txt', 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                
                logger.info("转录完成！")
                logger.info(f"转录文本: {transcript_text}")
                logger.info(f"完整结果保存在: {result_dir}")
                
                break
                
            elif status == 'FAILED':
                logger.error("转录任务失败")
                failure_reason = response['TranscriptionJob'].get('FailureReason', '未知原因')
                logger.error(f"失败原因: {failure_reason}")
                break
                
            else:
                time.sleep(30)  # 等待30秒后再次检查
        
        # 清理（可选）
        # os.remove(local_file)
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 检查AWS凭证
    try:
        boto3.Session().get_credentials()
        logger.info("AWS凭证验证成功")
    except Exception as e:
        logger.error(f"AWS凭证验证失败: {str(e)}")
        logger.error("请先配置AWS凭证")
        exit(1)
    
    # 运行测试
    test_single_audio()