from llama_index.core import (
    SimpleDirectoryReader,
    DocumentSummaryIndex,
    VectorStoreIndex,
    StorageContext,
    Settings,
    get_response_synthesizer
)

from llama_index.core.node_parser import SemanticSplitterNodeParser # Llamaindex provides other text splitter like CodeSplitter, LangchainNodeParser, SentenceSplitter, SentenceWindowNodeParser, TokenTextSplitter, HierarchicalNodeParser
import chromadb
from chromadb.config import Settings as ChromaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from crewai_tools import LlamaIndexTool

import os
import logging
import sys
# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# Vector store local persistent directory
persist_vector_store_path = 'src/req_engineering_project/tools/chromadb/'

class QueryEngineToolset:
    def __init__(self, document_dir, model_name, api_key, collection_name, load_collection_status):
        self.document_dir = document_dir
        self.model_name = model_name
        self.api_key = api_key
        self.collection_name = collection_name
        self.load_collection_status = load_collection_status
        
        Settings.llm = OpenAI(model=self.model_name, api_key=self.api_key, temperature=0)
        Settings.embed_model = OpenAIEmbedding(model='text-embedding-3-small', api_key=self.api_key)
        Settings.text_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95, 
            embed_model=Settings.embed_model
        )

        # Load documents
        self.documents = self.load_documents(document_dir=self.document_dir)
         # Initialize vector store client
        self.chroma_client = self.initialize_vector_store_client()
        self.summary_index = self.create_summary_index(
            collection_name=self.collection_name, 
            load_collection_status=self.load_collection_status
        )
        self.semantic_search_index = self.create_vector_store_index(
            collection_name=self.collection_name, 
            load_collection_status=self.load_collection_status
        )
    
    def load_documents(self, document_dir):
        """
            Load documents from the specified directory.
        """
        try:
            reader = SimpleDirectoryReader(input_dir=document_dir, required_exts=['.pdf', '.docx', '.txt', '.md', 'mp3', '.mp4'])
            documents = reader.load_data()
            return documents
        except Exception as e:
            logging.error(f"Error loading documents: {e}")
            return []
        
    def initialize_vector_store_client(self):
        """
        Initialize the Chroma vector store client
        """
        try:
            chroma_client = chromadb.PersistentClient(
                path=persist_vector_store_path, 
                settings=ChromaSettings(allow_reset=True)
            )
            return chroma_client
        except Exception as e:
            logging.error(f"Error iinitializing vector store client: {e}")
            return None
        
    def initialize_chromadb_collection(self, chroma_client, collection_name, load_collection_status):
        """
        Create or load a Chroma DB collection for storing vectors.
        """
        try:
            collections_list = [col.name for col in chroma_client.list_collections()]
            if load_collection_status:
                try:
                    # Load existing collection
                    if collection_name in collections_list:
                        chromadb_collection = chroma_client.get_collection(name=collection_name)
                        logging.info(f"Loaded existing Chroma DB collection: {collection_name}")
                    else:
                        logging.error(f"Collection {collection_name} does not exist.")
                        return None
                except Exception as e:
                    logging.error(f"Error loading existing Chroma DB collection: {e}")
                    return None

            else:
                # Delete existing collection
                if collection_name in collections_list:
                    try:
                        chroma_client.delete_collection(name=collection_name)
                        logging.info(f"Deleted existing Chroma DB collection: {collection_name}")
                    except Exception as e:
                        logging.error(f"Error deleting existing Chroma DB collection: {e}")
                        return None
                
                # Create new collection
                try:
                    chromadb_collection = chroma_client.create_collection(name=collection_name)
                    logging.info(f"Created new Chroma DB collection: {collection_name}")
                except Exception as e:
                    logging.error(f"Error creating Chroma DB collection: {e}")
                    return None
            
            vector_store_instance = ChromaVectorStore(chroma_collection=chromadb_collection)
            logging.info(f"Chroma DB collection created or loaded successfully: {collection_name}")
            return vector_store_instance

        except Exception as e:
            logging.error(f"Error creating Chroma DB collection: {e}")
            return None

    def create_summary_index(self, collection_name, load_collection_status):
        """
            Create a summary index for the loaded documents.
        """
        try:
            logging.info(f"Creating or loading summary vector store with collection name: {collection_name}")
            summary_vector_store_instance = self.initialize_chromadb_collection(
                chroma_client=self.chroma_client,
                collection_name=f"{collection_name}-summary",
                load_collection_status=self.load_collection_status
            )
            summary_storage_context = StorageContext.from_defaults(vector_store=summary_vector_store_instance)
            response_synthesizer = get_response_synthesizer(
                llm=Settings.llm, response_mode="tree_summarize", use_async=True
            )

            if load_collection_status==True:
                logging.info("Loading Document summary index from existing vector store")
                summary_index =  VectorStoreIndex.from_vector_store(
                    vector_store=summary_vector_store_instance,
                    storage_context=summary_storage_context
                )
            else:
                logging.info("Creating DocumentSummaryIndex from documents")
                summary_index = DocumentSummaryIndex.from_documents(
                    documents=self.documents,
                    llm=Settings.llm,
                    transformations=[Settings.text_splitter],
                    response_synthesizer=response_synthesizer,
                    storage_context=summary_storage_context,
                    embed_model=Settings.embed_model,
                    show_progress=True,
                )
            logging.info("DocumentSummaryIndex created successfully")
            return summary_index

        except Exception as e:
            logging.error(f"Error creating summary index: {e}")
            return None

    def create_vector_store_index(self, collection_name, load_collection_status):
        """
        Create a vector store index for semantic search.
        """
        try:
            logging.info(f"Creating or loading semantic search vector store with collection name: {collection_name}")
            semantic_search_vector_store_instance = self.initialize_chromadb_collection(
                self.chroma_client,
                collection_name=f"{collection_name}-semantic_search",
                load_collection_status=self.load_collection_status
            )

            semantic_search_storage_context = StorageContext.from_defaults(
                vector_store=semantic_search_vector_store_instance
                )

            if load_collection_status==True:
                logging.info("Loading vector store index from existing vector store")
                vector_store_index = VectorStoreIndex.from_vector_store(
                    vector_store=semantic_search_vector_store_instance,
                    storage_context=semantic_search_storage_context
                )
            else:
                logging.info("Creating vector store index from documents")
                vector_store_index = VectorStoreIndex.from_documents(
                    documents=self.documents,
                    llm=Settings.llm,
                    transformations=[Settings.text_splitter],
                    embed_model=Settings.embed_model,
                    storage_context=semantic_search_storage_context,
                    show_progress=True,
                )
            logging.info("Vector store index created successfully")
            return vector_store_index
        except Exception as e:
            logging.error(f"Error creating vector store index: {e}")
            return None

    def create_tools(self):
        """
        Create query engine tools for interacting with the summary and vector store indices.
        """
        try:
            self.summary_query_engine = self.summary_index.as_query_engine(response_mode="tree_summarize", use_async=True, streaming=True)
            self.vector_store_query_engine = self.semantic_search_index.as_query_engine(similarity_top_k=5, llm=Settings.llm, streaming=True)
            self.summary_tool = LlamaIndexTool.from_query_engine(
                self.summary_query_engine,
                name="Summary Index Query Tool",
                description="Use this tool to query summaries over the given document(s)."
            )
            self.vector_store_tool = LlamaIndexTool.from_query_engine(
                self.vector_store_query_engine,
                name="Vector Store Index Query Tool",
                description="Use this tool to semantic search over the given document(s)."
            )
            return self.summary_tool, self.vector_store_tool
        except Exception as e:
            logging.error(f"Error creating query engine tools: {e}")
            return None, None
        




