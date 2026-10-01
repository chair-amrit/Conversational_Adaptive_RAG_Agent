from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from llm_utils import generate_chain

load_dotenv()

def create_rag(pdf_path):
    #load pdf
    loader = PyPDFLoader(pdf_path)
    docs=loader.load()

    #splitter:provide chunk size and overlap
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=90
    )

    #split into chunks
    chunks=splitter.split_documents(docs)

    #create embeddings
    embeds=GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    #create Chroma
    vectors = Chroma.from_documents(
        chunks,
        embeds,
        collection_name="my_rag",
        persist_directory="./chroma_db"
    )

    #create retriever
    retriever=vectors.as_retriever(
        search_kwargs={"k":2}
    )

    return retriever

def ask_question(query,retriever):
    #retrieve chunks
    retrieved_docs=retriever.invoke(query)

    #join the retieved chunks(doc object) into text object for gemini model 
    cont="\n\n".join(
        doc.page_content for doc in retrieved_docs
    )

    #create the chain(prompt->llm)
    chain = generate_chain()

    #generate answer and get the response
    response=chain.invoke({
        "context":cont,
        "question":query
    })

    return response.content