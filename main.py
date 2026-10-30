from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from rag_utils import create_rag, get_record_by_index
from llm_utils import generate_chain , tav_search , web_chain , router_chain , rewrite_chain , retrieval_grader
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
import os
import re
from pathlib import Path

pdf_paths = [
    r"D:\mycodes\langchain\prac_files\finetune.pdf",
    r"D:\mycodes\langchain\prac_files\min_project.pdf",
    r"D:\mycodes\langchain\prac_files\sample.docx",
    r"D:\mycodes\langchain\prac_files\notes.txt",
    r"D:\mycodes\langchain\prac_files\AI_survey_responses.csv",
    r"D:\mycodes\langchain\prac_files\dabstep_task_registry.xlsx",
    r"D:\mycodes\langchain\prac_files\project_atlas_kickoff.pptx",
    r"D:\mycodes\langchain\prac_files\quant_strategy_spec.json",
    r"D:\mycodes\langchain\prac_files\rag_service_design.html",
]

retriever = create_rag(pdf_paths)

# Generic words that should not be used to identify a filename.
FILE_NAME_STOPWORDS = {
    "the", "our", "my", "a", "an", "of", "from", "in", "for",
    "me", "please", "get", "show", "give", "find", "tell",
    "details", "detail", "information", "about", "what", "is",
    "are", "and", "with", "this", "that", "response", "responses",
    "record", "records", "row", "rows", "entry", "entries",
    "item", "items", "number", "no", "csv", "file", "dataset",
    "data", "th", "st", "nd", "rd",
}


def extract_record_index(query):
    patterns = [
        r"\b(\d+)\s*(?:st|nd|rd|th)\s+"
        r"(?:response|record|row|entry|item)s?\b",

        r"\b(?:response|record|row|entry|item)s?\s*"
        r"(?:number|no\.?|#)?\s*(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return int(match.group(1))

    return None


def normalize_tokens(text):
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token.isalpha()
    }

    # Basic singular/plural matching, e.g. transactions/transaction.
    expanded = set(tokens)
    for token in tokens:
        if len(token) > 4 and token.endswith("s"):
            expanded.add(token[:-1])

    return expanded


def resolve_csv_path(query):
    candidates = [
        Path(file_path).resolve()
        for file_path in pdf_paths
        if Path(file_path).suffix.lower() == ".csv"
    ]

    if not candidates:
        return None

    query_tokens = (
        normalize_tokens(query) - FILE_NAME_STOPWORDS
    )

    # A generic request such as "show row 12" can use the
    # sole CSV, but not choose arbitrarily between multiple CSVs.
    if not query_tokens:
        if len(candidates) == 1:
            return str(candidates[0])
        return None

    scores = []
    for path in candidates:
        filename_tokens = normalize_tokens(path.stem)
        filename_tokens -= FILE_NAME_STOPWORDS
        scores.append(
            len(query_tokens & filename_tokens)
        )

    best_score = max(scores)

    # No filename match, or multiple equally likely files:
    # don't guess which CSV the user intended.
    if best_score == 0 or scores.count(best_score) != 1:
        return None

    return str(candidates[scores.index(best_score)])

#LangGraph needs to know what data exists in the state.
class State(TypedDict):
    question: str
    standalone_question: str
    context: str
    answer: str
    web_context: str
    messages: Annotated[list,add_messages]
    route: str
    web_permission: str
    retrieval_status: str
    record_path: str
    record_index: int
    record_found: bool

#check query and determine if chat/valid question/invalid query and update route in state
def router_node(state):
    chain=router_chain()
    response=chain.invoke({
        "query":state["question"]
    })
    return {
        "route": response.content.strip().lower().replace(".", "")
    }

#fuction to return route from state
def route_query(state):
    return state["route"]

#if invalid query....
def invalid_node(state):
    return{
        "answer":"I couldn't understand that input."
    }

#if normal chatting......
def chat_node(state):
    return{
        "answer":"I can answer questions about the document or chat with you."
    }

#if question..... we need a rewriter so we could retrieve for follow up questions
def rewrite_node(state):
    chain = rewrite_chain()
    response = chain.invoke({
        "messages":state["messages"],
        "question":state["question"]
    })
    return {
        "standalone_question":response.content.strip()
    }


