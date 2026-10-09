from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from llm_utils import generate_chain
import os

load_dotenv()


def create_rag(pdf_paths):

    # Allow either one PDF path or a list of paths
    if isinstance(pdf_paths, (str, os.PathLike)):
        pdf_paths = [pdf_paths]

    # Create the embedding model
    embeds = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001"
    )

    # Open the persistent Chroma database
    vectors = Chroma(
        collection_name="my_rag",
        persist_directory="./chroma_db",
        embedding_function=embeds,
    )

    # Keep the same chunking configuration
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=90
    )

    # Process each PDF independently
    for pdf_path in pdf_paths:

        source_path = os.path.abspath(os.fspath(pdf_path))

        # Check whether this particular PDF is already indexed.
        # The fallback also recognizes your existing Chroma data,
        # whose source metadata was created by PyPDFLoader.
        existing = vectors.get(
            where={"source": source_path},
            limit=1
        )["ids"]

        if existing:
            print(f"Already indexed: {os.path.basename(source_path)}")
            continue

        print(f"Indexing: {os.path.basename(source_path)}")

        # Load PDF
        loader = PyPDFLoader(source_path)
        docs = loader.load()

        # Attach source metadata to each page/document
        for doc in docs:
            doc.metadata["source"] = source_path
            doc.metadata["file_name"] = os.path.basename(source_path)

        # Split into chunks
        chunks = splitter.split_documents(docs)

        if not chunks:
            print(f"No chunks created: {source_path}")
            continue

        # Embed and store chunks in Chroma
        vectors.add_documents(chunks)

    # Return one retriever that searches the collection
    retriever = vectors.as_retriever(
        search_kwargs={"k": 2}
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