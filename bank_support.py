from dataclasses import dataclass
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic import BaseModel, Field

from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv

load_dotenv()

class DatabaseConn:
    """This is a fake database for example purposes.

    In reality, you'd be connecting to an external database
    (e.g. PostgreSQL) to get information about customers.
    
    """
    

    users = [
        {
            'id': 123,
            'name': 'John',
            'balance': 123.45,
            'status': 'active',
            'card_blocked': False,
        
        },
        {
            'id': 456,
            'name': 'Kawya',
            'balance': 678.90,
            'status': 'active',
            'card_blocked': False,
        },
    ]

    @classmethod
    async def customer_name(cls, *, id: int) -> str | None:
        for user in cls.users:
            if user['id'] == id:
                return user['name']
        raise ValueError('Customer not found')

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        for user in cls.users:
            if user['id'] == id:
                return user['balance']
        raise ValueError('Customer not found')
    
    @classmethod
    async def block_card(cls, *, id: int, include_pending: bool) -> None:
        for user in cls.users:
            if user['id'] == id:
                user['card_blocked'] = True
                return
        raise ValueError('Customer not found')


@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


class SupportResult(BaseModel):
    support_advice: str = Field(description='Advice returned to the customer')
    block_card: bool = Field(description='Whether to block their')
    risk: int = Field(description='Risk level of query', ge=0, le=10)
    
    

support_agent = Agent(
    "ollama:mistral",
    deps_type=SupportDependencies,
    result_type=SupportResult,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level(0-10) of their query. '
        'if blocking the card is necessary, return True'
        "Reply using the customer's name."
    ),
)


@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"


@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies], include_pending: bool
) -> str:
    """Returns the customer's current account balance."""
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return f'${balance:.2f}'

@support_agent.tool
async def block_card(ctx: RunContext[SupportDependencies], include_pending: bool) -> bool:
    """Block the customer's card."""
    await ctx.deps.db.block_card(id=ctx.deps.customer_id, include_pending=include_pending)
    return True


deps = SupportDependencies(customer_id=123, db=DatabaseConn())
try:
    result = support_agent.run_sync('What is my balance?', deps=deps)
    print(result.data)
    result = support_agent.run_sync('I just lost my card! I have needed to block the card. please block the card', deps=deps)
    print(result.data)
except UnexpectedModelBehavior:
    print(support_agent.last_run_messages)
    raise

print(DatabaseConn.users)
