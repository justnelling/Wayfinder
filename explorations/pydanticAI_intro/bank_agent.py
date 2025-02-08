'''
https://ai.pydantic.dev/examples/bank-support/#example-code


Small but complete example of using PydanticAI to build a support agent for a bank.

Demonstrates:

dynamic system prompt
structured result_type
tools
'''

from dataclasses import dataclass 
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

class DatabaseConn:
    '''This is a fake DB for example purposes.
    
    in reality you'd be connecting to an external DB (postgresql) to get info about customers'''

    @classmethod
    async def customer_name(cls, *, id: int) -> str| None:
        if id == 123:
            return 'John'
        
    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        if id == 123:
            return 123.45
        else:
            raise ValueError('Customer not found')
        
@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn

class SupportResult(BaseModel):
    support_adivce: str = Field(description='The advice to give to the customer')
    block_card: bool = Field(description='Whether to block the card or not')
    risk: int = Field(description='The risk level of the query', ge=0, le=10)

support_agent = Agent(
    'openai:gpt-4o',
    deps_type=SupportDependencies,
    result_type = SupportResult,
    system_prompt=(
        'You are a support agent in our bank, give the '
        'customer support and judge the risk level of their query. '
        "Reply using the customer's name."
    )
)

#? define added system prompt agent gets injected
@support_agent.system_prompt
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
    customer_name = await ctx.deps.db.customer_name(id=ctx.deps.customer_id)
    return f"The customer's name is {customer_name!r}"

@support_agent.tool
async def customer_balance(
    ctx: RunContext[SupportDependencies],
    include_pending: bool
) -> str:
    '''Returns the customer's current account balance'''
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending
    )
    return f'${balance:.2f}'

if __name__ == '__main__':
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())
    result = support_agent.run_sync('What is my balance?', deps=deps)
    print(result.data)

    result=support_agent.run_sync('I just lost my card!', deps=deps)
    print(result.data)
    