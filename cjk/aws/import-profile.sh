#!/bin/bash
mv *.csv /root/cjk/aws/aws_profiles.csv

CSV_FILE="aws_profiles.csv"

# 跳过第一行（表头）
tail -n +2 "$CSV_FILE" | while IFS=',' read -r  access_key secret_key 
do
  echo "正在配置 profile: default"
  aws configure set aws_access_key_id "$access_key" --profile "default"
  aws configure set aws_secret_access_key "$secret_key" --profile "default"
  aws configure set region "us-east-1" --profile "default"
  aws configure set output json --profile "default"
done

echo "✅ 所有配置已导入完毕。"

