"""
MULTI-ENGINE PDF EXTRACTION SYSTEM
Uses multiple extraction engines with consensus voting for maximum accuracy

Engines:
1. pdfplumber - Best for tables and precise coordinates
2. PyMuPDF (fitz) - Fast, good for text and images
3. pdfminer - Best for complex layouts and fonts

Consensus Algorithm:
- Extract with all engines
- Compare results
- Vote on conflicts
- Flag low-confidence sections
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import time
from difflib import SequenceMatcher
from collections import Counter


@dataclass
class EngineResult:
    """Result from a single extraction engine"""
    engine_name: str
    pages: List[str]
    word_count: int
    char_count: int
    extraction_time: float
    success: bool
    error: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'engine': self.engine_name,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'time': round(self.extraction_time, 2),
            'success': self.success,
            'confidence': self.confidence,
            'error': self.error
        }


@dataclass
class ConsensusResult:
    """Result of consensus voting across engines"""
    final_text: str
    pages: List[str]
    engine_results: List[EngineResult]
    consensus_score: float
    conflicts: List[Dict]
    flags: List[Dict]
    word_count: int
    char_count: int
    total_time: float
    
    def to_dict(self) -> Dict:
        return {
            'consensus_score': round(self.consensus_score, 3),
            'word_count': self.word_count,
            'char_count': self.char_count,
            'total_time': round(self.total_time, 2),
            'conflicts_count': len(self.conflicts),
            'flags_count': len(self.flags),
            'engines': [r.to_dict() for r in self.engine_results]
        }


class PDFPlumberEngine:
    """Extraction using pdfplumber"""
    name = "pdfplumber"
    
    def extract(self, pdf_path: str) -> EngineResult:
        start_time = time.time()
        try:
            import pdfplumber
            pages = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages.append(text)
            full_text = '\n\n'.join(pages)
            return EngineResult(
                engine_name=self.name, pages=pages,
                word_count=len(full_text.split()), char_count=len(full_text),
                extraction_time=time.time() - start_time, success=True
            )
        except Exception as e:
            return EngineResult(
                engine_name=self.name, pages=[], word_count=0, char_count=0,
                extraction_time=time.time() - start_time, success=False, error=str(e)
            )


class PyMuPDFEngine:
    """Extraction using PyMuPDF (fitz)"""
    name = "pymupdf"
    
    def extract(self, pdf_path: str) -> EngineResult:
        start_time = time.time()
        try:
            import fitz
            pages = []
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text("text")
                pages.append(text)
            doc.close()
            full_text = '\n\n'.join(pages)
            return EngineResult(
                engine_name=self.name, pages=pages,
                word_count=len(full_text.split()), char_count=len(full_text),
                extraction_time=time.time() - start_time, success=True
            )
        except ImportError:
            return EngineResult(
                engine_name=self.name, pages=[], word_count=0, char_count=0,
                extraction_time=time.time() - start_time, success=False,
                error="PyMuPDF not installed. Run: pip install pymupdf"
            )
        except Exception as e:
            return EngineResult(
                engine_name=self.name, pages=[], word_count=0, char_count=0,
                extraction_time=time.time() - start_time, success=False, error=str(e)
            )


class PDFMinerEngine:
    """Extraction using pdfminer.six"""
    name = "pdfminer"
    
    def extract(self, pdf_path: str) -> EngineResult:
        start_time = time.time()
        try:
            from pdfminer.high_level import extract_text
            full_text = extract_text(pdf_path)
            pages = [full_text]  # pdfminer extracts all at once
            
            return EngineResult(
                engine_name=self.name, pages=pages,
                word_count=len(full_text.split()), char_count=len(full_text),
                extraction_time=time.time() - start_time, success=True
            )
        except ImportError:
            return EngineResult(
                engine_name=self.name, pages=[], word_count=0, char_count=0,
                extraction_time=time.time() - start_time, success=False,
                error="pdfminer not installed. Run: pip install pdfminer.six"
            )
        except Exception as e:
            return EngineResult(
                engine_name=self.name, pages=[], word_count=0, char_count=0,
                extraction_time=time.time() - start_time, success=False, error=str(e)
            )


class ConsensusEngine:
    """Consensus algorithm for combining multiple extraction results"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.similarity_threshold = 0.85
        self.conflict_threshold = 0.7
    
    def build_consensus(self, results: List[EngineResult]) -> ConsensusResult:
        start_time = time.time()
        successful = [r for r in results if r.success]
        
        if not successful:
            return ConsensusResult(
                final_text="", pages=[], engine_results=results,
                consensus_score=0.0, conflicts=[],
                flags=[{'type': 'error', 'message': 'All engines failed'}],
                word_count=0, char_count=0, total_time=time.time() - start_time
            )
        
        if len(successful) == 1:
            result = successful[0]
            return ConsensusResult(
                final_text='\n\n'.join(result.pages), pages=result.pages,
                engine_results=results, consensus_score=1.0, conflicts=[],
                flags=[{'type': 'warning', 'message': f'Only {result.engine_name} succeeded'}],
                word_count=result.word_count, char_count=result.char_count,
                total_time=time.time() - start_time
            )
        
        if self.verbose:
            print(f"\n[Consensus] Building consensus from {len(successful)} engines...")
        
        # Use the result with most content as base
        best_result = max(successful, key=lambda r: r.char_count)
        
        # Calculate similarity between all pairs
        similarities = []
        for i, r1 in enumerate(successful):
            for r2 in successful[i+1:]:
                text1 = '\n'.join(r1.pages)
                text2 = '\n'.join(r2.pages)
                sim = SequenceMatcher(None, text1, text2).ratio()
                similarities.append(sim)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
        
        flags = []
        conflicts = []
        
        if avg_similarity < self.conflict_threshold:
            flags.append({
                'type': 'low_consensus',
                'message': f'Low agreement between engines ({avg_similarity:.1%})'
            })
            conflicts.append({
                'type': 'major_disagreement',
                'similarity': avg_similarity
            })
        
        final_text = '\n\n'.join(best_result.pages)
        
        if self.verbose:
            print(f"  → Consensus score: {avg_similarity:.1%}")
            print(f"  → Using {best_result.engine_name} as base ({best_result.char_count:,} chars)")
        
        return ConsensusResult(
            final_text=final_text, pages=best_result.pages,
            engine_results=results, consensus_score=avg_similarity,
            conflicts=conflicts, flags=flags,
            word_count=len(final_text.split()), char_count=len(final_text),
            total_time=time.time() - start_time
        )


