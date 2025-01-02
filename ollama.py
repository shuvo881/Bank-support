from pydantic import BaseModel
from pydantic_ai import Agent


class CityLocation(BaseModel):
    city: str
    country: str


agent = Agent('ollama:llama3.2', result_type=CityLocation)

result = agent.run_sync('Where the olympics held in 2012?')
print(result.data)
