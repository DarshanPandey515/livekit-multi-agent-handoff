from dataclasses import dataclass

from livekit.agents import Agent, AgentSession, AgentServer, RunContext, JobContext, function_tool
from dotenv import load_dotenv
from livekit.plugins import groq
from livekit import agents

load_dotenv()

HR_INSTRUCTION = """
    You are the company's HR representative.
    You handle:
    - compensation
    - benefits
    - leave
    - policies
    - workplace concerns
    - HR procedures

    If the user asks to speak with the manager,
    transfer to the manager.

    If the user asks to speak with the team lead,
    transfer to the team lead.

    Do not provide management decisions that belong
    to the manager.
"""

MANAGER_INSTRUCTION = """
You are now speaking as the employee's manager.

The receptionist has just transferred the user to you.

Start by briefly introducing yourself as the manager and asking
how you can help.

You can discuss:
- goals
- performance
- projects
- priorities
- team issues

If the user explicitly asks to speak with HR,
transfer to HR.

If the user explicitly asks to speak with their team lead,
transfer to the team lead.

Do not impersonate HR or the team lead.
"""

TEAMLEAD_INSTRUCTION = """
    You are the employee's team lead.

    You handle:
    - technical work
    - sprint priorities
    - implementation details
    - blockers
    - day-to-day team coordination

    If the user asks for HR,
    transfer to HR.

    If the user asks for the manager,
    transfer to the manager.
"""

BASEAGENT_INSTRUCTION = """
    You are the company's receptionist.
    
    You handle:
    - basic conversation about customer query and handover call to HR, team lead or manager

    If the user asks to speak with the manager,
    transfer to the manager.

    If the user asks to speak with the team lead,
    transfer to the team lead.
    
    If the user asks to speak with the HR,
    transfer to the HR.

    Do not provide management decisions that belong
    to the manager.
"""

@dataclass
class SessionState:
    employee_name: str | None = None
    current_role: str = "receptionist"
    conversation_summary: str | None = None


class BaseCompanyAgent(Agent):
    """Base agent shared by all company personas."""

    def __init__(self, role: str, instructions: str, chat_ctx=None) -> None:
        self.role = role
        super().__init__(
            instructions=instructions,
            chat_ctx=chat_ctx,
        )

    def handoff_context(self, context: RunContext[SessionState]):
        return self.chat_ctx.copy(exclude_instructions=True)
    
    @function_tool()
    async def transfer_to_manager(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the manager."""
        
        context.userdata.current_role = "manager"
        return ManagerAgent(
            chat_ctx=self.handoff_context(context=context)
        )

    @function_tool()
    async def transfer_to_hr(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to HR."""
        
        context.userdata.current_role = "hr"
        return HRAgent(
            chat_ctx=self.handoff_context(context=context)
        )

    @function_tool()
    async def transfer_to_team_lead(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the team lead."""
        
        context.userdata.current_role = "team_lead"
        return TeamLeadAgent(
            chat_ctx=self.handoff_context(context=context)
        )


class ManagerAgent(BaseCompanyAgent):
    """Manager persona."""

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            role="manager",
            chat_ctx=chat_ctx,
            instructions=MANAGER_INSTRUCTION,
        )

    @function_tool()
    async def transfer_to_hr(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to HR."""
        context.userdata.current_role = "hr"
        return HRAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )

    @function_tool()
    async def transfer_to_team_lead(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the team lead."""
        context.userdata.current_role = "team_lead"
        return TeamLeadAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )


class HRAgent(BaseCompanyAgent):
    """HR persona."""

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            role="hr",
            chat_ctx=chat_ctx,
            instructions=HR_INSTRUCTION,
        )

    @function_tool()
    async def transfer_to_manager(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the manager."""
        context.userdata.current_role = "manager"
        return ManagerAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )

    @function_tool()
    async def transfer_to_team_lead(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the team lead."""
        context.userdata.current_role = "team_lead"
        return TeamLeadAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )


class TeamLeadAgent(BaseCompanyAgent):
    """Team lead persona."""

    def __init__(self, chat_ctx=None) -> None:
        super().__init__(
            role="team_lead",
            chat_ctx=chat_ctx,
            instructions=TEAMLEAD_INSTRUCTION,
        )

    @function_tool()
    async def transfer_to_manager(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to the manager."""
        context.userdata.current_role = "manager"
        return ManagerAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )

    @function_tool()
    async def transfer_to_hr(self, context: RunContext[SessionState]) -> Agent:
        """Transfer the user to HR."""
        context.userdata.current_role = "hr"
        return HRAgent(
            chat_ctx=self.chat_ctx.copy(exclude_instructions=True)
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession[SessionState](
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(
            model="openai/gpt-oss-20b",  
        ),
        tts=groq.TTS(
            model="canopylabs/orpheus-v1-english",
            voice="autumn",
        ),
        userdata=SessionState()
    )
    
    await session.start(
        room=ctx.room,
        agent=BaseCompanyAgent(
            instructions=BASEAGENT_INSTRUCTION, 
            chat_ctx=None, 
            role="receptionist"
        )
    )
    
    await ctx.connect()
    
    await session.generate_reply(
        instructions="Greet the user and ask how you can help"
    )


if __name__ == "__main__":
    agents.cli.run_app(server=server)