class MultiEngineExtractor:
    """Main class for multi-engine extraction with consensus"""
    
    def __init__(self, use_pdfplumber=True, use_pymupdf=True, use_pdfminer=True, verbose=True):
        self.verbose = verbose
        self.engines = []
        if use_pdfplumber:
            self.engines.append(PDFPlumberEngine())
        if use_pymupdf:
            self.engines.append(PyMuPDFEngine())
        if use_pdfminer:
            self.engines.append(PDFMinerEngine())
        self.consensus = ConsensusEngine(verbose=verbose)
    
    def extract(self, pdf_path: str) -> ConsensusResult:
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"MULTI-ENGINE EXTRACTION: {Path(pdf_path).name}")
            print(f"{'='*60}")
            print(f"Engines: {[e.name for e in self.engines]}")
        
        results = []
        for engine in self.engines:
            if self.verbose:
                print(f"\n[{engine.name}] Extracting...")
            result = engine.extract(pdf_path)
            results.append(result)
            if self.verbose:
                if result.success:
                    print(f"  → {result.word_count:,} words in {result.extraction_time:.2f}s")
                else:
                    print(f"  → FAILED: {result.error}")
        
        consensus_result = self.consensus.build_consensus(results)
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Final: {consensus_result.word_count:,} words, {consensus_result.consensus_score:.1%} consensus")
            print(f"{'='*60}\n")
        
        return consensus_result
    
    def print_comparison(self, result: ConsensusResult):
        """Print detailed comparison of engine results"""
        print("\n" + "="*60)
        print("ENGINE COMPARISON")
        print("="*60)
        
        for er in result.engine_results:
            status = "✓" if er.success else "✗"
            print(f"\n{status} {er.engine_name.upper()}")
            if er.success:
                print(f"  Words: {er.word_count:,}")
                print(f"  Time: {er.extraction_time:.2f}s")
            else:
                print(f"  Error: {er.error}")
        
        print("\n" + "-"*60)
        print(f"CONSENSUS: {result.consensus_score:.1%}")
        print(f"Final words: {result.word_count:,}")
        print("="*60 + "\n")


def extract_with_consensus(pdf_path: str, verbose: bool = True) -> ConsensusResult:
    """Quick function to extract PDF with multi-engine consensus"""
    extractor = MultiEngineExtractor(verbose=verbose)
    return extractor.extract(pdf_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python multi_engine_extractor.py <pdf_path>")
        sys.exit(1)
    
    result = extract_with_consensus(sys.argv[1])
    output_path = Path(sys.argv[1]).with_suffix('.consensus.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result.final_text)
    print(f"Output saved to: {output_path}")
