from abc import ABC, abstractmethod
from typing import Union, List
from collections import OrderedDict
import os, sys, pickle, hashlib, time, shutil

def singleton(cls):
    instances = {}
    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance

@singleton
class Cache(ABC):
    
    __max_size    = None
    __cache_dir   = None
    __default_ttl = None
    __cache_data  = OrderedDict()
    
    def setDiskCache(self, cache_dir = None):
        """
        开启持久化缓存
        
        Args:
            cache_dir: 缓存目录，默认使用用户目录下的 .xin_cache/
        """
        self.__cache_dir = cache_dir if cache_dir is not None else (os.path.expanduser("~") + '/.xin_cache/')
        if os.path.exists(self.__cache_dir) == False:
            os.makedirs(self.__cache_dir, exist_ok=True)
        return self
    
    def setMaxSize(self, max_size):
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
    
    def setDiskCache(self, key: str):
        """
        写入持久化缓存
        
        Args:
            key (str): 缓存键
        """
        if self.__cache_dir is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            if os.path.exists(self.__cache_dir.rstrip('/') + '/' + str(filename[6:8])) == False:
                os.makedirs(self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(pickle.dumps(self.__cache_data[key]))
                
    def getDiskCache(self, key: str):
        """
        获取持久化缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            any: 缓存值
        """
        ret = None
        if self.hasDiskCache(key):
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            with open(filepath, 'rb') as f:
                ret = pickle.loads(f.read())
        return ret
        
    def hasDiskCache(self, key: str):
        """
        判断是否存在持久化缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否存在持久化缓存
        """
        if self.__cache_dir is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            return os.path.exists(filepath)
        return False
    
    def deleteDiskCache(self, key: str):
        """
        删除持久化缓存
        
        Args:
            key (str): 缓存键
        """
        if self.__cache_dir is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            if os.path.exists(filepath):
                os.remove(filepath)
    
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
        if self.__max_size is not None and (sys.getsizeof(self.__cache_dir) / 1024 ** 2) >= self.__max_size:
            clear_size = 0
            over_size  = sys.getsizeof(self.__cache_dir) - self.__max_size - sys.getsizeof(value)
            for k in self.__cache_data:
                clear_size += sys.getsizeof(self.__cache_data[k])
                del self.__cache_data[k]
                if clear_size >= over_size:
                    break
        
        if ttl is None:
            ttl = (int(time.time()) + self.__default_ttl) if (self.__default_ttl is not None and self.__default_ttl > 0) else None
        else:
            ttl = (int(time.time()) + ttl) if ttl > 0 else None
            
        self.__cache_data[key] = {
            'data': value,
            'tags': [tags] if isinstance(tags, str) else tags if tags is not None else [],
            'ttl' : ttl,
        }
        
        # 持久化缓存
        self.setDiskCache(key)
        
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
        if key not in self.__cache_data:
            self.__cache_data[key] = self.getDiskCache(key)
        if key in self.__cache_data:
            if self.__cache_data[key]['ttl'] is not None and self.__cache_data[key]['ttl'] < int(time.time()):
                del self.__cache_data[key]
                self.deleteDiskCache(key)
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
            self.deleteDiskCache(key)
        return True
    
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
        self.setDiskCache(key)
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
        if self.__cache_dir is not None:
            # 遍历文件夹中的所有文件和子文件夹
            for filename in os.listdir(self.__cache_data):
                file_path = os.path.join(self.__cache_data, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'{file_path} 缓存文件删除失败: {e}')

    def delete_expired(self):
        """
        删除过期缓存
        """
        for key in list(self.__cache_data.keys()):
            if self.__cache_data[key]['ttl'] is not None and self.__cache_data[key]['ttl'] < int(time.time()):
                del self.__cache_data[key]
                self.deleteDiskCache(key)
        return self
    
    def get_tags(self, tags: Union[str, List[str]]):
        """
        获取指定标签的缓存
        
        Args:
            tags (str or list): 缓存标签
            
        Returns:
            list: 缓存列表
        """
        ret = []
        for key in self.__cache_data:
            if tags is None or (isinstance(tags, list) and set(tags).intersection(set(self.__cache_data[key]['tags']))):
                ret.append(self.__cache_data[key]['data'])
        return ret
    
    def get_keys(self):
        """
        获取所有缓存键
        
        Returns:
            list: 缓存键列表
        """
        return list(self.__cache_data.keys())
    
    def get_size(self):
        """
        获取缓存大小
        
        Returns:
            int: 缓存大小，单位为字节
        """
        return sys.getsizeof(self.__cache_data)
    
    def get_count(self):
        """
        获取缓存数量
        
        Returns:
            int: 缓存数量
        """
        return len(self.__cache_data)