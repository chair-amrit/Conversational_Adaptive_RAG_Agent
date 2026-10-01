from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from llm_utils import generate_chain

load_dotenv()

def create_rag(pdf_path):
    embeds=GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    vectors = Chroma(
        collection_name="my_rag",
        persist_directory="chroma_db",
        embedding_function=embeds,
    )

    if not vectors.get(limit=1)["ids"]:
        loader = PyPDFLoader(pdf_path)
        docs=loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=90
        )
        chunks=splitter.split_documents(docs)
        vectors.add_documents(chunks)

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