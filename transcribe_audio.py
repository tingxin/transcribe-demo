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
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
    
    def get_cached_filename(self, url):
        """
        根据URL生成缓存文件名
        
        Args:
            url: 音频文件URL
            
        Returns:
            str: 缓存文件名
        """
        import hashlib
        from urllib.parse import urlparse
        
        # 使用URL的hash作为文件名的一部分，确保唯一性
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        # 尝试从URL获取原始文件名和扩展名
        parsed_url = urlparse(url)
        original_filename = Path(parsed_url.path).name
        
        if original_filename and '.' in original_filename:
            name, ext = original_filename.rsplit('.', 1)
            return f"{name}_{url_hash}.{ext}"
        else:
            return f"audio_{url_hash}.mp3"
    
    def download_audio_file(self, url, filename=None):
        """
        下载音频文件，如果本地已存在则使用缓存
        
        Args:
            url: 音频文件URL
            filename: 本地保存的文件名，如果为None则自动生成
            
        Returns:
            str: 本地文件路径，如果下载失败返回None
        """
        try:
            # 如果没有指定文件名，则根据URL生成缓存文件名
            if filename is None:
                filename = self.get_cached_filename(url)
            
            file_path = self.audio_dir / filename
            
            # 检查文件是否已存在
            if file_path.exists():
                file_size = file_path.stat().st_size
                if file_size > 0:  # 确保文件不为空
                    logger.info(f"使用缓存文件: {file_path} (大小: {file_size} 字节)")
                    return str(file_path)
                else:
                    logger.warning(f"缓存文件为空，重新下载: {file_path}")
                    file_path.unlink()  # 删除空文件
            
            logger.info(f"正在下载: {url}")
            
            # 发送HTTP请求下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 验证下载的文件大小
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.error(f"下载的文件为空: {file_path}")
                file_path.unlink()  # 删除空文件
                return None
            
            logger.info(f"下载完成: {file_path} (大小: {file_size} 字节)")
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
    def clean_cache(self, max_age_days=7):
        """
        清理过期的缓存文件
        
        Args:
            max_age_days: 缓存文件的最大保留天数
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            cleaned_count = 0
            total_size = 0
            
            for file_path in self.audio_dir.glob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    file_size = file_path.stat().st_size
                    
                    if file_age > max_age_seconds:
                        total_size += file_size
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"删除过期缓存文件: {file_path}")
            
            if cleaned_count > 0:
                logger.info(f"清理完成: 删除了 {cleaned_count} 个文件，释放空间 {total_size / 1024 / 1024:.2f} MB")
            else:
                logger.info("没有需要清理的过期缓存文件")
                
        except Exception as e:
            logger.error(f"清理缓存失败: {str(e)}")
    
    def get_cache_info(self):
        """
        获取缓存信息
        
        Returns:
            dict: 缓存统计信息
        """
        try:
            file_count = 0
            total_size = 0
            
            for file_path in self.audio_dir.glob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
            
            return {
                'file_count': file_count,
                'total_size_mb': total_size / 1024 / 1024,
                'cache_dir': str(self.audio_dir)
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {str(e)}")
            return None
    def process_csv_file(self, csv_file, s3_bucket, s3_folder_prefix='', audio_column='通话录音', limit=None):
        """
        处理CSV文件中的音频URL
        
        Args:
            csv_file: CSV文件路径
            s3_bucket: S3存储桶名称
            s3_folder_prefix: S3文件夹前缀，例如 'my-project/audio-transcripts/'
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
                    
                    # 下载音频文件（使用缓存）
                    local_file_path = self.download_audio_file(audio_url)
                    if not local_file_path:
                        continue
                    
                    # 从本地文件路径获取文件名
                    filename = Path(local_file_path).name
                    
                    # 上传到S3（使用指定的文件夹前缀）
                    s3_key = f"{s3_folder_prefix}audio/{filename}" if s3_folder_prefix else f"transcribe-audio/{filename}"
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
    # 从环境变量读取配置参数
    CSV_FILE = os.getenv('CSV_FILE', 'call.csv')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    LIMIT = int(os.getenv('LIMIT', '5')) if os.getenv('LIMIT') else None
    
    # 验证必需的配置
    if not S3_BUCKET:
        logger.error("S3_BUCKET 环境变量未设置，请检查.env文件")
        return
    
    logger.info(f"配置信息:")
    logger.info(f"  CSV文件: {CSV_FILE}")
    logger.info(f"  S3桶: {S3_BUCKET}")
    logger.info(f"  S3文件夹前缀: {S3_FOLDER_PREFIX}")
    logger.info(f"  AWS区域: {AWS_REGION}")
    logger.info(f"  处理限制: {LIMIT if LIMIT else '无限制'}")
    
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
    
    # 显示缓存信息
    cache_info = transcriber.get_cache_info()
    if cache_info:
        logger.info(f"缓存信息: {cache_info['file_count']} 个文件, {cache_info['total_size_mb']:.2f} MB")
    
    # 可选：清理过期缓存（超过7天的文件）
    # transcriber.clean_cache(max_age_days=7)
    
    # 处理CSV文件
    transcriber.process_csv_file(
        csv_file=CSV_FILE,
        s3_bucket=S3_BUCKET,
        s3_folder_prefix=S3_FOLDER_PREFIX,
        limit=LIMIT
    )


if __name__ == "__main__":
    main()