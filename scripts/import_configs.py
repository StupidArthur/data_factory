"""
批量导入配置文件到数据库
"""

import yaml
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webserver.models import Config

def import_configs(config_dir='config', group_id=None):
    """
    批量导入配置文件到数据库
    
    Args:
        config_dir: 配置文件目录
        group_id: 分组ID（可选）
    """
    # 连接数据库
    engine = create_engine('sqlite:///webserver/database.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        config_path = Path(config_dir)
        yaml_files = list(config_path.glob('*.yaml')) + list(config_path.glob('*.yml'))
        
        for yaml_file in yaml_files:
            # 读取YAML文件
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config_yaml = f.read()
            
            # 配置名称（使用文件名，去掉扩展名）
            config_name = yaml_file.stem
            
            # 检查是否已存在
            existing = session.query(Config).filter(Config.name == config_name).first()
            if existing:
                print(f"配置 {config_name} 已存在，跳过")
                continue
            
            # 创建配置
            config = Config(
                name=config_name,
                description=f'从文件导入：{yaml_file.name}',
                config_yaml=config_yaml,
                group_id=group_id,
                user=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(config)
            print(f"导入配置：{config_name}")
        
        session.commit()
        print("批量导入完成")
    except Exception as e:
        session.rollback()
        print(f"导入失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    # 导入config目录下的所有YAML文件
    import_configs('config', group_id=None)

