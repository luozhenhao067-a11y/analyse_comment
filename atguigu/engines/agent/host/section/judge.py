import json
from typing import Any

from click import prompt
from langchain_core.prompts import PromptTemplate
from loguru import logger
from typesafe_sdk import AsyncTypeSafeClient, Choice, ChoiceAnswer

from atguigu.engines.agent.host.section.output import AgentSectionPair
from atguigu.engines.common.llm import LLMClient
from atguigu.engines.contract.config import get_config_settings
from atguigu.engines.contract.judgement import SectionJudgement
from atguigu.engines.prompts.host import (
    HOST_SECTION_JUDGE_SYSTEM_PROMPT,
    HOST_SECTION_JUDGE_USER_PROMPT,
)

'''
这个脚本就干了一件事：当两个写手（Insight 和 Media）把同一章的稿子都交上来后，
找个“裁判”定个性，
再找个“主编”写总结
'''

_JEV_MODEL = "jev-latest"

_VERDICT_CRITERIA: dict[str, str] = {
    "aligned": "双方核心事实与结论基本一致，仅侧重点或细节详略不同",
    "complementary": "一方有实质分析、另一方声明数据缺口或样本视角不同，属互补而非冲突",
    "conflicting": "双方对同一事实、成因或趋势提出了不兼容的实质性主张"
}

_llm_client:LLMClient = LLMClient.from_role('host')


# AgentSectionPair(
#     section_key="chapter_1",  # 这是哪一章（比如第一章）
#     title="事件背景",           # 这一章的标题
#     insight=...,              # Insight 写的那份正文
#     media=...                 # Media 写的那份正文
# )
def _build_judgement_context(section_pair:AgentSectionPair) -> dict[str, Any]:
    '''把两个 AI 写好的长文章，砍掉多余的尾巴，打包成一个小盒子，准备拿去给裁判看'''
    return {
        "section":{
          "key": section_pair.section_key,
          "title": section_pair.title
        },
        "insight": {'body':section_pair.insight.body[:3000]},
        "media": {"body": section_pair.media.body[:3000]}
    }

# ChoiceAnswer 不是什么 Python 自带的官方类型，
# 它是项目里用到的一个第三方 AI 库（也就是代码里导进来的 typesafe_sdk）自己定义的一个数据类。
async def select_jev_verdict(judgement_context:dict[str,Any]) -> ChoiceAnswer | None:
    '''花 30 秒钟找个外包裁判（Jev），拿着两份稿子去问他一道单选题，如果他正常回答就录用，如果他罢工就作废'''
    api_key = get_config_settings().TYPESAFE_API_KEY
    try:
        async with AsyncTypeSafeClient(api_key=api_key, model=_JEV_MODEL, timeout=30.0) as client:
            response = await client.system_one(
                state=judgement_context,
                questions={
                    'jev_verdict': Choice(
                        instructions=(
                            "判断私域舆情研究员(insight)与公开媒体研究员(media)在同一章节的结论关系。"
                            "单方缺少数据或双方观察不同层面时属于 complementary，只有对同一问题提出不兼容主张才属于 conflicting。"
                        ),
                        # Criteria 的意象是：“一把用来衡量、筛选的尺子”，或者“招考简章上的硬性标准”。
                        criteria=_VERDICT_CRITERIA, # 答案有哪些选项,每个选项各代表什么意思
                    )
                }
            )
        answer = response.choices['jev_verdict']
        if answer.choice in _VERDICT_CRITERIA:  # 答案是否在选项中
            return answer
    except Exception as exc:
        logger.warning(f"Jev 章节裁决失败，降级为仅由 LLM 研判: {exc}")
    return None


async def judge_section(section_pair: AgentSectionPair) -> SectionJudgement:
    '''
    让裁判定个调，让主编照着这个调去写一篇总结报告，最后盖上印章交差
    '''

    # 塞给jev的文档
    judgement_context = _build_judgement_context(section_pair)

    # verdict 在英语里的核心意象是：“权威的、最终的判决”  answer 就是一个包含裁判（Jev）判决结果的对象。
    answer = await select_jev_verdict(judgement_context)

    # 这叫“打底”，或者叫“防守型编程”。
    # 这个 judge_section 函数有一个硬性要求：
    # 不管你裁判（Jev）有没有干活，不管你判没判成功，最后你都必须交出这三个变量。
    jev_verdict = ''
    confidence = 0.0
    probabilities:dict[str,float] = {}

    if answer is not None:
        jev_verdict = answer.choice  # 选择 ( 对齐 互补 冲突 ) 的哪一个
        # 这是 Python 内置的四舍五入函数。意思就是：只保留小数点后 4 位，后面的全砍掉。
        confidence = round(answer.confidence,4)
        probabilities = {k:round(v,4) for k,v in answer.probabilities.items()}

        logger.info(
            f"【裁判】Jev 章节裁决 章节={section_pair.section_key} "
            f"结果={jev_verdict} 置信度={confidence:.2%} 概率分布={probabilities}"
        )

        judgement_context['jev_verdict'] = {
            'verdict': jev_verdict,
            'description': _VERDICT_CRITERIA[jev_verdict],  # 名词解释
            'confidence': confidence,
            'probabilities': probabilities
        }

    prompt = PromptTemplate.from_template(HOST_SECTION_JUDGE_USER_PROMPT).format(
        # 填空
        judgement_evidence=json.dumps(judgement_context,ensure_ascii=False)
    )

    judgement = await _llm_client.generate_object(
        HOST_SECTION_JUDGE_SYSTEM_PROMPT,
        prompt,
        # 输出对象的类型
        SectionJudgement
    )

    # 就是把judgement复制一份，然后更新一些字段
    return judgement.model_copy(
        update={
            "section_key": section_pair.section_key,
            "jev_verdict": jev_verdict,
            "confidence": confidence,
            "probabilities": probabilities
        }
    )


