#!/bin/bash

# 分批处理所有记录的脚本
# 每批处理50条记录，总共1728条

BATCH_SIZE=50
TOTAL_RECORDS=1728

echo "开始分批处理 $TOTAL_RECORDS 条记录，每批 $BATCH_SIZE 条"

for ((i=0; i<TOTAL_RECORDS; i+=BATCH_SIZE)); do
    echo "处理批次: $((i+1)) 到 $((i+BATCH_SIZE))"
    python batch_process.py $i $BATCH_SIZE
    
    if [ $? -ne 0 ]; then
        echo "批次处理失败，停止执行"
        exit 1
    fi
    
    echo "批次完成，等待5秒..."
    sleep 5
done

echo "所有批次处理完成！"