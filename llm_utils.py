from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from dotenv import load_dotenv

load_dotenv()

def generate_chain():
    llm=ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite"
    )
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a helpful assistant answering questions
            using retrieved document context.

            Rules:
            1. Answer using the provided context.
            2. Cite document-based claims using the exact source
               and page information supplied in the context.
            3. Format citations like:
               [Source: min_project.pdf, Page 4]
            4. Never invent filenames, page numbers, or citations.
            5. If the context does not support an answer, say
               that the information was not found in the documents.
            6. Use conversation history to understand follow-up
               questions, but do not treat it as document evidence.
            """
        ),
        MessagesPlaceholder(variable_name="messages"),
        (
            "human",
                """
            Retrieved context:
            {context}

            Question:
            {question}
            """
        )
    ])

    chain = prompt | llm
    return chain


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