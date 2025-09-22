import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA,  LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
from duckduckgo_search import DDGS


load_dotenv() 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Step 1: Embedding model
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4o-mini")

# Load documents (PDF + text FAQs)
pdf_loader1 = PyMuPDFLoader("finance_faq_extended.pdf")   # <--- Your PDF
pdf_loader2 = PyMuPDFLoader("sofi_top_products.pdf") 
pdf_docs = pdf_loader1.load() + pdf_loader2.load()
print("PDF docs:", len(pdf_docs))


faq_loader = TextLoader("faqs.txt")  
try:
    faq_docs = faq_loader.load()
    print("FAQ docs:", len(faq_docs))
except Exception:
    faq_docs = []


# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
docs = splitter.split_documents(pdf_docs + faq_docs)
print("Total after split:", len(docs))

# Create Chroma vectorstore
if os.path.exists("chroma_store"):
    vectorstore = Chroma(persist_directory="chroma_store", embedding_function=embeddings)
    # Add new docs
    vectorstore.add_documents(docs)  # docs should include only the new PDFs
    vectorstore.persist()
else:
    vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="chroma_store")

# Step 5: Create a Prompt Template
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are SofiBot, SoFi's personal financial assistant. You have expert knowledge of SoFi's products, banking, loans, investments, credit cards, interest rates, and company policies.

Rules:
1. Always respond in a helpful, clear, and professional manner.
2. Use ONLY the information provided in the context below or authoritative SoFi sources.
3. If the answer is not in your documents or sources, say: "I'm sorry, I don't have that information right now."
4. Do NOT provide information about unrelated topics (like SoFi Stadium, sports, etc.).
5. If the user asks about comparing SoFi to other companies, provide a factual comparison only based on finance-related context.
6. Keep answers concise and easy to understand for everyday users.
Context:
{context}

Question: {question}

Answer:
"""
)

# Create RetrievalQA chain
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(),
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt_template}  # use our prompt template
)

# Step 4: Summarization prompt for DuckDuckGo results
ddg_summary_prompt = PromptTemplate(
    input_variables=["search_results", "question"],
    template="""
        You are SofiBot, SoFi's personal financial assistant. Summarize the following web search results to answer the user's question. Only include finance-related information. If nothing relevant is found, say "I don't have that information."


    Search results:
    {search_results}

    Question: {question}

    Answer:
    """
)
summary_chain = LLMChain(llm=llm, prompt=ddg_summary_prompt)
def ask_question(question: str):
    response = qa_chain.invoke({"query": question})
    answer = response["result"]

    if "I couldn't find it in my documents" in answer:
        # Step 2: Perform DuckDuckGo search
        ddgs = DDGS()
        search_results = ddgs.text(question, max_results=5)
        if not search_results:
            return {
                "answer": "I searched online but couldn't find relevant results.",
                "sources": []
            }

        # Combine top results into a single string
        combined_results = "\n".join(
            [f"Title: {r['title']}\nSnippet: {r['body']}\nLink: {r['href']}" for r in search_results]
        )

        # Summarize using GPT
        summary = summary_chain.run({
            "search_results": combined_results,
            "question": question
        })
        return {
            "answer": summary,
            "sources": ["DuckDuckGo search"]
        }

    return {
        "answer": response["result"],
        "sources": [doc.page_content for doc in response["source_documents"]],
    }
