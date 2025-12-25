#!/usr/bin/env python3
"""
简化版音频转录测试脚本（带标签功能）
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

def get_speaker_name(speaker_label):
    """
    将说话人标签转换为更友好的名称
    """
    speaker_0_label = os.getenv('SPEAKER_0_LABEL', '客服')
    speaker_1_label = os.getenv('SPEAKER_1_LABEL', '客户')
    
    speaker_mapping = {
        'spk_0': f'[{speaker_0_label}]',
        'spk_1': f'[{speaker_1_label}]', 
        'spk_2': '[说话人3]',
        'spk_3': '[说话人4]',
        'spk_4': '[说话人5]'
    }
    return speaker_mapping.get(speaker_label, f'[{speaker_label}]')

def get_channel_name(channel_label):
    """
    将声道标签转换为更友好的名称
    """
    channel_mapping = {
        'ch_0': '[声道1-客服]',
        'ch_1': '[声道2-客户]',
        'ch_2': '[声道3]',
        'ch_3': '[声道4]'
    }
    return channel_mapping.get(channel_label, f'[{channel_label}]')

def create_labeled_transcript(transcript_data):
    """
    创建带标签的转录文本，清晰标记每段话的说话人
    """
    try:
        labeled_lines = []
        
        # 获取results数据 - 处理嵌套结构
        if 'full_result' in transcript_data:
            full_data = transcript_data['full_result']
        else:
            full_data = transcript_data
        
        results_data = full_data.get('results', {})
        
        # 处理results可能是列表的情况
        if isinstance(results_data, list) and len(results_data) > 0:
            results_data = results_data[0]
        
        logger.info(f"数据结构检查: results类型={type(results_data)}")
        if isinstance(results_data, dict):
            logger.info(f"results键: {list(results_data.keys())}")
        
        # 方法1: 尝试使用说话人标签
        if isinstance(results_data, dict) and 'speaker_labels' in results_data:
            logger.info("使用说话人标签进行分段")
            speaker_labels = results_data['speaker_labels']
            
            if isinstance(speaker_labels, dict) and 'segments' in speaker_labels:
                segments = speaker_labels['segments']
                logger.info(f"找到 {len(segments)} 个说话人片段")
                
                for i, segment in enumerate(segments):
                    speaker_label = segment.get('speaker_label', f'unknown_{i}')
                    speaker_name = get_speaker_name(speaker_label)
                    
                    # 获取这个时间段的文本
                    segment_text = ""
                    if 'items' in segment:
                        for item in segment['items']:
                            if isinstance(item, dict) and 'alternatives' in item:
                                if len(item['alternatives']) > 0:
                                    content = item['alternatives'][0].get('content', '')
                                    if item.get('type') == 'punctuation':
                                        segment_text = segment_text.rstrip() + content + " "
                                    else:
                                        segment_text += content + " "
                    
                    if segment_text.strip():
                        labeled_lines.append(f"{speaker_name}: {segment_text.strip()}")
        
        # 方法2: 尝试使用声道标签
        elif isinstance(results_data, dict) and 'channel_labels' in results_data:
            logger.info("使用声道标签进行分段")
            channel_labels = results_data['channel_labels']
            
            if isinstance(channel_labels, dict) and 'channels' in channel_labels:
                channels = channel_labels['channels']
                logger.info(f"找到 {len(channels)} 个声道")
                
                # 收集所有带时间戳的词汇
                all_items = []
                for channel in channels:
                    channel_label = channel.get('channel_label', 'unknown')
                    channel_name = get_channel_name(channel_label)
                    
                    if 'items' in channel:
                        for item in channel['items']:
                            if (isinstance(item, dict) and 
                                item.get('type') == 'pronunciation' and 
                                'start_time' in item and 
                                'alternatives' in item and
                                len(item['alternatives']) > 0):
                                
                                all_items.append({
                                    'start_time': float(item['start_time']),
                                    'content': item['alternatives'][0].get('content', ''),
                                    'channel': channel_name
                                })
                
                logger.info(f"收集到 {len(all_items)} 个词汇项目")
                
                if all_items:
                    # 按时间排序
                    all_items.sort(key=lambda x: x['start_time'])
                    
                    # 按声道分组连续的文本
                    current_channel = None
                    current_text = ""
                    
                    for item in all_items:
                        if item['channel'] != current_channel:
                            # 保存前一个声道的文本
                            if current_text.strip():
                                labeled_lines.append(f"{current_channel}: {current_text.strip()}")
                            
                            # 开始新的声道
                            current_channel = item['channel']
                            current_text = item['content'] + " "
                        else:
                            current_text += item['content'] + " "
                    
                    # 保存最后一个声道的文本
                    if current_text.strip():
                        labeled_lines.append(f"{current_channel}: {current_text.strip()}")
        
        # 方法3: 如果都没有，尝试从原始转录文本创建简单标签
        if not labeled_lines:
            logger.info("未找到说话人或声道标签，尝试简单分段")
            
            # 获取原始转录文本
            original_text = ""
            if 'transcript' in transcript_data:
                original_text = transcript_data['transcript']
            elif isinstance(results_data, dict) and 'transcripts' in results_data:
                transcripts = results_data['transcripts']
                if len(transcripts) > 0:
                    original_text = transcripts[0].get('transcript', '')
            
            if original_text:
                # 简单的句子分割 - 按句号、问号、感叹号分割
                import re
                sentences = re.split(r'[.!?。！？]+', original_text)
                
                # 交替分配给两个说话人
                for i, sentence in enumerate(sentences):
                    sentence = sentence.strip()
                    if sentence:
                        speaker = get_speaker_name('spk_0') if i % 2 == 0 else get_speaker_name('spk_1')
                        labeled_lines.append(f"{speaker}: {sentence}")
            
            if not labeled_lines:
                labeled_lines.append(f"[未识别说话人]: {original_text}")
        
        result = "\n\n".join(labeled_lines)
        logger.info(f"最终生成 {len(labeled_lines)} 个标签片段")
        return result
        
    except Exception as e:
        logger.error(f"创建带标签转录失败: {str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        
        # 返回原始文本作为备选
        try:
            if 'transcript' in transcript_data:
                return f"[处理错误]: {transcript_data['transcript']}"
            else:
                return "[转录处理失败: 无法获取文本]"
        except:
            return "[转录处理完全失败]"

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
                
                # 创建带标签的转录文本
                labeled_transcript = create_labeled_transcript(transcript_data)
                
                # 提取说话人信息
                speaker_segments = []
                try:
                    # 处理results可能是列表的情况
                    results_data = transcript_data['results']
                    if isinstance(results_data, list) and len(results_data) > 0:
                        results_data = results_data[0]
                    
                    if 'speaker_labels' in results_data and 'segments' in results_data['speaker_labels']:
                        for segment in results_data['speaker_labels']['segments']:
                            speaker_segments.append({
                                'speaker': segment['speaker_label'],
                                'start_time': segment['start_time'],
                                'end_time': segment['end_time'],
                                'items': segment.get('items', [])
                            })
                        logger.info(f"提取了 {len(speaker_segments)} 个说话人片段")
                    else:
                        logger.info("未找到说话人片段信息")
                except Exception as e:
                    logger.error(f"提取说话人信息失败: {str(e)}")
                
                # 获取原始转录文本
                try:
                    results_data = transcript_data['results']
                    if isinstance(results_data, list) and len(results_data) > 0:
                        results_data = results_data[0]
                    transcript_text = results_data['transcripts'][0]['transcript']
                except Exception as e:
                    logger.error(f"获取原始转录文本失败: {str(e)}")
                    transcript_text = "[无法获取原始转录文本]"
                
                # 保存完整JSON结果（包含带标签转录）
                complete_result = {
                    'transcript': transcript_text,
                    'labeled_transcript': labeled_transcript,
                    'speaker_segments': speaker_segments,
                    'full_result': transcript_data
                }
                
                with open(result_dir / 'test_transcript.json', 'w', encoding='utf-8') as f:
                    json.dump(complete_result, f, ensure_ascii=False, indent=2)
                
                # 保存格式化的文本结果
                with open(result_dir / 'test_transcript.txt', 'w', encoding='utf-8') as f:
                    f.write("=== 带标签的转录文本（推荐用于分析） ===\n")
                    f.write(labeled_transcript + "\n\n")
                    
                    f.write("=== 原始完整转录文本 ===\n")
                    f.write(transcript_text + "\n\n")
                    
                    # 添加说话人分段信息（带时间戳）
                    if speaker_segments:
                        f.write("=== 按说话人分段（详细时间） ===\n")
                        for segment in speaker_segments:
                            start_time = float(segment['start_time'])
                            end_time = float(segment['end_time'])
                            
                            # 格式化时间
                            start_min = int(start_time // 60)
                            start_sec = start_time % 60
                            end_min = int(end_time // 60)
                            end_sec = end_time % 60
                            
                            time_str = f"[{start_min:02d}:{start_sec:05.2f} - {end_min:02d}:{end_sec:05.2f}]"
                            
                            # 获取这个时间段的文本
                            segment_text = ""
                            for item in segment['items']:
                                if 'alternatives' in item and len(item['alternatives']) > 0:
                                    segment_text += item['alternatives'][0]['content'] + " "
                            
                            # 使用友好的说话人名称
                            speaker_name = get_speaker_name(segment['speaker'])
                            f.write(f"{speaker_name} {time_str}: {segment_text.strip()}\n")
                
                logger.info("转录完成！")
                logger.info("=== 带标签的转录预览 ===")
                # 显示前200个字符的带标签转录
                preview = labeled_transcript[:200] + "..." if len(labeled_transcript) > 200 else labeled_transcript
                logger.info(f"{preview}")
                logger.info(f"完整结果保存在: {result_dir}")
                logger.info(f"  - test_transcript.json: 完整JSON数据")
                logger.info(f"  - test_transcript.txt: 格式化文本（包含标签）")
                
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