"""
Test for 'rag-implementation' skill — RAG (Retrieval-Augmented Generation) with langchain
Validates that the Agent implemented RAG patterns including document loading,
embedding, vector store, and retrieval chain.
"""

import os
import re

import pytest


class TestRagImplementation:
    """Verify RAG implementation with langchain."""

    REPO_DIR = "/workspace/langchain"

    def test_document_loader(self):
        """Document loader must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"DocumentLoader|TextLoader|PDFLoader|WebBaseLoader|load_documents|DirectoryLoader", content):
                        found = True
                        break
            if found:
                break
        assert found, "No document loader found"

    def test_text_splitter(self):
        """Text splitter/chunker must be used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"TextSplitter|RecursiveCharacterTextSplitter|CharacterTextSplitter|split_documents|chunk", content):
                        found = True
                        break
            if found:
                break
        assert found, "No text splitter found"

    def test_embeddings_model(self):
        """Embeddings model must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]mbedding|OpenAIEmbeddings|HuggingFaceEmbeddings|embed_documents|embed_query", content):
                        found = True
                        break
            if found:
                break
        assert found, "No embeddings model found"

    def test_vector_store(self):
        """Vector store must be used (FAISS, Chroma, Pinecone, etc)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"FAISS|Chroma|Pinecone|Weaviate|Milvus|VectorStore|vectorstore|from_documents", content):
                        found = True
                        break
            if found:
                break
        assert found, "No vector store found"

    def test_retriever(self):
        """Retriever must be configured."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]etriever|as_retriever|VectorStoreRetriever|similarity_search|get_relevant_documents", content):
                        found = True
                        break
            if found:
                break
        assert found, "No retriever configured"

    def test_retrieval_chain(self):
        """Retrieval chain combining retriever + LLM must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"RetrievalQA|RetrievalChain|create_retrieval_chain|stuff_documents|create_stuff_documents_chain", content):
                        found = True
                        break
            if found:
                break
        assert found, "No retrieval chain found"

    def test_prompt_template_for_rag(self):
        """RAG prompt template must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"context|retrieved|documents", content, re.IGNORECASE):
                        if re.search(r"[Pp]rompt[Tt]emplate|[Cc]hat[Pp]rompt", content):
                            found = True
                            break
            if found:
                break
        assert found, "No RAG prompt template found"

    def test_llm_integration(self):
        """LLM must be integrated for answer generation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ChatOpenAI|OpenAI|llm|ChatModel|BaseChatModel", content):
                        found = True
                        break
            if found:
                break
        assert found, "No LLM integration found"

    def test_query_or_invoke(self):
        """RAG system must accept queries and return answers."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\.invoke\(|\.run\(|query|question|ask", content):
                        if re.search(r"retriev|rag|chain", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No query/invoke functionality found"

    def test_metadata_handling(self):
        """Documents should include metadata."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"metadata|page_content|Document\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No metadata handling found"
