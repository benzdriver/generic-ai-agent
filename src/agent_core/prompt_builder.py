# src/agent_core/prompt_builder.py

def build_prompt(user_query: str, retrieved_chunks: list) -> str:
    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
你是一名资深的加拿大移民顾问助手，请根据以下相关资料回答用户的问题。

【相关资料】
{context}

【用户提问】
{user_query}

请用简洁、专业且友好的语气作答。如果没有相关信息，请明确说明。
"""
    return prompt
