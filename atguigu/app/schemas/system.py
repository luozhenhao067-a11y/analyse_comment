from typing import Any

from pydantic import BaseModel, Field, RootModel, field_validator


class SystemConfigRequest(RootModel):
    '''
    root 存的就是请求体里的内容

    ① 收到请求体 {"theme": "dark", "page_size": 20}
        ↓
    ② 因为类继承 RootModel，它把整个请求体存进 root 字段
       相当于内部执行：root = {"theme": "dark", "page_size": 20}
        ↓
    ③ 赋值时触发 field_validator('root') 注册的验证器
       调用 not_empty(value={"theme": "dark", "page_size": 20})
        ↓
    ④ 非空 → 通过
    '''

    # 字段 校验器
    @field_validator('root')  # 告诉 Pydantic："这个函数是 root 字段的验证器，每次给 root 赋值时都要过一遍它。"
    @staticmethod
    def not_empty(value: dict[str, Any]):
        if not value:
            # 在 Python 里，return ValueError 只是把这个异常对象当成普通值返回了，并不会触发报错！
            # 正确的写法是 raise ValueError('请求体不能为空')。
            raise ValueError('请求体不能为空')
        return value





class SystemConfigResponse(BaseModel):
    # Field 是 Pydantic 里用来给字段附加各种元信息的工具。
    # 默认值只是它能干的一小部分，它还能管校验、别名、文档、序列化等一大堆事。
    # Pydantic 每次需要默认值时，调用 dict()，得到一个新的空字典,所以这里是factory,传递的是函数名
    config:dict[str, Any] = Field(default_factory=dict)