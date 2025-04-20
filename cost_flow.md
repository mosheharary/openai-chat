# Token Counting and Cost Calculation Flow

## How Token Counting Works

1. **Prompt Tokens**: Counted before sending the request using `tiktoken`
   - Each message is counted individually
   - Each message adds 3 tokens overhead
   - Special handling for different models

2. **Completion Tokens**: Counted after receiving the response
   - Uses `tiktoken` to count tokens in the response text
   - More accurate than estimating based on word count

3. **Total Tokens**: Sum of prompt + completion tokens

4. **Cost Calculation**: Based on OpenAI's pricing model
   - Different rates for prompt and completion tokens
   - Different rates for different models (GPT-4, GPT-3.5, etc.)
   - Calculates cost per 1,000 tokens

## Pricing Table (as of 2024)

| Model        | Prompt (per 1K) | Completion (per 1K) |
|--------------|-----------------|---------------------|
| GPT-4o       | $0.005         | $0.015             |
| GPT-4o-mini  | $0.00015       | $0.0006            |
| GPT-4-turbo  | $0.01          | $0.03              |
| GPT-4        | $0.03          | $0.06              |
| GPT-3.5-turbo| $0.0005        | $0.0015            |

## Display Components

1. **Per-Query Display**: Shows tokens and cost for each interaction
2. **Session Total**: Running total displayed in the sidebar
3. **Cost Metrics**: Clear visualization using Streamlit metrics
