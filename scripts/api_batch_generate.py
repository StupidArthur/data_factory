"""
使用API批量生成数据
"""

import requests
import json
from pathlib import Path

API_BASE = 'http://localhost:8000'

def batch_generate_via_api(config_ids=None):
    """
    通过API批量生成数据
    
    Args:
        config_ids: 配置ID列表（如果为None，则使用所有配置）
    """
    # 获取配置列表
    if config_ids is None:
        try:
            response = requests.get(f'{API_BASE}/api/configs/')
            if response.status_code == 200:
                configs = response.json().get('data', [])
                config_ids = [c['id'] for c in configs]
            else:
                print(f"获取配置列表失败：{response.status_code}")
                return
        except Exception as e:
            print(f"连接API失败：{e}")
            print(f"请确保后端服务已启动：python webserver/app.py")
            return
    
    # 批量生成
    for config_id in config_ids:
        print(f"生成配置 {config_id} 的数据...")
        
        try:
            # 生成数据
            response = requests.post(f'{API_BASE}/api/generate/', json={
                'config_id': config_id
            })
            
            if response.status_code == 200:
                result = response.json()
                full_data = result.get('data', {}).get('full', [])
                print(f"  成功：共 {len(full_data)} 行数据")
            else:
                print(f"  失败：{response.status_code} - {response.text}")
                continue
            
            # 导出数据
            response = requests.get(f'{API_BASE}/api/export/{config_id}?type=full')
            if response.status_code == 200:
                output_file = f'output/config_{config_id}_full.csv'
                Path('output').mkdir(parents=True, exist_ok=True)
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"  数据已导出：{output_file}")
            
        except Exception as e:
            print(f"  处理失败：{e}")
            continue
    
    print("批量生成完成")

if __name__ == '__main__':
    # 生成所有配置的数据
    batch_generate_via_api()
    
    # 或指定配置ID
    # batch_generate_via_api([1, 2, 3])

