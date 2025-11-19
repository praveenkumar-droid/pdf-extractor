"""
PHASE 10: CONTEXT WINDOWS FOR LARGE DOCUMENTS
Intelligent chunking and context management for large PDFs

This module handles:
1. Smart document chunking
2. Context preservation across chunks
3. Overlap management for continuity
4. Memory-efficient processing
5. Chunk reassembly with deduplication

Purpose: Process large documents without memory issues while maintaining context
"""

import re
from typing import List, Dict, Optional, Tuple, Any, Generator
from dataclasses import dataclass, field
from pathlib import Path
import time


@dataclass
class Chunk:
    """A single chunk of document content"""
    chunk_id: int
    page_start: int
    page_end: int
    content: str
    word_count: int
    char_count: int
    has_overlap_start: bool = False
    has_overlap_end: bool = False
    overlap_start_text: str = ""
    overlap_end_text: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'chunk_id': self.chunk_id,
            'page_start': self.page_start,
            'page_end': self.page_end,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'has_overlap_start': self.has_overlap_start,
            'has_overlap_end': self.has_overlap_end
        }


@dataclass
class ChunkingStrategy:
    """Configuration for chunking strategy"""
    max_chunk_size: int = 50000      # Max characters per chunk
    overlap_size: int = 500          # Characters to overlap between chunks
    min_chunk_size: int = 1000       # Minimum chunk size
    chunk_by: str = "characters"     # "characters", "words", "pages", "sections"
    preserve_sections: bool = True   # Try to break at section boundaries
    preserve_paragraphs: bool = True # Try to break at paragraph boundaries


@dataclass
class ContextWindow:
    """Manages context across chunks"""
    window_size: int                 # Size of context window
    chunks: List[Chunk]              # All chunks
    current_chunk: int = 0           # Current chunk index
    context_before: str = ""         # Context from previous chunk
    context_after: str = ""          # Context for next chunk
    
    def get_current_with_context(self) -> str:
        """Get current chunk with surrounding context"""
        if not self.chunks:
            return ""
        
        chunk = self.chunks[self.current_chunk]
        
        # Build full context
        result = ""
        if self.context_before:
            result += f"[...previous context...]\n{self.context_before}\n\n"
        
        result += chunk.content
        
        if self.context_after:
            result += f"\n\n{self.context_after}\n[...continues...]"
        
        return result


@dataclass
class ReassemblyResult:
    """Result of chunk reassembly"""
    full_text: str
    total_chunks: int
    total_pages: int
    total_words: int
    duplicates_removed: int
    processing_time: float
    
    def to_dict(self) -> Dict:
        return {
            'total_chunks': self.total_chunks,
            'total_pages': self.total_pages,
            'total_words': self.total_words,
            'duplicates_removed': self.duplicates_removed,
            'processing_time': round(self.processing_time, 2)
        }


