from typing import Union, List
from collections import OrderedDict
from .core.CacheEngineAbstract import CacheEngineAbstract
import sys, time, inspect

def singleton(cls):
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

@singleton
class Cache:
    
    __max_size    = None
    __default_ttl = None
    __cache_data  = OrderedDict()
    __engine      = None
    
    def __init__(self, forever_engine: CacheEngineAbstract = None, max_size = None, ttl = None):
        if forever_engine:
            self.__engine = forever_engine() if inspect.isclass(forever_engine) else forever_engine
        if max_size is not None and max_size > 0:
            self.setMaxMemoryUsage(max_size)
        if ttl is not None and ttl > 0:
            self.setDefaultTTL(ttl)
    
    def setMaxMemoryUsage(self, max_size):
        """
        设置最大缓存大小
        
        Args:
            max_size: 最大缓存大小，单位为 MB
        """
        self.__max_size = (max_size * 1024 * 1024) if max_size is not None else None
        return self
    
    def setDefaultTTL(self, ttl: int):
        """
        设置默认缓存过期时间
        
        Args:
            ttl: 缓存过期时间，单位为秒
        """
        self.__default_ttl = ttl if ttl is not None else None
        return self
    
    def set(self, key: str, value, ttl: int = 0, tags: Union[str, List[str]] = None):
        """
        设置缓存
        
        Args:
            key (str)         : 缓存键
            value (any)       : 缓存值
            ttl (int)         : 缓存过期时间，单位为秒, 0 表示永不过期
            tags (str or list): 缓存标签
            
        Returns:
            any: 缓存值
        """
        # 缓存值为 None 则不缓存并直接返回 None
        if value is None:
            return None
        
        # 内存超限清理
        if self.__max_size is not None and (sys.getsizeof(self.__cache_data) / 1024 ** 2) >= self.__max_size:
            clear_size = 0
            over_size  = sys.getsizeof(self.__cache_data) - self.__max_size - sys.getsizeof(value)
            for k in self.__cache_data:
                clear_size += sys.getsizeof(self.__cache_data[k])
                del self.__cache_data[k]
                if clear_size >= over_size:
                    break
        
        if ttl is None or ttl == 0:
            ttl = (int(time.time()) + self.__default_ttl) if (self.__default_ttl is not None and self.__default_ttl > 0) else None
        else:
            ttl = (int(time.time()) + ttl) if ttl > 0 else None
            
        self.__cache_data[key] = {
            'data': value,
            'tags': [tags] if isinstance(tags, str) else tags if tags is not None else [],
            'ttl' : ttl,
        }
        
        # 持久化缓存
        if isinstance(self.__engine, CacheEngineAbstract):
            self.__engine.set(key, self.__cache_data[key])
        
        return self.__cache_data[key]['data']
    
    def add(self, key: str, value, ttl: int = 0, tags: Union[str, List[str]] = None):
        """
        设置缓存
        
            set 别名
            
            Args:
                key (str)         : 缓存 Key
                value (any)       : 缓存 Value
                ttl (int)         : 缓存时间, 单位: 秒, 0 表示永不过期
                tags (str or list): 缓存标签
        """
        return self.set(key, value, ttl, tags)
        
    def get(self, key: str, default = None):
        """
        获取缓存
        
        Args:
            key (str): 缓存键
            default (any, optional): 无数据返回的默认值. Defaults to None.
            
        Returns:
            any: 缓存值
        """
        if key not in self.__cache_data and self.__engine:
            self.__cache_data[key] = self.__engine.get(key, default)
        if key in self.__cache_data:
            if 'ttl' in self.__cache_data[key] and self.__cache_data[key]['ttl'] is not None and self.__cache_data[key]['ttl'] < int(time.time()):
                self.delete(key)
            else:
                return self.__cache_data[key]['data']
        return default
    
    def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key (str): 缓存键
        """
        if key in self.__cache_data:
            del self.__cache_data[key]
            if self.__engine:
                self.__engine.delete(key)
        return True
    
    def exists(self, key: str):
        return self.has(key)
    
    def has(self, key: str):
        """
        判断是否存在缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否存在缓存
        """
        value = self.get(key, None)
        return bool(value) if value != 0 else True
    
    def set_ttl(self, key, ttl: int):
        """
        设置缓存过期时间
        
        Args:
            key (str): 缓存键
            ttl (int): 缓存过期时间，单位为秒, 0 表示永不过期
            
        Returns:
            Cache: 缓存对象
        """
        self.get(key)
        if key in self.__cache_data:
            self.__cache_data[key]['ttl'] = (int(time.time()) + ttl) if ttl > 0 else None
        self.set(key, self.__cache_data[key])
        return self
    
    def get_ttl(self, key: str):
        """
        获取缓存剩余过期时间
        
        Args:
            key (str): 缓存键
            
        Returns:
            int | None: 缓存过期时间，单位为秒, -1 表示永不过期, None 表示无数据
        """
        self.get(key)
        if key in self.__cache_data:
            return (self.__cache_data[key]['ttl'] - int(time.time())) if (self.__cache_data[key]['ttl'] is not None and self.__cache_data[key]['ttl'] > 0) else -1
        return None
    
    def clear(self):
        """
        清空所有缓存
        """
        self.__cache_data.clear()
        self.__engine.clear()

    def delete_expired(self):
        """
        删除过期缓存
        """
        for key in list(self.__cache_data.keys()):
            if self.__cache_data[key]['ttl'] is not None and self.__cache_data[key]['ttl'] < int(time.time()):
                del self.__cache_data[key]
                self.__engine.delete(key)
        return self
    
    def set_tags(self, key: str, tags: Union[str, List[str]]):
        """
        设置缓存标签
        
        Args:
            key (str)         : 缓存键
            tags (str or list): 缓存标签
            
        Returns:
            Cache: 缓存对象
        """
        self.get(key)
        if key in self.__cache_data:
            self.__cache_data[key]['tags'] = [tags] if isinstance(tags, str) else tags
        self.__engine.set(key, self.__cache_data[key])
        return self
    
    def get_tags(self, tags: Union[str, List[str]]):
        """
        获取指定标签的缓存
        
        Args:
            tags (str or list): 缓存标签
            
        Returns:
            list: 缓存列表
        """
        tags = tags if type(tags) in [list, tuple] else [tags]
        ret = []
        for key in self.__cache_data:
            if tags is None or (isinstance(tags, list) and set(tags).intersection(set(self.__cache_data[key]['tags']))):
                ret.append(self.__cache_data[key]['data'])
        return ret
    
    def remember(self, key, value, ttl: int = 0, tags: Union[str, List[str]] = None):
        """
        缓存记忆，如果缓存不存在则设置缓存
        
        Args:
            key (str)         : 缓存键
            value (any)       : 缓存值
            ttl (int)         : 缓存过期时间，单位为秒, 0 表示永不过期
            tags (str or list): 缓存标签
            
        Returns:
            any: 缓存值
        """
        if not self.has(key):
            self.set(key, value, ttl, tags)
        return self.get(key)
    
    def get_keys(self):
        """
        获取所有缓存键
        
        Returns:
            list: 缓存键列表
        """
        return list(self.__cache_data.keys())
    
    def get_size(self):
        """
        获取当前内存中缓存大小
        
        Returns:
            int: 缓存大小，单位为字节
        """
        return sys.getsizeof(self.__cache_data)
    
    def get_count(self):
        """
        获取当前内存中缓存数量
        
        Returns:
            int: 缓存数量
        """
        return len(self.__cache_data)