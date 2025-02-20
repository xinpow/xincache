from .CacheEngineAbstract import CacheEngineAbstract
import os, pickle, hashlib, shutil

class DiskCache(CacheEngineAbstract):
    
    def __init__(self, cache_dir: str = None):
        """
        初始化文件缓存
        
        Args:
            cache_dir: 缓存目录，默认使用用户目录下的 .xin_cache/
        """
        self.__cache_dir = cache_dir if cache_dir is not None else (os.path.expanduser("~") + '/.xin_cache/')
        if os.path.exists(self.__cache_dir) == False:
            os.makedirs(self.__cache_dir, exist_ok=True)
    
    def set(self, key: str, value = None):
        """
        写入文件缓存
        
        Args:
            key (str): 缓存键
        """
        if self.__cache_dir is not None and value is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            if os.path.exists(self.__cache_dir.rstrip('/') + '/' + str(filename[6:8])) == False:
                os.makedirs(self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(pickle.dumps(value))
        return value
    
    def get(self, key: str, default = None):
        """
        获取文件缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            any: 缓存值
        """
        ret = default
        if self.has(key):
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            with open(filepath, 'rb') as f:
                ret = pickle.loads(f.read())
        return ret
    
    def has(self, key: str):
        """
        判断是否存在文件缓存
        
        Args:
            key (str): 缓存键
            
        Returns:
            bool: 是否存在文件缓存
        """
        if self.__cache_dir is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            return os.path.exists(filepath)
        return False
    
    def delete(self, key: str):
        """
        删除文件缓存
        
        Args:
            key (str): 缓存键
        """
        if self.__cache_dir is not None:
            filename = hashlib.md5(key.encode()).hexdigest()
            filepath = self.__cache_dir.rstrip('/') + '/' + str(filename[6:8]) + '/' + filename
            if os.path.exists(filepath):
                os.remove(filepath)
    
    def clear(self):
        """
        清空文件缓存
        """
        if self.__cache_dir is not None:
            # 遍历文件夹中的所有文件和子文件夹
            for filename in os.listdir(self.__cache_dir):
                file_path = os.path.join(self.__cache_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'{file_path} 缓存文件删除失败: {e}')