class LargeDocumentProcessor:
    """
    Processes large documents using context windows.
    
    Features:
    - Smart chunking by size, pages, or sections
    - Context preservation with overlaps
    - Memory-efficient streaming
    - Intelligent reassembly with deduplication
    """
    
    def __init__(self, 
                 strategy: Optional[ChunkingStrategy] = None,
                 verbose: bool = False):
        """
        Initialize processor.
        
        Args:
            strategy: Chunking strategy configuration
            verbose: Print progress information
        """
        self.strategy = strategy or ChunkingStrategy()
        self.verbose = verbose
        
        # Section patterns for smart breaking
        self.section_patterns = [
            r'^#{1,6}\s+',              # Markdown headers
            r'^\d+\.\s+',               # Numbered sections
            r'^\d+\.\d+\s+',            # Sub-sections
            r'^第\d+[章条節項]',          # Japanese sections
            r'^[一二三四五六七八九十]+[、.]', # Japanese numbering
            r'^={3,}',                  # Section breaks
            r'^-{3,}',                  # Horizontal rules
        ]
    
    def chunk_document(self, 
                       pages: List[str], 
                       filename: str = "") -> List[Chunk]:
        """
        Chunk a document into manageable pieces.
        
        Args:
            pages: List of page texts
            filename: Document filename for reference
            
        Returns:
            List of Chunk objects
        """
        if self.verbose:
            print(f"\n[Context Windows] Chunking document...")
            print(f"  Total pages: {len(pages)}")
            total_chars = sum(len(p) for p in pages)
            print(f"  Total characters: {total_chars:,}")
        
        if self.strategy.chunk_by == "pages":
            chunks = self._chunk_by_pages(pages)
        elif self.strategy.chunk_by == "sections":
            chunks = self._chunk_by_sections(pages)
        elif self.strategy.chunk_by == "words":
            chunks = self._chunk_by_words(pages)
        else:  # characters (default)
            chunks = self._chunk_by_characters(pages)
        
        # Add overlaps
        chunks = self._add_overlaps(chunks)
        
        if self.verbose:
            print(f"  Created {len(chunks)} chunks")
            avg_size = sum(c.char_count for c in chunks) / len(chunks) if chunks else 0
            print(f"  Average chunk size: {avg_size:,.0f} characters")
        
        return chunks
    
    def _chunk_by_characters(self, pages: List[str]) -> List[Chunk]:
        """Chunk by character count"""
        chunks = []
        current_content = ""
        current_pages = []
        chunk_id = 0
        
        for page_num, page_text in enumerate(pages, 1):
            # Check if adding this page exceeds limit
            if (len(current_content) + len(page_text) > self.strategy.max_chunk_size 
                and len(current_content) >= self.strategy.min_chunk_size):
                
                # Save current chunk
                chunks.append(self._create_chunk(
                    chunk_id, current_pages, current_content
                ))
                chunk_id += 1
                current_content = ""
                current_pages = []
            
            # Add page to current chunk
            if current_content:
                current_content += "\n\n"
            current_content += page_text
            current_pages.append(page_num)
        
        # Save final chunk
        if current_content:
            chunks.append(self._create_chunk(
                chunk_id, current_pages, current_content
            ))
        
        return chunks
    
    def _chunk_by_pages(self, pages: List[str]) -> List[Chunk]:
        """Chunk by page count"""
        # Calculate pages per chunk based on average page size
        total_chars = sum(len(p) for p in pages)
        avg_page_chars = total_chars / len(pages) if pages else 0
        pages_per_chunk = max(1, int(self.strategy.max_chunk_size / avg_page_chars))
        
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(pages), pages_per_chunk):
            chunk_pages = pages[i:i + pages_per_chunk]
            page_nums = list(range(i + 1, i + len(chunk_pages) + 1))
            content = "\n\n".join(chunk_pages)
            
            chunks.append(self._create_chunk(chunk_id, page_nums, content))
            chunk_id += 1
        
        return chunks
    
    def _chunk_by_sections(self, pages: List[str]) -> List[Chunk]:
        """Chunk by section boundaries"""
        # First, combine all pages
        full_text = "\n\n".join(pages)
        
        # Find section boundaries
        boundaries = self._find_section_boundaries(full_text)
        
        if not boundaries:
            # Fall back to character chunking
            return self._chunk_by_characters(pages)
        
        # Create chunks at section boundaries
        chunks = []
        chunk_id = 0
        current_start = 0
        current_content = ""
        
        for boundary in boundaries:
            section_text = full_text[current_start:boundary]
            
            if (len(current_content) + len(section_text) > self.strategy.max_chunk_size
                and len(current_content) >= self.strategy.min_chunk_size):
                
                # Save current chunk
                page_nums = self._estimate_page_numbers(current_content, pages)
                chunks.append(self._create_chunk(chunk_id, page_nums, current_content))
                chunk_id += 1
                current_content = ""
            
            current_content += section_text
            current_start = boundary
        
        # Add remaining content
        remaining = full_text[current_start:]
        current_content += remaining
        
        if current_content:
            page_nums = self._estimate_page_numbers(current_content, pages)
            chunks.append(self._create_chunk(chunk_id, page_nums, current_content))
        
        return chunks
    
    def _chunk_by_words(self, pages: List[str]) -> List[Chunk]:
        """Chunk by word count"""
        # Convert max_chunk_size from chars to words (estimate 5 chars/word)
        max_words = self.strategy.max_chunk_size // 5
        
        chunks = []
        current_content = ""
        current_pages = []
        current_words = 0
        chunk_id = 0
        
        for page_num, page_text in enumerate(pages, 1):
            page_words = len(page_text.split())
            
            if (current_words + page_words > max_words 
                and current_words >= self.strategy.min_chunk_size // 5):
                
                # Save current chunk
                chunks.append(self._create_chunk(
                    chunk_id, current_pages, current_content
                ))
                chunk_id += 1
                current_content = ""
                current_pages = []
                current_words = 0
            
            if current_content:
                current_content += "\n\n"
            current_content += page_text
            current_pages.append(page_num)
            current_words += page_words
        
        # Save final chunk
        if current_content:
            chunks.append(self._create_chunk(
                chunk_id, current_pages, current_content
            ))
        
        return chunks
    
    def _find_section_boundaries(self, text: str) -> List[int]:
        """Find section boundary positions in text"""
        boundaries = []
        
        for pattern in self.section_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                boundaries.append(match.start())
        
        # Sort and deduplicate
        boundaries = sorted(set(boundaries))
        
        return boundaries
    
    def _estimate_page_numbers(self, content: str, pages: List[str]) -> List[int]:
        """Estimate which pages are in a chunk of content"""
        page_nums = []
        
        for page_num, page_text in enumerate(pages, 1):
            # Check if any significant part of the page is in the content
            if page_text[:100] in content or page_text[-100:] in content:
                page_nums.append(page_num)
        
        return page_nums if page_nums else [1]
    
    def _create_chunk(self, chunk_id: int, page_nums: List[int], content: str) -> Chunk:
        """Create a Chunk object"""
        return Chunk(
            chunk_id=chunk_id,
            page_start=min(page_nums) if page_nums else 1,
            page_end=max(page_nums) if page_nums else 1,
            content=content,
            word_count=len(content.split()),
            char_count=len(content)
        )
    
    def _add_overlaps(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add overlap text between chunks for context continuity"""
        if len(chunks) < 2:
            return chunks
        
        overlap_size = self.strategy.overlap_size
        
        for i in range(len(chunks)):
            chunk = chunks[i]
            
            # Add overlap from previous chunk
            if i > 0:
                prev_content = chunks[i - 1].content
                chunk.has_overlap_start = True
                chunk.overlap_start_text = prev_content[-overlap_size:]
            
            # Add overlap for next chunk
            if i < len(chunks) - 1:
                chunk.has_overlap_end = True
                chunk.overlap_end_text = chunk.content[-overlap_size:]
        
        return chunks
    
    def create_context_window(self, chunks: List[Chunk]) -> ContextWindow:
        """Create a context window for navigating chunks"""
        return ContextWindow(
            window_size=self.strategy.overlap_size,
            chunks=chunks
        )
    
    def process_chunks_streaming(self, 
                                  chunks: List[Chunk],
                                  processor_func) -> Generator[Tuple[int, Any], None, None]:
        """
        Process chunks in streaming fashion.
        
        Args:
            chunks: List of chunks to process
            processor_func: Function to apply to each chunk
            
        Yields:
            Tuple of (chunk_id, result)
        """
        for chunk in chunks:
            # Build context
            context = ""
            if chunk.has_overlap_start:
                context = chunk.overlap_start_text
            
            # Process with context
            result = processor_func(chunk.content, context)
            
            yield chunk.chunk_id, result
    
    def reassemble_chunks(self, 
                          chunks: List[Chunk],
                          processed_contents: Optional[List[str]] = None) -> ReassemblyResult:
        """
        Reassemble chunks into complete document.
        
        Args:
            chunks: Original chunks
            processed_contents: Processed content for each chunk (optional)
            
        Returns:
            ReassemblyResult with complete text
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"\n[Context Windows] Reassembling {len(chunks)} chunks...")
        
        # Use original or processed content
        contents = processed_contents if processed_contents else [c.content for c in chunks]
        
        # Remove overlaps to avoid duplication
        deduplicated = []
        duplicates_removed = 0
        
        for i, content in enumerate(contents):
            if i == 0:
                # First chunk - use as is
                deduplicated.append(content)
            else:
                # Remove overlap from start
                prev_overlap = chunks[i].overlap_start_text
                if prev_overlap and content.startswith(prev_overlap):
                    content = content[len(prev_overlap):]
                    duplicates_removed += 1
                
                deduplicated.append(content)
        
        # Combine
        full_text = "\n\n".join(deduplicated)
        
        # Clean up any double spacing from joins
        full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)
        
        processing_time = time.time() - start_time
        
        result = ReassemblyResult(
            full_text=full_text,
            total_chunks=len(chunks),
            total_pages=max(c.page_end for c in chunks) if chunks else 0,
            total_words=len(full_text.split()),
            duplicates_removed=duplicates_removed,
            processing_time=processing_time
        )
        
        if self.verbose:
            print(f"  Duplicates removed: {duplicates_removed}")
            print(f"  Final word count: {result.total_words:,}")
        
        return result
    
    def get_chunk_for_page(self, chunks: List[Chunk], page_num: int) -> Optional[Chunk]:
        """Get the chunk containing a specific page"""
        for chunk in chunks:
            if chunk.page_start <= page_num <= chunk.page_end:
                return chunk
        return None
    
    def estimate_memory_usage(self, pages: List[str]) -> Dict[str, int]:
        """
        Estimate memory usage for processing.
        
        Returns:
            Dict with memory estimates in bytes
        """
        total_chars = sum(len(p) for p in pages)
        
        # Estimate: ~2 bytes per char for Python strings
        text_memory = total_chars * 2
        
        # Estimate chunk overhead
        num_chunks = max(1, total_chars // self.strategy.max_chunk_size)
        chunk_overhead = num_chunks * 1000  # ~1KB per chunk object
        
        # Total with 50% buffer for processing
        total_estimate = int((text_memory + chunk_overhead) * 1.5)
        
        return {
            'text_bytes': text_memory,
            'chunk_overhead': chunk_overhead,
            'total_estimate': total_estimate,
            'total_mb': total_estimate // (1024 * 1024)
        }
    
    def print_chunk_summary(self, chunks: List[Chunk]):
        """Print summary of chunks"""
        print("\n" + "="*60)
        print("CHUNK SUMMARY")
        print("="*60)
        
        print(f"\nTotal chunks: {len(chunks)}")
        
        if chunks:
            total_chars = sum(c.char_count for c in chunks)
            total_words = sum(c.word_count for c in chunks)
            
            print(f"Total characters: {total_chars:,}")
            print(f"Total words: {total_words:,}")
            print(f"Pages covered: {chunks[0].page_start} - {chunks[-1].page_end}")
            
            print("\nChunk details:")
            for chunk in chunks:
                overlap_info = ""
                if chunk.has_overlap_start:
                    overlap_info += " [←overlap]"
                if chunk.has_overlap_end:
                    overlap_info += " [overlap→]"
                
                print(f"  Chunk {chunk.chunk_id}: "
                      f"Pages {chunk.page_start}-{chunk.page_end}, "
                      f"{chunk.word_count:,} words, "
                      f"{chunk.char_count:,} chars"
                      f"{overlap_info}")
        
        print("="*60 + "\n")


class ContextWindowManager:
    """
    Manages context windows for LLM processing.
    
    Handles token limits and context preservation for LLM-based operations.
    """
    
    def __init__(self, 
                 max_tokens: int = 4000,
                 chars_per_token: float = 4.0):
        """
        Initialize context window manager.
        
        Args:
            max_tokens: Maximum tokens for LLM context
            chars_per_token: Estimated characters per token
        """
        self.max_tokens = max_tokens
        self.chars_per_token = chars_per_token
        self.max_chars = int(max_tokens * chars_per_token)
    
    def fit_to_context(self, 
                       text: str, 
                       preserve_start: int = 500,
                       preserve_end: int = 500) -> str:
        """
        Fit text to context window, preserving start and end.
        
        Args:
            text: Text to fit
            preserve_start: Characters to preserve at start
            preserve_end: Characters to preserve at end
            
        Returns:
            Text fitting within context window
        """
        if len(text) <= self.max_chars:
            return text
        
        # Calculate how much to keep
        available = self.max_chars - preserve_start - preserve_end - 50  # Buffer
        
        if available < 100:
            # Not enough room, just truncate
            return text[:self.max_chars] + "\n[...truncated...]"
        
        # Keep start and end
        start = text[:preserve_start]
        end = text[-preserve_end:]
        
        # Add middle indicator
        return f"{start}\n\n[...{len(text) - preserve_start - preserve_end:,} characters omitted...]\n\n{end}"
    
    def split_for_context(self, 
                          text: str,
                          overlap: int = 200) -> List[str]:
        """
        Split text into context-sized pieces with overlap.
        
        Args:
            text: Text to split
            overlap: Characters to overlap
            
        Returns:
            List of text pieces
        """
        if len(text) <= self.max_chars:
            return [text]
        
        pieces = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chars
            
            if end >= len(text):
                pieces.append(text[start:])
                break
            
            # Try to break at paragraph
            break_point = text.rfind('\n\n', start + self.max_chars - 1000, end)
            if break_point == -1:
                # Try sentence
                break_point = text.rfind('. ', start + self.max_chars - 500, end)
            if break_point == -1:
                break_point = end
            
            pieces.append(text[start:break_point])
            start = break_point - overlap
        
        return pieces
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return int(len(text) / self.chars_per_token)


# Convenience functions
def chunk_large_document(pages: List[str], 
                         max_chunk_size: int = 50000,
                         verbose: bool = True) -> List[Chunk]:
    """
    Quick function to chunk a large document.
    
    Args:
        pages: List of page texts
        max_chunk_size: Maximum characters per chunk
        verbose: Print progress
        
    Returns:
        List of Chunk objects
    """
    strategy = ChunkingStrategy(max_chunk_size=max_chunk_size)
    processor = LargeDocumentProcessor(strategy=strategy, verbose=verbose)
    return processor.chunk_document(pages)


def process_large_pdf(pdf_path: str,
                      extractor,
                      max_chunk_size: int = 50000,
                      verbose: bool = True) -> Tuple[str, ReassemblyResult]:
    """
    Process a large PDF with chunking.
    
    Args:
        pdf_path: Path to PDF file
        extractor: Extractor to use
        max_chunk_size: Maximum characters per chunk
        verbose: Print progress
        
    Returns:
        Tuple of (full_text, reassembly_result)
    """
    import pdfplumber
    
    # Extract pages
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    
    # Chunk
    strategy = ChunkingStrategy(max_chunk_size=max_chunk_size)
    processor = LargeDocumentProcessor(strategy=strategy, verbose=verbose)
    chunks = processor.chunk_document(pages, Path(pdf_path).name)
    
    # Reassemble
    result = processor.reassemble_chunks(chunks)
    
    return result.full_text, result


# Demo
if __name__ == "__main__":
    # Demo with sample pages
    sample_pages = [
        "Page 1 content. " * 100,
        "Page 2 content. " * 100,
        "Page 3 content. " * 100,
        "Page 4 content. " * 100,
        "Page 5 content. " * 100,
    ]
    
    print("Context Windows Demo")
    print("="*60)
    
    # Create processor
    strategy = ChunkingStrategy(
        max_chunk_size=5000,
        overlap_size=200
    )
    processor = LargeDocumentProcessor(strategy=strategy, verbose=True)
    
    # Chunk
    chunks = processor.chunk_document(sample_pages, "demo.pdf")
    
    # Print summary
    processor.print_chunk_summary(chunks)
    
    # Reassemble
    result = processor.reassemble_chunks(chunks)
    
    print(f"\nReassembly result:")
    print(f"  Total words: {result.total_words:,}")
    print(f"  Duplicates removed: {result.duplicates_removed}")
    print(f"  Processing time: {result.processing_time:.3f}s")
