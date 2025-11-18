from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

KNOWLEDGE_VECTOR_STORE_ID = os.getenv("KNOWLEDGE_VECTOR_STORE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not KNOWLEDGE_VECTOR_STORE_ID:
    raise RuntimeError("KNOWLEDGE_VECTOR_STORE_ID is not set in environment variables")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in environment variables")

_client = OpenAI(api_key=OPENAI_API_KEY)

_IMMATRICULATION_REGEX = re.compile(r"^[A-Z]{2}-[A-Z0-9]{3}-[A-Z0-9]{2}$")


def extract_immatriculation_from_path(path: str) -> str | None:
    """Extract immatriculation from a path or filename.
    
    Format expected: GH-XXX-XX (2 letters, 3 alphanumeric, 2 alphanumeric)
    
    Args:
        path: Path string or filename
    
    Returns:
        Extracted immatriculation or None if not found
    """
    path_obj = Path(path)
    name = path_obj.name
    
    if _IMMATRICULATION_REGEX.match(name):
        return name
    
    stem = path_obj.stem
    if _IMMATRICULATION_REGEX.match(stem):
        return stem
    
    parts = name.split("-")
    if len(parts) >= 3:
        candidate = "-".join(parts[:3])
        if _IMMATRICULATION_REGEX.match(candidate):
            return candidate
    
    return None


def list_vector_store_files() -> list[dict[str, Any]]:
    """List all files in the vector store.
    
    Returns:
        List of file dictionaries with metadata (id, filename, status, created_at, bytes, purpose)
    """
    if not KNOWLEDGE_VECTOR_STORE_ID:
        raise RuntimeError("KNOWLEDGE_VECTOR_STORE_ID is not configured")
    
    try:
        files = _client.vector_stores.files.list(
            vector_store_id=KNOWLEDGE_VECTOR_STORE_ID,
            limit=100
        )
        
        result = []
        for file in files.data:
            file_info = _client.files.retrieve(file.id)
            attributes = getattr(file, "attributes", None) or {}
            result.append({
                "id": file.id,
                "filename": getattr(file_info, "filename", "unknown"),
                "status": file.status,
                "created_at": file.created_at,
                "bytes": getattr(file_info, "bytes", 0),
                "purpose": getattr(file_info, "purpose", "assistants"),
                "immatriculation": attributes.get("immatriculation") if isinstance(attributes, dict) else None,
                "client": attributes.get("client") if isinstance(attributes, dict) else None,
            })
        
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to list vector store files: {str(e)}") from e


def upload_file_to_vector_store(
    file_path: str | Path,
    file_content: bytes | None = None,
    immatriculation: str | None = None,
    client: str | None = None,
) -> dict[str, Any]:
    """Upload a single file to OpenAI Files API and add it to the vector store.
    
    Args:
        file_path: Path to the file or filename string
        file_content: Optional file content as bytes (if provided, file_path is used as filename)
        immatriculation: Optional immatriculation metadata (e.g., "GH-XXX-XX")
        client: Optional client metadata (e.g., "GROUPE BEL", "HOMECARE")
    
    Returns:
        Dictionary with file metadata (id, filename, status, created_at, bytes, immatriculation, client)
    """
    if not KNOWLEDGE_VECTOR_STORE_ID:
        raise RuntimeError("KNOWLEDGE_VECTOR_STORE_ID is not configured")
    
    try:
        path = Path(file_path)
        filename = path.name
        
        if file_content is None:
            with open(path, "rb") as f:
                file_content = f.read()
        
        file_obj = _client.files.create(
            file=(filename, file_content),
            purpose="assistants",
        )
        
        attributes = {}
        if immatriculation:
            attributes["immatriculation"] = immatriculation
        if client:
            attributes["client"] = client
        
        vector_store_file = _client.vector_stores.files.create(
            vector_store_id=KNOWLEDGE_VECTOR_STORE_ID,
            file_id=file_obj.id,
            attributes=attributes if attributes else None,
        )
        
        return {
            "id": file_obj.id,
            "filename": filename,
            "status": vector_store_file.status,
            "created_at": file_obj.created_at,
            "bytes": file_obj.bytes,
            "purpose": file_obj.purpose,
            "immatriculation": immatriculation,
            "client": client,
        }
    except Exception as e:
        raise RuntimeError(f"Failed to upload file {file_path}: {str(e)}") from e


def upload_files_batch(file_paths: list[str | Path]) -> list[dict[str, Any]]:
    """Upload multiple files to OpenAI Files API and add them to the vector store.
    
    Args:
        file_paths: List of file paths to upload
    
    Returns:
        List of dictionaries with file metadata for each uploaded file
    """
    results = []
    errors = []
    
    for file_path in file_paths:
        try:
            result = upload_file_to_vector_store(file_path)
            results.append(result)
        except Exception as e:
            errors.append({"file": str(file_path), "error": str(e)})
    
    if errors:
        return {
            "success": results,
            "errors": errors
        }
    
    return results


def delete_file_from_vector_store(file_id: str) -> dict[str, Any]:
    """Delete a file from both the vector store and the Files API.
    
    Args:
        file_id: The OpenAI file ID to delete
    
    Returns:
        Dictionary with deletion status
    """
    if not KNOWLEDGE_VECTOR_STORE_ID:
        raise RuntimeError("KNOWLEDGE_VECTOR_STORE_ID is not configured")
    
    try:
        _client.vector_stores.files.delete(
            vector_store_id=KNOWLEDGE_VECTOR_STORE_ID,
            file_id=file_id
        )
        
        _client.files.delete(file_id)
        
        return {
            "success": True,
            "file_id": file_id,
            "message": "File deleted from vector store and Files API"
        }
    except Exception as e:
        raise RuntimeError(f"Failed to delete file {file_id}: {str(e)}") from e

