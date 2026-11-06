"""Insight/Media 共享的章节摘要节点基类"""
import json
from typing import Any

from langchain_core.prompts import PromptTemplate
from loguru import logger
from atguigu.engines.contract.context import ResearchBaseNode
from atguigu.engines.contract.evidence import render_evidence_context
from atguigu.engines.contract.role import get_role_display_name
from atguigu.engines.contract.section import get_section_definition_for_key
from atguigu.engines.prompts.shared import SECTION_SUMMARY_USER_PROMPT


class BaseSectionSummaryNode(ResearchBaseNode):
    """章节摘要节点基类:游标推进、证据组装、LLM 生成摘要与事件发布"""
    system_prompt: str = ""
    fallback_body: str = ""

    async def __call__(self, state:dict[str,Any]) -> dict[str,Any]:
        """按当前第几章，取出这章的证据，让 AI 写出这章内容，然后通知下一步。"""
        agent_name = get_role_display_name(self.context.role)

        logger.info(f"{agent_name} 开始生成章节摘要")

        cursor = state.get('cursor',0)
        sections = state['sections']
        section = sections[cursor]
        # section_records 证据列表
        section_records = state['section_evidence_records'][cursor]

        if not section_records:

            logger.info(f"【章节 {section['section_key']}】证据上下文为空,跳过生成。")

            section['body'] = self.fallback_body
        else:
            section['body'] = await self._generate_section_body(
                section,  # 当前章节对象
                query=self._query(state,cursor),  # 这一章用的查询文本
                evidence_context=render_evidence_context(section_records) # 当前章证据渲染后的文本
            )

        # 摘要就是每一章的正文
        logger.info(f"{agent_name} 生成章节摘要完成")

        # 写完这一章 游标要去下一章
        return {'sections':sections,'cursor':cursor+1}

    async def _generate_section_body(self, section:dict[str,Any], query:str, evidence_context:str) -> str:
        '''
        调用llm生成章节正文
        '''

        # 这行代码就是根据章节的 key，去查这个章节的完整定义。
        section_definition = get_section_definition_for_key(section['section_key'])
        section_context = section_definition.section_context_by_role(self.context.role)

        user_prompt = PromptTemplate.from_template(template=SECTION_SUMMARY_USER_PROMPT).format(
            section_context=json.dumps(section_context, ensure_ascii=False, indent=2),
            query=query,
            evidence_context=evidence_context
        )
        
        return await self.context.llm_client.generate_text(self.system_prompt, user_prompt)

    def _query(self, state:dict[str,Any], cursor:int) -> str:
        """章节证据对应的检索请求,默认取用户最初的研究问题"""
        return self.context.query