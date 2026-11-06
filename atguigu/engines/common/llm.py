"""
封装LLM客户端
提供根据角色返回对应角色的客户端、调用LLM的方法（文本内容、结构化对象）

"""
import asyncio
from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from atguigu.engines.common.retryer import with_retry
from atguigu.engines.contract.config import get_config_settings
from atguigu.engines.contract.role import RoleId, ROLE_METADATA

from langchain.chat_models import init_chat_model

# var 变量 bound = 给泛型 T 加"边界"，限定 T 必须是 BaseModel 或它的子类。
T = TypeVar('T',bound=BaseModel)


def _build_messages(system_prompt:str, user_prompt:str) -> list[BaseMessage]:
    '''
    字典虽然能凑合，但 LangChain 的接口约定是收 BaseMessage 这类消息对象。
    用对象的好处：
    有类型（SystemMessage、HumanMessage），区分角色
    自带方法（.content、.type 等）
    和 LangChain 其他组件能对接
    '''
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

class LLMClient:
    '''
    llm 客户端
    '''

    def __init__(
            self,
            model_name:str,
            model_provider:str,
            api_key:str,
            base_url:str
    ):
        self.model_name = model_name
        self.model_provider = model_provider
        self.api_key = api_key
        self.base_url = base_url

    '''
    类方法通常用于返回类实例 
    因为 LLMClient 这个类还没定义完，不能直接写它自己，所以用字符串代替。
    用引号包起来，Python 就先当字符串存着，不当场检查，等类定义完再解析。
    '''
    @classmethod
    def from_role(cls,role:RoleId) -> 'LLMClient':
        """
        职责：根据不同的Agent角色 获取对应角色LLM客户端
        :param role:
        :return:
        """

        # 1 根据role 获得对应llm配置
        llm_config_prefix = ROLE_METADATA[role].llm_config_prefix

        # 2 获取settings
        config_settings = get_config_settings()
        return cls(
            model_name=getattr(config_settings, f"{llm_config_prefix}_MODEL_NAME"),
            model_provider=getattr(config_settings, f"{llm_config_prefix}_MODEL_PROVIDER"),
            api_key=getattr(config_settings, f"{llm_config_prefix}_API_KEY"),
            base_url=getattr(config_settings, f"{llm_config_prefix}_BASE_URL")
        )

    @with_retry
    async def generate_text(self,
                            system_prompt: str,
                            user_prompt:str):
        """
        1. 获取到chat_model实例
        2. 调用LLM
        3. 获取响应的文本内容

        使用流式的方式获取非流式的输出结果。
        优点：针对长文本生成，可以减少服务端网络超时的发生。
        面试：如果调用LLM非常耗时【长文本】，怎么保证能够拿到最终文本的内容。

        用流式（stream）拿，不干等。

        核心：
        不用 ainvoke（等全部生成完才返回，容易超时）
        用 astream（一个字一个字往回吐）
        边收边拼，收到多少算多少

        """
        # 1 将用户以及系统提示词封装到标准的消息对象中
        messages = _build_messages(system_prompt, user_prompt)

        # 2 创建chat_model实例
        chat_model = self._get_chat_model()

        # 3 调
        final_texts:list[str] = []

        try:
            async for chunk in chat_model.astream(messages):
                # 先算右边 → 赋值 → 再判断非空(赋值完也有可能是空的,这个chunk本来就没值)
                if text := chunk.text:
                    final_texts.append(text)
        except Exception as exc:
            raise ValueError(f'{self.model_name}返回文本失败{exc}')

        # 4 返回
        return ''.join(final_texts)



    def _get_chat_model(self) -> BaseChatModel:
        return init_chat_model(
            model_provider=self.model_provider,
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url
        )

    @with_retry
    async def generate_object(self,
                              system_prompt: str,
                              user_prompt: str,
                              structed_object: type[T]  # 你想要的输出结构类型T
                              ) -> T:  # 返回你想要的结构(实例)

        """
        json_object：输出的是一个json格式字符串（提示词：返回JSON格式）
        function_calling:API(层面) 现代大语言模型都支持工具调用（广）
        json_schema:最稳的（物理）---->保证一定获取结构化对象【deepseek模型处理】--最准
        """
        # 1. 将用户以及系统的提示词内容封装到标准的消息对象中
        messages = _build_messages(system_prompt, user_prompt)

        # 2. 创建chat_model的实例对象
        chat_model = self._get_chat_model()

        # 3. 为模型调用时去指定结构化输出(返回的 structed_runnable_object = 一个"会按结构输出"的新对象，后面调它就行。)
        structed_runnable_object = chat_model.with_structured_output(structed_object, method="json_schema")

        # 4. 调用
        try:
            structed_response = await structed_runnable_object.ainvoke(messages)
        except Exception as exc:
            raise ValueError(f'{self.model_name}返回结构化对象失败{exc}')

        if structed_response is None:
            raise ValueError(f'{self.model_name}返回结构化对象为空')

        return structed_response













