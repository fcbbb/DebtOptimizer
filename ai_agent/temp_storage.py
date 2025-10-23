import base64
import uuid
from typing import Dict, Optional

# 存储临时图片数据的字典
_temp_images: Dict[str, bytes] = {}

def save_temp_image(image_id: str, image_bytes: bytes) -> None:
    """
    保存临时图片数据
    
    Args:
        image_id (str): 图片唯一标识符
        image_bytes (bytes): 图片二进制数据
    """
    _temp_images[image_id] = image_bytes

def get_temp_image(image_id: str) -> Optional[bytes]:
    """
    获取临时图片数据
    
    Args:
        image_id (str): 图片唯一标识符
        
    Returns:
        Optional[bytes]: 图片二进制数据，如果不存在则返回None
    """
    return _temp_images.get(image_id)

def delete_temp_image(image_id: str) -> bool:
    """
    删除临时图片数据
    
    Args:
        image_id (str): 图片唯一标识符
        
    Returns:
        bool: 删除成功返回True，否则返回False
    """
    if image_id in _temp_images:
        del _temp_images[image_id]
        return True
    return False