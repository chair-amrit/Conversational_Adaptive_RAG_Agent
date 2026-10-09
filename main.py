from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from rag_utils import create_rag
from llm_utils import generate_chain , tav_search , web_chain , router_chain , rewrite_chain , retrieval_grader
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

pdf_paths = [
    r"D:\finetune.pdf",
    r"D:\min_project.pdf",
]

retriever = create_rag(pdf_paths)

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
    docs=retriever.invoke(
        state["standalone_question"]
    )
    context="\n\n".join(
        doc.page_content
        for doc in docs
    )
    print("Rewritten:",state["standalone_question"])
    return {
        "context": context
    }


def grader_node(state):
    chain = retrieval_grader()
    response = chain.invoke({
        "question":state["standalone_question"],
        "context":state["context"]
    })
    return {
        "retrieval_status":response.content.strip().lower()
    }


def route_retrieval_node(state):
    return state["retrieval_status"]


def generate_node(state):
    chain=generate_chain()
    response=chain.invoke({
        "messages":state["messages"],
        "context": state["context"],
        "question": state["question"]
    })
    return {
        "answer":response.content
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
        "answer":response.content
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
        "yes":"web_search",
        "no":END
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