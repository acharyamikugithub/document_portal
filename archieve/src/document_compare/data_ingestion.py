import sys
from pathlib import Path
from datetime import datetime, timezone
import fitz
import uuid
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException


class DocumentIngestion:
    def __init__(self, base_dir: str = "data\\document_compare"):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)

        # ✅ Proper session_id initialization
        self.session_id = (
            f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_"
            f"{uuid.uuid4().hex[:8]}"
        )

        # ✅ Session-specific directory
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.log.info(
            "Document comparator initialized",
            session_id=self.session_id,
            session_path=str(self.session_path)
        )

    def save_uploaded_files(self, reference_file, actual_file):
        """
        Saves uploaded PDF files to the session directory.
        """
        try:
            if not reference_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Only PDF files are allowed")

            # ✅ Save inside session folder
            ref_path = self.session_path / reference_file.name
            act_path = self.session_path / actual_file.name

            with open(ref_path, "wb") as f:
                f.write(reference_file.getbuffer())

            with open(act_path, "wb") as f:
                f.write(actual_file.getbuffer())

            self.log.info(
                "Files saved successfully",
                reference_file=str(ref_path),
                actual_file=str(act_path)
            )

            return ref_path, act_path

        except Exception as e:
            self.log.error("Error saving uploaded files", error=str(e))
            raise DocumentPortalException(
                "An error occurred while saving uploaded files", sys
            )

    def read_pdf(self, pdf_path: Path) -> str:
        """
        Reads a PDF file and extracts text from each page.
        """
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}")

                all_text = []

                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    if text.strip():
                        all_text.append(f"\n---Page {page_num + 1}---\n{text}")

                self.log.info(
                    "PDF read successfully",
                    file=str(pdf_path),
                    pages=len(all_text)
                )

                return "\n".join(all_text)

        except Exception as e:
            self.log.error("Error reading PDF", error=str(e))
            raise DocumentPortalException(
                "An error occurred while reading the PDF.", sys
            )

    def combine_documents(self) -> str:
        """
        Combines all PDFs in the session directory into one text.
        """
        try:
            content_dict = {}
            doc_parts = []

            # ✅ Read from session directory
            for file_path in sorted(self.session_path.iterdir()):
                if file_path.is_file() and file_path.suffix == ".pdf":
                    content_dict[file_path.name] = self.read_pdf(file_path)

            for filename, content in content_dict.items():
                doc_parts.append(f"Document: {filename}\n{content}")

            combined_text = "\n\n".join(doc_parts)

            self.log.info(
                "Documents combined",
                count=len(doc_parts),
                session_id=self.session_id
            )

            return combined_text

        except Exception as e:
            self.log.error("Error combining documents", error=str(e))
            raise DocumentPortalException(
                "An error occurred while combining documents", sys
            )

    def clean_old_sessions(self, keep_latest: int = 3):
        """
        Keeps only the latest N session folders and deletes older ones.
        """
        try:
            # ✅ Only consider session directories
            sessions = [d for d in self.base_dir.iterdir() if d.is_dir()]

            # Sort by last modified time (latest first)
            sessions_sorted = sorted(
                sessions,
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )

            old_sessions = sessions_sorted[keep_latest:]

            for session in old_sessions:
                for file in session.iterdir():
                    file.unlink()
                session.rmdir()

                self.log.info(
                    "Old session deleted",
                    session=str(session)
                )

            self.log.info(
                "Session cleanup completed",
                kept=keep_latest,
                deleted=len(old_sessions)
            )

        except Exception as e:
            self.log.error("Error cleaning old sessions", error=str(e))
            raise DocumentPortalException(
                "An error occurred while cleaning old sessions", sys
            )