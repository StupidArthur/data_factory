"""
数据库模型定义

使用SQLAlchemy定义配置存储的数据模型。
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent / 'database.db'
DATABASE_URL = f'sqlite:///{DB_PATH}'

# 创建数据库引擎
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ConfigGroup(Base):
    """
    配置分组模型
    
    存储配置分组信息。
    """
    __tablename__ = 'config_groups'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, comment='分组名称')
    description = Column(Text, comment='分组描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联配置
    configs = relationship('Config', back_populates='group', cascade='all, delete-orphan')
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            分组字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'config_count': len(self.configs) if self.configs else 0
        }


class Config(Base):
    """
    配置模型
    
    存储数据生成的YAML配置。
    """
    __tablename__ = 'configs'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment='配置名称')
    description = Column(Text, comment='配置描述')
    config_yaml = Column(Text, nullable=False, comment='YAML配置内容')
    group_id = Column(Integer, ForeignKey('config_groups.id'), nullable=True, comment='分组ID')
    user = Column(String(255), nullable=True, comment='配置用户')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联分组
    group = relationship('ConfigGroup', back_populates='configs')
    
    def to_dict(self):
        """
        转换为字典格式
        
        Returns:
            配置字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'config_yaml': self.config_yaml,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'user': self.user,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


def init_db():
    """
    初始化数据库
    
    创建所有表结构，并创建默认分组。
    """
    Base.metadata.create_all(bind=engine)
    
    # 创建默认分组（已删除）
    db = SessionLocal()
    try:
        # 检查是否已存在"已删除"分组
        deleted_group = db.query(ConfigGroup).filter(ConfigGroup.name == '已删除').first()
        if not deleted_group:
            deleted_group = ConfigGroup(name='已删除', description='已删除的配置分组')
            db.add(deleted_group)
            db.commit()
    finally:
        db.close()


def get_db():
    """
    获取数据库会话
    
    Yields:
        数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

