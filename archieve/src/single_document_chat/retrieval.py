import sys
import os
from dotenv import load_dotenv

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from utils.model_loader import ModelLoader
from exception.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from prompt.prompt_library import PROMPT_REGISTRY
from model.models import PromptType


class ConversationalRAG:
    def __init__(self, session_id, retriever):
        try:
            load_dotenv()

            self.log = CustomLogger().get_logger(__name__)
            self.session_id = session_id
            self.retriever = retriever

            # ✅ Load LLM
            self.llm = self._load_llm()

            # ✅ Prompts
            self.contextualize_prompt = PROMPT_REGISTRY[
                PromptType.CONTEXTUALIZE_QUESTION.value
            ]
            self.qa_prompt = PROMPT_REGISTRY[
                PromptType.CONTEXT_QA.value
            ]

            # ✅ Chains
            self.history_aware_retriever = create_history_aware_retriever(
                self.llm,
                self.retriever,
                self.contextualize_prompt
            )

            self.qa_chain = create_stuff_documents_chain(
                self.llm,
                self.qa_prompt
            )

            self.rag_chain = create_retrieval_chain(
                self.history_aware_retriever,
                self.qa_chain
            )

            # ✅ Memory store
            self.store = {}

            self.chain = RunnableWithMessageHistory(
                self.rag_chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="chat_history",
                output_messages_key="answer"
            )

            self.log.info(
                "Conversational RAG initialized successfully",
                session_id=session_id
            )

        except Exception as e:
            self.log.error(
                "Error initializing ConversationalRAG",
                error=str(e),
                session_id=session_id
            )
            raise DocumentPortalException(
                "Failed to initialize ConversationalRAG",
                sys
            )

    # ✅ Load LLM
    def _load_llm(self):
        try:
            model_loader = ModelLoader()
            llm = model_loader.load_llm() 
            self.log.info("LLM loaded successfully")
            return llm

        except Exception as e:
            self.log.error("Error loading LLM", error=str(e))
            raise DocumentPortalException("Failed to load LLM", sys)

    # ✅ FIXED: Session memory
    def _get_session_history(self, session_id):
        try:
            if session_id not in self.store:
                self.store[session_id] = ChatMessageHistory()

            return self.store[session_id]

        except Exception as e:
            self.log.error("Error retrieving session history", error=str(e))
            raise DocumentPortalException(
                "Failed to retrieve session history",
                sys
            )

    # ❌ REMOVE THIS METHOD (not needed)
    # You are already passing retriever from test.py
    # def load_retriever_from_faiss(...):

    # ✅ Invoke
    def invoke(self, user_input: str) -> str:
        try:
            response = self.chain.invoke(
                {"input": user_input},
                config={"session_id": self.session_id}
            )

            answer = response.get("answer", "No Answer")

            if not answer:
                self.log.warning(
                    "RAG chain returned empty answer",
                    session_id=self.session_id
                )

            self.log.info(
                "RAG chain invoked successfully",
                session_id=self.session_id,
                user_input=user_input,
                answer_preview=answer[:150]
            )

            return answer

        except Exception as e:
            self.log.error(
                "Failed to invoke conversational RAG",
                error=str(e),
                session_id=self.session_id
            )
            raise DocumentPortalException(
                "Failed to invoke RAG chain",
                sys
            )