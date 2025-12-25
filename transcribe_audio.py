#!/usr/bin/env python3
"""
音频文件下载和转录脚本
从CSV文件中读取MP3 URL，下载音频文件，并使用AWS Transcribe进行语音转文字
"""

import pandas as pd
import requests
import boto3
import os
import time
import json
from urllib.parse import urlparse
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioTranscriber:
    def __init__(self, aws_region='us-east-1'):
        """
        初始化转录器
        
        Args:
            aws_region: AWS区域，默认为us-east-1
        """
        self.transcribe_client = boto3.client('transcribe', region_name=aws_region)
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.aws_region = aws_region
        
        # 创建本地目录
        self.audio_dir = Path('downloaded_audio')
        self.transcripts_dir = Path('transcripts')
        self.audio_dir.mkdir(exist_ok=True)
        self.transcripts_dir.mkdir(exist_ok=True)
    
    def download_audio_file(self, url, filename):
        """
        下载音频文件
        
        Args:
            url: 音频文件URL
            filename: 本地保存的文件名
            
        Returns:
            str: 本地文件路径，如果下载失败返回None
        """
        try:
            logger.info(f"正在下载: {url}")
            
            # 发送HTTP请求下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            file_path = self.audio_dir / filename
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"下载完成: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"下载失败 {url}: {str(e)}")
            return None
    
    def upload_to_s3(self, local_file_path, bucket_name, s3_key):
        """
        上传文件到S3
        
        Args:
            local_file_path: 本地文件路径
            bucket_name: S3存储桶名称
            s3_key: S3对象键
            
        Returns:
            str: S3 URI，如果上传失败返回None
        """
        try:
            logger.info(f"正在上传到S3: {s3_key}")
            
            self.s3_client.upload_file(local_file_path, bucket_name, s3_key)
            s3_uri = f"s3://{bucket_name}/{s3_key}"
            
            logger.info(f"上传完成: {s3_uri}")
            return s3_uri
            
        except Exception as e:
            logger.error(f"S3上传失败: {str(e)}")
            return None
    
    def start_transcription_job(self, job_name, s3_uri):
        """
        启动AWS Transcribe转录任务
        
        Args:
            job_name: 转录任务名称
            s3_uri: S3音频文件URI
            
        Returns:
            bool: 是否成功启动任务
        """
        try:
            logger.info(f"启动转录任务: {job_name}")
            
            # 启动转录任务，设置为墨西哥西班牙语（使用美国西班牙语识别）
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': s3_uri},
                MediaFormat='mp3',
                LanguageCode='es-US',  # 美国西班牙语
                Settings={
                    'ShowSpeakerLabels': True,  # 显示说话人标签
                    'MaxSpeakerLabels': 10,     # 最多10个说话人
                    'ChannelIdentification': True  # 启用声道识别
                }
            )
            
            logger.info(f"转录任务已启动: {job_name}")
            return True
            
        except Exception as e:
            logger.error(f"启动转录任务失败: {str(e)}")
            return False
    
    def wait_for_transcription_completion(self, job_name, max_wait_time=1800):
        """
        等待转录任务完成
        
        Args:
            job_name: 转录任务名称
            max_wait_time: 最大等待时间（秒），默认30分钟
            
        Returns:
            dict: 转录结果，如果失败返回None
        """
        logger.info(f"等待转录任务完成: {job_name}")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    logger.info(f"转录任务完成: {job_name}")
                    return response['TranscriptionJob']
                elif status == 'FAILED':
                    logger.error(f"转录任务失败: {job_name}")
                    return None
                else:
                    logger.info(f"转录任务状态: {status}, 继续等待...")
                    time.sleep(30)  # 等待30秒后再次检查
                    
            except Exception as e:
                logger.error(f"检查转录任务状态失败: {str(e)}")
                return None
        
        logger.error(f"转录任务超时: {job_name}")
        return None
    
    def download_transcript(self, transcript_uri):
        """
        下载转录结果
        
        Args:
            transcript_uri: 转录结果URI
            
        Returns:
            dict: 转录结果JSON，如果失败返回None
        """
        try:
            logger.info(f"下载转录结果: {transcript_uri}")
            
            response = requests.get(transcript_uri)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"下载转录结果失败: {str(e)}")
            return None
    
    def save_transcript(self, transcript_data, output_file):
        """
        保存转录结果到文件
        
        Args:
            transcript_data: 转录结果数据
            output_file: 输出文件路径
        """
        try:
            # 提取转录文本
            transcript_text = transcript_data['results']['transcripts'][0]['transcript']
            
            # 提取说话人信息（如果有）
            speaker_segments = []
            if 'speaker_labels' in transcript_data['results']:
                for segment in transcript_data['results']['speaker_labels']['segments']:
                    speaker_segments.append({
                        'speaker': segment['speaker_label'],
                        'start_time': segment['start_time'],
                        'end_time': segment['end_time'],
                        'items': segment['items']
                    })
            
            # 保存结果
            result = {
                'transcript': transcript_text,
                'speaker_segments': speaker_segments,
                'full_result': transcript_data
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"转录结果已保存: {output_file}")
            
            # 同时保存纯文本版本
            text_file = output_file.with_suffix('.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            logger.info(f"纯文本已保存: {text_file}")
            
        except Exception as e:
            logger.error(f"保存转录结果失败: {str(e)}")
    def process_csv_file(self, csv_file, s3_bucket, audio_column='通话录音', limit=None):
        """
        处理CSV文件中的音频URL
        
        Args:
            csv_file: CSV文件路径
            s3_bucket: S3存储桶名称
            audio_column: 音频URL列名，默认为'通话录音'
            limit: 处理的最大行数，None表示处理所有行
        """
        try:
            # 读取CSV文件
            logger.info(f"读取CSV文件: {csv_file}")
            df = pd.read_csv(csv_file)
            
            if audio_column not in df.columns:
                logger.error(f"CSV文件中未找到列: {audio_column}")
                return
            
            # 过滤有效的URL
            valid_urls = df[df[audio_column].notna() & (df[audio_column] != '')]
            
            if limit:
                valid_urls = valid_urls.head(limit)
            
            logger.info(f"找到 {len(valid_urls)} 个有效的音频URL")
            
            # 处理每个音频文件
            for index, row in valid_urls.iterrows():
                try:
                    audio_url = row[audio_column]
                    logger.info(f"处理第 {index + 1} 个文件: {audio_url}")
                    
                    # 生成文件名
                    parsed_url = urlparse(audio_url)
                    file_extension = Path(parsed_url.path).suffix or '.mp3'
                    filename = f"audio_{index}_{int(time.time())}{file_extension}"
                    
                    # 下载音频文件
                    local_file_path = self.download_audio_file(audio_url, filename)
                    if not local_file_path:
                        continue
                    
                    # 上传到S3
                    s3_key = f"transcribe-audio/{filename}"
                    s3_uri = self.upload_to_s3(local_file_path, s3_bucket, s3_key)
                    if not s3_uri:
                        continue
                    
                    # 启动转录任务
                    job_name = f"transcribe-job-{index}-{int(time.time())}"
                    if not self.start_transcription_job(job_name, s3_uri):
                        continue
                    
                    # 等待转录完成
                    job_result = self.wait_for_transcription_completion(job_name)
                    if not job_result:
                        continue
                    
                    # 下载转录结果
                    transcript_uri = job_result['Transcript']['TranscriptFileUri']
                    transcript_data = self.download_transcript(transcript_uri)
                    if not transcript_data:
                        continue
                    
                    # 保存转录结果
                    output_file = self.transcripts_dir / f"transcript_{index}.json"
                    self.save_transcript(transcript_data, output_file)
                    
                    # 清理本地音频文件（可选）
                    # os.remove(local_file_path)
                    
                    logger.info(f"第 {index + 1} 个文件处理完成")
                    
                except Exception as e:
                    logger.error(f"处理第 {index + 1} 个文件时出错: {str(e)}")
                    continue
            
            logger.info("所有文件处理完成")
            
        except Exception as e:
            logger.error(f"处理CSV文件失败: {str(e)}")


def main():
    """
    主函数
    """
    # 配置参数
    CSV_FILE = 'call.csv'  # CSV文件路径
    S3_BUCKET = 'your-transcribe-bucket'  # 替换为你的S3存储桶名称
    AWS_REGION = 'us-east-1'  # AWS区域
    LIMIT = 5  # 限制处理的文件数量，用于测试。设置为None处理所有文件
    
    # 检查AWS凭证
    try:
        boto3.Session().get_credentials()
        logger.info("AWS凭证验证成功")
    except Exception as e:
        logger.error(f"AWS凭证验证失败: {str(e)}")
        logger.error("请确保已配置AWS凭证（通过AWS CLI、环境变量或IAM角色）")
        return
    
    # 检查CSV文件是否存在
    if not os.path.exists(CSV_FILE):
        logger.error(f"CSV文件不存在: {CSV_FILE}")
        return
    
    # 创建转录器实例
    transcriber = AudioTranscriber(aws_region=AWS_REGION)
    
    # 处理CSV文件
    transcriber.process_csv_file(
        csv_file=CSV_FILE,
        s3_bucket=S3_BUCKET,
        limit=LIMIT
    )


if __name__ == "__main__":
    main()