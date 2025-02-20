##### 导入Cache模块
``` from Cache import Cache ```

##### 导入持久化缓存的DiskCache模块, 该模块持久化为保存数据在磁盘文件中
``` from core.DiskCache import DiskCache ```

##### 实例化Cache对象, 使用DiskCache作为持久化缓存模式
``` xincache = Cache(DiskCache) ```

##### 也可以指定DiskCache的数据路径
``` xincache = Cache(DiskCache('/tmp/cache')) ```

##### 也可以不指定持久化缓存模式, 项目终止后缓存失效
``` xincache = Cache() ```

##### 设置缓存默认有效期, 单位: 秒, 不设置则使用默认值 None, 为永久缓存
``` xincache.setDefaultTTL(3600) ```

##### 设置缓存占用最大 RAM 空间, 单位: MB
``` xincache.setMaxMemoryUsage(100) ```

##### 设置缓存
``` xincache.set("key", "Cache Value") ```

##### 设置缓存并设置单独的过期时间, 单位: 秒
``` xincache.set("key", "Cache Value", 60) ```

##### 设置缓存并设定缓存标签
```python
xincache.set("key", "Cache Value", tags=["default", "shopping"]) 
xincache.set("key", "Cache Value", tags="default")
```

##### 单独设置缓存区过期时间, 单位: 秒
``` xincache.set_ttl("key", 60) ```

##### 单独设置缓存标签, 会覆盖原有标签
```python
xincache.set_tags("key", ["default", "shopping"])
xincache.set_tags("key", "default")
```

##### 获取缓存
``` xincache.get("key") ```

##### 获取缓存,如果缓存不存在,则返回默认值
``` xincache.get("key", "Default Value") ```

##### 删除缓存
``` xincache.delete("key") ```

##### 手动删除过期缓存
``` xincache.delete_expired() ```

##### 清空所有缓存
``` xincache.clear() ```

##### 获取缓存占用最大 RAM 空间, 单位: MB
``` xincache.get_size() ```

##### 获取缓存数量
``` xincache.get_count() ```

##### 获取缓存过期 TTL 时间, 单位: 秒
``` xincache.get_ttl("key") ```