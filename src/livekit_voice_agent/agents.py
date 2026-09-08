from dotenv import load_dotenv
from livekit.agents import Agent, AgentSession, JobContext, RunContext, AgentServer, function_tool
from livekit import agents
from livekit.plugins import groq
import httpx
from pydantic import BaseModel, Field
import logging
import inspect



logger = logging.getLogger(__name__)

load_dotenv()


class WeatherResult(BaseModel):
    city: str
    temperature_c: float
    condition: str
    humidity_percent: int


class Assistant(Agent):
    
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful voice AI assistant.Keep your responses concise because you are speaking. always answer in one or two sentences. "
        )
        
        
    @function_tool
    async def get_weather(self, ctx: RunContext, city: str) -> str:
        """
        Get the current weather for a city
        
        Args:
        city: name of the city
        """ 
        url = f"https://wttr.in/{city}?format=j1"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url=url)
            response.raise_for_status()
            
        data = response.json()
        current = data["current_condition"][0]
        
        logger.debug("weather result: %s", current)
        
        result = WeatherResult(
            city=city,
            temperature_c=float(current["temp_C"]),
            condition=current["weatherDesc"][0]["value"],
            humidity_percent=int(current["humidity"]),
        )
        
        return result.model_dump_json()
    
server = AgentServer()    


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    
    session = AgentSession(
        stt=groq.STT(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm=groq.LLM(
            model="openai/gpt-oss-20b"
        ),
        tts=groq.TTS(
            model="canopylabs/orpheus-v1-english",
            voice="autumn",
        ),
    )
    
    await session.start(
        room=ctx.room,
        agent=Assistant()
    )
    
    await ctx.connect()
    
    await session.generate_reply(
        instructions="Greet the user and ask how you can help"
    )
    
    
if __name__ == "__main__":
    agents.cli.run_app(
        server=server
    )