from atguigu.engines.agent.host.section.output import AgentSectionOutput
from atguigu.engines.contract.events import HostDiscussionMessageEvent
from atguigu.engines.contract.judgement import SectionJudgement


def build_agent_discussion_event(
        task_id:str,
        output: AgentSectionOutput
) -> HostDiscussionMessageEvent:
    '''
    构造讨论事件(原味切片)
    '''
    return HostDiscussionMessageEvent(
        task_id=task_id,
        source=output.source,
        content=output.body[:2000],
        section_key=output.section_key
    )


def build_judgement_discussion_event(
        task_id:str,
        judgement: SectionJudgement
) -> HostDiscussionMessageEvent:
    '''
    构造讨论事件(主持人总结)
    '''
    return HostDiscussionMessageEvent(
        task_id=task_id,
        source='host',
        content=judgement.host_judgement,
        section_key=judgement.section_key,
        judgement=judgement
    )