"""自定义异常层次。"""


class PIMException(Exception):
    """个人信息管理器基础异常。"""
    pass


class DataLoadError(PIMException):
    """数据加载失败。"""
    pass


class DataSaveError(PIMException):
    """数据保存失败。"""
    pass


class RecordNotFoundError(PIMException):
    """记录未找到。"""
    pass


class ValidationError(PIMException):
    """数据校验失败。"""
    pass


class BackupError(PIMException):
    """备份/恢复操作失败。"""
    pass
