#!/usr/bin/env python3
"""
AWS Transcribe 输出格式示例
展示说话人识别和声道识别的结果格式
"""

# 这是AWS Transcribe返回的典型JSON结构示例
example_transcript_with_speakers = {
    "results": {
        "transcripts": [
            {
                "transcript": "Hola buenos días señor Jonathan gracias por tomar la llamada me presento soy asesora de la financiera Hola Fina este es un recordatorio de pago por cuatrocientos diez pesos para el día de hoy cómo lo estaría haciendo señor en transferencia o en efectivo"
            }
        ],
        "speaker_labels": {
            "speakers": 2,
            "segments": [
                {
                    "start_time": "0.0",
                    "speaker_label": "spk_0",
                    "end_time": "15.23",
                    "items": [
                        {
                            "start_time": "0.0",
                            "speaker_label": "spk_0",
                            "end_time": "0.45",
                            "alternatives": [{"content": "Hola"}]
                        },
                        {
                            "start_time": "0.45",
                            "speaker_label": "spk_0", 
                            "end_time": "0.89",
                            "alternatives": [{"content": "buenos"}]
                        }
                        # ... 更多单词
                    ]
                },
                {
                    "start_time": "15.5",
                    "speaker_label": "spk_1",
                    "end_time": "18.2",
                    "items": [
                        {
                            "start_time": "15.5",
                            "speaker_label": "spk_1",
                            "end_time": "16.1",
                            "alternatives": [{"content": "De"}]
                        }
                        # ... 更多单词
                    ]
                }
            ]
        },
        "channel_labels": {
            "channels": [
                {
                    "channel_label": "ch_0",
                    "items": [
                        {
                            "start_time": "0.0",
                            "end_time": "0.45",
                            "alternatives": [{"content": "Hola"}],
                            "type": "pronunciation"
                        }
                        # ... 更多单词
                    ]
                },
                {
                    "channel_label": "ch_1", 
                    "items": [
                        {
                            "start_time": "15.5",
                            "end_time": "16.1", 
                            "alternatives": [{"content": "De"}],
                            "type": "pronunciation"
                        }
                        # ... 更多单词
                    ]
                }
            ]
        }
    }
}

def print_example_output():
    """打印示例输出格式"""
    
    print("=== AWS Transcribe 可以识别的信息 ===\n")
    
    print("1. 完整转录文本:")
    print("Hola buenos días señor Jonathan gracias por tomar la llamada...")
    print()
    
    print("2. 按说话人分段 (Speaker Labels):")
    print("spk_0 [00:00.00 - 00:15.23]: Hola buenos días señor Jonathan gracias por tomar la llamada me presento soy asesora de la financiera...")
    print("spk_1 [00:15.50 - 00:18.20]: De hecho yo les escribí ahí en la aplicación porque para hacer transferencias...")
    print("spk_0 [00:18.50 - 00:25.10]: Claro una clave yo le voy a mandar la clave interbancaria...")
    print()
    
    print("3. 按声道分段 (Channel Labels):")
    print("=== 声道 0 (左声道 - 通常是客服) ===")
    print("[00:00.00] Hola")
    print("[00:00.45] buenos")
    print("[00:00.89] días")
    print("...")
    print()
    print("=== 声道 1 (右声道 - 通常是客户) ===") 
    print("[00:15.50] De")
    print("[00:15.80] hecho")
    print("...")
    print()
    
    print("4. 我们的脚本输出格式:")
    print("transcript_X.json - 包含完整的JSON数据")
    print("transcript_X.txt - 格式化的文本，包含:")
    print("  - 完整转录文本")
    print("  - 按说话人/时间分段的对话")
    print("  - 时间戳信息")
    print()
    
    print("=== 实际使用场景 ===")
    print("• 电话录音: 声道0=客服, 声道1=客户")
    print("• 会议录音: spk_0, spk_1, spk_2... 代表不同参与者")
    print("• 多人对话: 最多可识别10个不同说话人")
    print("• 时间精度: 精确到0.01秒")

if __name__ == "__main__":
    print_example_output()