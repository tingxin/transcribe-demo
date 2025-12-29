#!/usr/bin/env python3
"""
分批处理音频转录脚本
"""

import os
import time
from transcribe_audio import AudioTranscriber
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_batch(start_index, batch_size=50):
    """
    处理指定批次的记录
    
    Args:
        start_index: 开始索引
        batch_size: 批次大小
    """
    # 读取环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    CSV_FILE = os.getenv('CSV_FILE', 'call.csv')
    S3_BUCKET = os.getenv('S3_BUCKET')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    if not S3_BUCKET:
        logger.error("S3_BUCKET 环境变量未设置")
        return
    
    # 读取CSV文件
    df = pd.read_csv(CSV_FILE)
    audio_column = '通话录音'
    
    if audio_column not in df.columns:
        logger.error(f"CSV文件中未找到列: {audio_column}")
        return
    
    # 过滤有效的URL
    valid_urls = df[df[audio_column].notna() & (df[audio_column] != '')]
    total_records = len(valid_urls)
    
    logger.info(f"总共有 {total_records} 条有效记录")
    
    # 计算批次范围
    end_index = min(start_index + batch_size, total_records)
    batch_data = valid_urls.iloc[start_index:end_index]
    
    logger.info(f"处理批次: {start_index+1} 到 {end_index} (共 {len(batch_data)} 条)")
    
    # 创建转录器
    transcriber = AudioTranscriber(aws_region=AWS_REGION)
    
    # 处理批次数据
    success_count = 0
    for idx, (original_index, row) in enumerate(batch_data.iterrows()):
        try:
            audio_url = row[audio_column]
            logger.info(f"处理第 {start_index + idx + 1} 条记录 (原始索引: {original_index}): {audio_url}")
            
            # 下载音频文件
            local_file_path = transcriber.download_audio_file(audio_url)
            if not local_file_path:
                logger.warning(f"跳过第 {original_index} 条记录：下载失败")
                continue
            
            # 上传到S3
            from pathlib import Path
            filename = Path(local_file_path).name
            s3_key = f"{S3_FOLDER_PREFIX}audio/{filename}" if S3_FOLDER_PREFIX else f"transcribe-audio/{filename}"
            s3_uri = transcriber.upload_to_s3(local_file_path, S3_BUCKET, s3_key)
            if not s3_uri:
                logger.warning(f"跳过第 {original_index} 条记录：S3上传失败")
                continue
            
            # 启动转录任务
            job_name = f"transcribe-job-{original_index}-{int(time.time())}"
            if not transcriber.start_transcription_job(job_name, s3_uri):
                logger.warning(f"跳过第 {original_index} 条记录：转录任务启动失败")
                continue
            
            # 等待转录完成
            job_result = transcriber.wait_for_transcription_completion(job_name)
            if not job_result:
                logger.warning(f"跳过第 {original_index} 条记录：转录任务失败")
                continue
            
            # 下载转录结果
            transcript_uri = job_result['Transcript']['TranscriptFileUri']
            transcript_data = transcriber.download_transcript(transcript_uri)
            if not transcript_data:
                logger.warning(f"跳过第 {original_index} 条记录：转录结果下载失败")
                continue
            
            # 保存转录结果
            output_file = transcriber.transcripts_dir / f"transcript_{original_index}.json"
            transcriber.save_transcript(transcript_data, output_file)
            
            success_count += 1
            logger.info(f"第 {original_index} 条记录处理完成")
            
            # 添加延迟避免API限制
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"处理第 {original_index} 条记录时出错: {str(e)}")
            continue
    
    logger.info(f"批次处理完成: 成功 {success_count}/{len(batch_data)} 条记录")
    return success_count

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("用法: python batch_process.py <开始索引> <批次大小>")
        print("示例: python batch_process.py 0 50")
        sys.exit(1)
    
    start_index = int(sys.argv[1])
    batch_size = int(sys.argv[2])
    
    process_batch(start_index, batch_size)