#!/usr/bin/env python3
"""
修复标签功能的脚本
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_speaker_name(speaker_label):
    """将说话人标签转换为更友好的名称"""
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
    """将声道标签转换为更友好的名称"""
    channel_mapping = {
        'ch_0': '[声道1-客服]',
        'ch_1': '[声道2-客户]',
        'ch_2': '[声道3]',
        'ch_3': '[声道4]'
    }
    return channel_mapping.get(channel_label, f'[{channel_label}]')

def create_labeled_transcript_fixed(transcript_data):
    """
    修复版本的带标签转录创建函数
    """
    try:
        labeled_lines = []
        
        # 获取results数据
        if 'full_result' in transcript_data:
            full_data = transcript_data['full_result']
        else:
            full_data = transcript_data
        
        results_data = full_data.get('results', {})
        
        # 处理results可能是列表的情况
        if isinstance(results_data, list) and len(results_data) > 0:
            results_data = results_data[0]
        
        print(f"数据结构检查:")
        print(f"  results类型: {type(results_data)}")
        print(f"  results键: {list(results_data.keys()) if isinstance(results_data, dict) else '不是字典'}")
        
        # 方法1: 尝试使用说话人标签
        if isinstance(results_data, dict) and 'speaker_labels' in results_data:
            print("找到speaker_labels")
            speaker_labels = results_data['speaker_labels']
            
            if isinstance(speaker_labels, dict) and 'segments' in speaker_labels:
                segments = speaker_labels['segments']
                print(f"找到 {len(segments)} 个说话人片段")
                
                for i, segment in enumerate(segments):
                    print(f"处理片段 {i+1}: {segment}")
                    
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
                        print(f"添加片段: {speaker_name}: {segment_text.strip()[:50]}...")
        
        # 方法2: 尝试使用声道标签
        elif isinstance(results_data, dict) and 'channel_labels' in results_data:
            print("找到channel_labels")
            channel_labels = results_data['channel_labels']
            
            if isinstance(channel_labels, dict) and 'channels' in channel_labels:
                channels = channel_labels['channels']
                print(f"找到 {len(channels)} 个声道")
                
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
                                'alternatives' in item):
                                
                                all_items.append({
                                    'start_time': float(item['start_time']),
                                    'content': item['alternatives'][0].get('content', ''),
                                    'channel': channel_name,
                                    'type': item.get('type', 'pronunciation')
                                })
                
                print(f"收集到 {len(all_items)} 个词汇项目")
                
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
                            print(f"添加声道片段: {current_channel}: {current_text.strip()[:50]}...")
                        
                        # 开始新的声道
                        current_channel = item['channel']
                        current_text = item['content'] + " "
                    else:
                        current_text += item['content'] + " "
                
                # 保存最后一个声道的文本
                if current_text.strip():
                    labeled_lines.append(f"{current_channel}: {current_text.strip()}")
                    print(f"添加最后声道片段: {current_channel}: {current_text.strip()[:50]}...")
        
        # 方法3: 如果都没有，返回原始文本
        else:
            print("未找到说话人或声道标签，使用原始文本")
            if isinstance(results_data, dict) and 'transcripts' in results_data:
                transcripts = results_data['transcripts']
                if len(transcripts) > 0:
                    original_text = transcripts[0].get('transcript', '')
                    labeled_lines.append(f"[未识别说话人]: {original_text}")
            elif 'transcript' in transcript_data:
                # 从我们保存的数据中获取
                original_text = transcript_data['transcript']
                labeled_lines.append(f"[未识别说话人]: {original_text}")
        
        result = "\n\n".join(labeled_lines)
        print(f"最终生成 {len(labeled_lines)} 个标签片段")
        return result
        
    except Exception as e:
        print(f"创建带标签转录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 返回原始文本作为备选
        try:
            if 'transcript' in transcript_data:
                return f"[处理错误]: {transcript_data['transcript']}"
            else:
                return "[转录处理失败: 无法获取文本]"
        except:
            return "[转录处理完全失败]"

def fix_existing_transcript():
    """修复现有的转录文件"""
    
    json_file = Path('test_results/test_transcript.json')
    
    if not json_file.exists():
        print("未找到test_transcript.json文件")
        return
    
    try:
        # 读取现有文件
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("=== 修复转录标签 ===")
        
        # 创建新的带标签转录
        new_labeled_transcript = create_labeled_transcript_fixed(data)
        
        # 更新数据
        data['labeled_transcript'] = new_labeled_transcript
        
        # 保存更新后的JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 更新文本文件
        text_file = json_file.with_suffix('.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("=== 带标签的转录文本（推荐用于分析） ===\n")
            f.write(new_labeled_transcript + "\n\n")
            
            f.write("=== 原始完整转录文本 ===\n")
            f.write(data.get('transcript', '[无原始文本]') + "\n\n")
            
            # 添加说话人分段信息（带时间戳）
            speaker_segments = data.get('speaker_segments', [])
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
                    for item in segment.get('items', []):
                        if 'alternatives' in item and len(item['alternatives']) > 0:
                            segment_text += item['alternatives'][0]['content'] + " "
                    
                    # 使用友好的说话人名称
                    speaker_name = get_speaker_name(segment['speaker'])
                    f.write(f"{speaker_name} {time_str}: {segment_text.strip()}\n")
        
        print("修复完成！")
        print(f"新的带标签转录长度: {len(new_labeled_transcript)}")
        print("预览:")
        preview = new_labeled_transcript[:300] + "..." if len(new_labeled_transcript) > 300 else new_labeled_transcript
        print(preview)
        
    except Exception as e:
        print(f"修复失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_existing_transcript()