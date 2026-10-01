from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

def generate_chain():
    llm=ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )
    prompt= ChatPromptTemplate.from_template(
        """
        You are a helpful AI assistant.

        Use the retrieved context to answer the user's question accurately.

        Rules:
        - Answer only from the provided context.
        - If the context is insufficient, do not guess.
        - Be clear and concise.
        - Use the conversation history only for conversational continuity, not as factual evidence.

        Conversation:
        {messages}

        Context:
        {context}

        Question:
        {question}

        Answer:
        """
    )
    return prompt | llm


def web_chain():
    llm=ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )
    prompt= ChatPromptTemplate.from_template(
        """
        Answer the question using the web search results.
        

        Web Search Results:
        {context}

        Question:
        {question}
        """
    )
    return prompt | llm



from tavily import TavilyClient
import os

client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

def tav_search(query):
    response = client.search(
        query=query
    )
    results=response["results"]

    context="\n\n".join(
        f"{result['title']}\n{result['content'][:400]}"
        for result in results[:5]
    )
    return context




from langchain_groq import ChatGroq

def router_chain():
    llm=ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )
    prompt=ChatPromptTemplate.from_template(
        """
        Classify the user input into exactly one category:

        chat: greetings, casual conversation, questions about the assistant, small talk.
        doc: information-seeking questions, technical questions, or questions that may require document or web knowledge.
        nonsense: gibberish or meaningless input.

        Return ONLY one word:
        chat
        doc
        nonsense

        Input:
        {query}
"""
    )
    return prompt | llm

def rewrite_chain():
    llm=ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0
    )
    prompt=ChatPromptTemplate.from_template(
        """
        You rewrite follow-up questions into standalone questions.

        Rules:
        - If the question is already standalone, return it unchanged.
        - Resolve pronouns like "it", "they", "that" using the conversation history.
        - If the user introduces a new topic or entity, do NOT replace it with an older one.
        - Return only the rewritten question.

        Conversation:
        {messages}

        Question:
        {question}
        """
    )
    return prompt | llm

def retrieval_grader():
    llm=ChatGroq(
        model="openai/gpt-oss-20b",     
        temperature=0
    )
    prompt=ChatPromptTemplate.from_template(
        """
        You are a retrieval relevance classifier.

        Your task is to determine whether the retrieved context contains information that is useful for answering the user's question.

        Rules:
        - Return "relevant" if the context contains all OR part of the information needed to answer the question.
        - Return "relevant" even if the answer is incomplete, brief, or requires inference from the retrieved context.
        - Return "irrelevant" ONLY if the context is completely unrelated to the user's question.
        - Do NOT judge the quality or completeness of the answer.
        - Do NOT explain your reasoning.

        Question:
        {question}

        Retrieved Context:
        {context}

        Output ONLY one word:
        relevant
        or
        irrelevant
        """
    )
    return prompt | llm