def retriever_node(state):
    docs = retriever.invoke(state["standalone_question"])

    # DEBUG: inspect what ChromaDB retrieves
    print("\n--- RETRIEVED DOCUMENTS ---")
    print("Rewritten question:", state["standalone_question"])
    print("Number of retrieved chunks:", len(docs))

    context_parts = []

    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("file_name")

        if not source:
            source = os.path.basename(
                doc.metadata.get("source", "Unknown source")
            )

        print(f"\n[Document {i}]")
        print("File:", source)
        print("Path:", doc.metadata.get("source"))
        print("Retrieved text:")
        print(doc.page_content[:1000])
        print("-" * 50)

        page = doc.metadata.get("page")

        # PyPDFLoader page metadata is zero-indexed.
        if page is not None:
            try:
                page_label = f"Page {int(page) + 1}"
            except (ValueError, TypeError):
                page_label = f"Page {page}"
        else:
            page_label = "Page unknown"

        context_parts.append(
            f"Source: {source}\n"
            f"{page_label}\n"
            f"Content:\n{doc.page_content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    print("\n--- END RETRIEVED DOCUMENTS ---\n")

    return {"context": context}




def grader_node(state):
    chain = retrieval_grader()

    response = chain.invoke({
        "question": state["standalone_question"],
        "context": state["context"]
    })

    # Handle either string content or a list of text blocks.
    raw = response.content

    if isinstance(raw, str):
        raw_text = raw
    elif isinstance(raw, list):
        raw_text = " ".join(
            block.get("text", "")
            if isinstance(block, dict)
            else str(block)
            for block in raw
        )
    else:
        raw_text = str(raw or "")

    # Normalize the model's response.
    tokens = [
        token.strip(".,:;!?\"'`*()[]{}").lower()
        for token in raw_text.split()
    ]

    labels = [
        token for token in tokens
        if token in {"relevant", "irrelevant"}
    ]

    if labels:
        status = labels[0]
    else:
        # If the grader fails, try answering from the retrieved
        # context instead of crashing the graph.
        print(
            "Warning: invalid retrieval grader response:",
            repr(raw_text)
        )
        print("Defaulting to 'relevant' for this question.")
        status = "relevant"

    print("Retrieval grader status:", status)

    return {"retrieval_status": status}




def route_retrieval_node(state):
    return state["retrieval_status"]



def response_to_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)

        return "\n".join(part for part in parts if part).strip()

    return str(content) if content is not None else ""



def generate_node(state):
    chain=generate_chain()
    response=chain.invoke({
        "messages":state["messages"],
        "context": state["context"],
        "question": state["question"]
    })
    return {
    "answer": response_to_text(response.content)
    }


def permission_node(state):
    while True:
        choice=input(
            "\nI couldn't find this in the document.\n"
            "Search the web? (yes/no): "
            ).strip().lower()
        if choice in ["yes","y"]:
            return {
                "web_permission":"yes"
            }
        if choice in ["no","n"]:
            return {
                "web_permission":"no"
            }
        print("Please enter 'yes' or ' no'.")


def route_web_permission(state):
    return state["web_permission"]


def web_search_node(state):
    web_context=tav_search(
        state['standalone_question']
    )
    return {
        "web_context":web_context
    }

def web_generate_node(state):
    chain=web_chain()

    response=chain.invoke({
        "context":state["web_context"],
        "question":state["question"]
    })
    return{
        "answer":response_to_text(response.content)
    }


def no_web_node(state):
    return {
        "answer": (
            "I couldn't find this information in the documents, "
            "and web search was not requested."
        )
    }



def save_node(state):
    print(state["messages"])
    return {
        "messages":[
            HumanMessage(content=state["question"]),
            AIMessage(content=state["answer"])
        ]
    }

memory=MemorySaver()

config = {
    "configurable":{
        "thread_id":"chat1"
    }
}

graph= StateGraph(State)

graph.add_node("check_query",router_node)
graph.add_node("invalid_node",invalid_node)
graph.add_node("chat_node",chat_node)
graph.add_node("rewrite",rewrite_node)
graph.add_node("retrieve",retriever_node)
graph.add_node("grader",grader_node)
graph.add_node("generate",generate_node)
graph.add_node("permission",permission_node)
graph.add_node("no_web", no_web_node)
graph.add_node("web_search",web_search_node)
graph.add_node("web_generate",web_generate_node)
graph.add_node("save",save_node)

#check query and redirect to appropriate node
graph.add_conditional_edges(
    "check_query",
    route_query,
    {
        "chat":"chat_node",
        "nonsense":"invalid_node",
        "doc":"rewrite"
    }
)
graph.add_conditional_edges(
    "grader",
    route_retrieval_node,
    {
        "relevant":"generate",
        "irrelevant":"permission"
    }
)

graph.add_conditional_edges(
    "permission",
    route_web_permission,
    {
        "yes": "web_search",
        "no": "no_web"
    }
)

graph.add_edge(START,"check_query")
graph.add_edge("chat_node",END)
graph.add_edge("invalid_node",END)
graph.add_edge("rewrite","retrieve")
graph.add_edge("retrieve","grader")
graph.add_edge("generate","save")
graph.add_edge("web_search","web_generate")
graph.add_edge("web_generate","save")
graph.add_edge("no_web", END)
graph.add_edge("save",END)


app = graph.compile(
    checkpointer=memory
)

while True:
    question=input("User:")
    
    if question.lower()=="exit":
        break

    result=app.invoke({
        "question":question,
        "context":"",
        "answer":"",
        "web_context":"",
        "messages":[],
        "route":"",
        "web_permission":"",
        "retrieval_status":""
        },config=config
    )
    print("\nAgent:",result["answer"])
    print()

#for debuging and understanding purpose
"""
for event in app.stream({
    "question":"Who won IPL 2020?",
    "context":"",
    "answer":""
}):
    print(event)
"""