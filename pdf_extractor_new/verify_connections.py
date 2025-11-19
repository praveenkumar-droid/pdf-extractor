"""
CONNECTION VERIFICATION SCRIPT
==============================

Tests all imports and connections in the optimized PDF extractor system.
Run this to verify everything is properly connected before using.
"""
import sys
import traceback

def test_imports():
    """Test all required imports"""
    print("\n" + "="*60)
    print("TESTING IMPORTS")
    print("="*60)
    
    results = []
    
    # Core modules
    core_modules = [
        ("pdfplumber", "PDF processing"),
        ("tqdm", "Progress bars"),
        ("fastapi", "API server"),
    ]
    
    for module, desc in core_modules:
        try:
            __import__(module)
            results.append((module, True, desc))
            print(f"  ✓ {module}: {desc}")
        except ImportError as e:
            results.append((module, False, str(e)))
            print(f"  ✗ {module}: {e}")
    
    # LLM APIs (optional but recommended)
    llm_modules = [
        ("anthropic", "Claude API"),
        ("openai", "OpenAI API"),
    ]
    
    print("\n  LLM APIs (optional):")
    for module, desc in llm_modules:
        try:
            __import__(module)
            results.append((module, True, desc))
            print(f"    ✓ {module}: {desc}")
        except ImportError:
            results.append((module, "optional", desc))
            print(f"    ○ {module}: Not installed (optional)")
    
    # Multi-engine (optional)
    engine_modules = [
        ("fitz", "PyMuPDF engine"),
        ("pdfminer", "PDFMiner engine"),
    ]
    
    print("\n  Multi-engine (optional):")
    for module, desc in engine_modules:
        try:
            __import__(module)
            results.append((module, True, desc))
            print(f"    ✓ {module}: {desc}")
        except ImportError:
            results.append((module, "optional", desc))
            print(f"    ○ {module}: Not installed (optional)")
    
    return results


def test_project_modules():
    """Test all project module imports"""
    print("\n" + "="*60)
    print("TESTING PROJECT MODULES")
    print("="*60)
    
    results = []
    
    # Original modules
    original_modules = [
        "config",
        "extractor",
        "processor",
        "element_inventory",
        "superscript_detector",
        "layout_analyzer",
        "footnote_extractor",
        "quality_scorer",
        "output_formatter",
        "error_handler",
        "context_windows",
        "flagging_system",
        "llm_verifier",
        "multi_engine_extractor",
        "batch_processor",
        "master_extractor",
    ]
    
    print("\n  Original modules:")
    for module in original_modules:
        try:
            __import__(module)
            results.append((module, True, ""))
            print(f"    ✓ {module}")
        except Exception as e:
            results.append((module, False, str(e)))
            print(f"    ✗ {module}: {e}")
    
    # Enhanced modules
    enhanced_modules = [
        "config_optimized",
        "llm_verifier_enhanced",
        "table_detector_enhanced",
        "optimized_extractor",
    ]
    
    print("\n  Enhanced modules:")
    for module in enhanced_modules:
        try:
            __import__(module)
            results.append((module, True, ""))
            print(f"    ✓ {module}")
        except Exception as e:
            results.append((module, False, str(e)))
            print(f"    ✗ {module}: {e}")
    
    return results


def test_class_instantiation():
    """Test that main classes can be instantiated"""
    print("\n" + "="*60)
    print("TESTING CLASS INSTANTIATION")
    print("="*60)
    
    results = []
    
    tests = [
        ("JapanesePDFExtractor", "extractor", "JapanesePDFExtractor"),
        ("ElementInventoryAnalyzer", "element_inventory", "ElementInventoryAnalyzer"),
        ("SuperscriptSubscriptDetector", "superscript_detector", "SuperscriptSubscriptDetector"),
        ("FootnoteExtractor", "footnote_extractor", "FootnoteExtractor"),
        ("QualityScorer", "quality_scorer", "QualityScorer"),
        ("OutputFormatter", "output_formatter", "OutputFormatter"),
        ("ErrorHandler", "error_handler", "ErrorHandler"),
        ("FlaggingSystem", "flagging_system", "FlaggingSystem"),
        ("EnhancedLLMVerifier", "llm_verifier_enhanced", "EnhancedLLMVerifier"),
        ("EnhancedTableDetector", "table_detector_enhanced", "EnhancedTableDetector"),
        ("OptimizedPDFExtractor", "optimized_extractor", "OptimizedPDFExtractor"),
    ]
    
    for name, module_name, class_name in tests:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            
            # Special handling for classes that need config
            if class_name in ["EnhancedLLMVerifier", "EnhancedTableDetector"]:
                import config_optimized
                instance = cls(config_optimized)
            elif class_name == "OptimizedPDFExtractor":
                instance = cls(verbose=False)
            elif class_name == "ErrorHandler":
                instance = cls(verbose=False)
            else:
                instance = cls()
            
            results.append((name, True, ""))
            print(f"  ✓ {name}")
            
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ✗ {name}: {e}")
    
    return results


def test_config():
    """Test configuration"""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION")
    print("="*60)
    
    try:
        import config_optimized as config
        
        # Required settings
        required = [
            "LLM_ENABLED",
            "LLM_BACKEND",
            "LLM_API_KEY",
            "LLM_MODEL",
            "MIN_ACCEPTABLE_QUALITY",
            "TABLE_DETECTION_ENABLED",
            "FLAGGING_ENABLED",
        ]
        
        print("\n  Required settings:")
        for setting in required:
            value = getattr(config, setting, None)
            if value is not None:
                # Mask API key
                if "API_KEY" in setting:
                    display = "SET" if value != "your-api-key-here" else "NOT SET"
                else:
                    display = value
                print(f"    ✓ {setting}: {display}")
            else:
                print(f"    ✗ {setting}: MISSING")
        
        # Validate
        errors, warnings = config.validate_config()
        
        if errors:
            print(f"\n  ❌ Errors ({len(errors)}):")
            for err in errors:
                print(f"    • {err}")
        
        if warnings:
            print(f"\n  ⚠ Warnings ({len(warnings)}):")
            for warn in warnings:
                print(f"    • {warn}")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"\n  ✗ Configuration error: {e}")
        return False


def test_connections():
    """Test that all components connect properly"""
    print("\n" + "="*60)
    print("TESTING CONNECTIONS")
    print("="*60)
    
    try:
        from optimized_extractor import OptimizedPDFExtractor
        
        # Create extractor (this tests all component initialization)
        print("\n  Initializing OptimizedPDFExtractor...")
        extractor = OptimizedPDFExtractor(verbose=False)
        
        # Check all components are initialized
        components = [
            ("text_extractor", "JapanesePDFExtractor"),
            ("inventory_analyzer", "ElementInventoryAnalyzer"),
            ("script_detector", "SuperscriptSubscriptDetector"),
            ("footnote_extractor", "FootnoteExtractor"),
            ("quality_scorer", "QualityScorer"),
            ("output_formatter", "OutputFormatter"),
            ("error_handler", "ErrorHandler"),
            ("llm_verifier", "EnhancedLLMVerifier"),
            ("table_detector", "EnhancedTableDetector"),
            ("flagger", "FlaggingSystem"),
            ("large_doc_processor", "LargeDocumentProcessor"),
        ]
        
        all_ok = True
        for attr, expected_type in components:
            if hasattr(extractor, attr):
                obj = getattr(extractor, attr)
                print(f"    ✓ {attr}: {type(obj).__name__}")
            else:
                print(f"    ✗ {attr}: MISSING")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"\n  ✗ Connection test failed: {e}")
        traceback.print_exc()
        return False


def test_data_flow():
    """Test that data types match between components"""
    print("\n" + "="*60)
    print("TESTING DATA FLOW")
    print("="*60)
    
    try:
        # Test that return types are correct
        from quality_scorer import QualityScorer
        from flagging_system import FlaggingSystem
        from llm_verifier_enhanced import EnhancedLLMVerifier
        
        print("\n  Checking data type compatibility...")
        
        # QualityScorer returns report with to_dict()
        scorer = QualityScorer()
        report = scorer.score_extraction("test", page_count=1)
        assert hasattr(report, 'to_dict'), "QualityReport missing to_dict()"
        print("    ✓ QualityScorer.score_extraction returns proper report")
        
        # FlaggingSystem returns flags with to_dict()
        flagger = FlaggingSystem()
        flag = flagger.add_flag(
            flagger.flags[0].flag_type if flagger.flags else None,
            None, 1, "test"
        ) if False else None
        # Just check the class has the method
        from flagging_system import Flag
        assert hasattr(Flag, '__dataclass_fields__'), "Flag not a dataclass"
        print("    ✓ FlaggingSystem.Flag is proper dataclass")
        
        # EnhancedLLMVerifier returns tuple
        import config_optimized
        verifier = EnhancedLLMVerifier(config_optimized)
        # Don't actually call verify_text, just check method exists
        assert hasattr(verifier, 'verify_text'), "EnhancedLLMVerifier missing verify_text"
        print("    ✓ EnhancedLLMVerifier.verify_text exists")
        
        print("\n  All data flow checks passed!")
        return True
        
    except Exception as e:
        print(f"\n  ✗ Data flow test failed: {e}")
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("PDF EXTRACTOR CONNECTION VERIFICATION")
    print("="*60)
    
    all_passed = True
    
    # Test imports
    test_imports()
    
    # Test project modules
    module_results = test_project_modules()
    failed_modules = [r for r in module_results if r[1] == False]
    if failed_modules:
        all_passed = False
    
    # Test class instantiation
    class_results = test_class_instantiation()
    failed_classes = [r for r in class_results if r[1] == False]
    if failed_classes:
        all_passed = False
    
    # Test configuration
    config_ok = test_config()
    if not config_ok:
        all_passed = False
    
    # Test connections
    connections_ok = test_connections()
    if not connections_ok:
        all_passed = False
    
    # Test data flow
    data_flow_ok = test_data_flow()
    if not data_flow_ok:
        all_passed = False
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED")
        print("\nThe system is properly connected and ready to use.")
        print("\nNext steps:")
        print("  1. Set your API key in config_optimized.py")
        print("  2. Run: python run_optimized.py <your_pdf>")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nPlease fix the issues above before using the system.")
        
        if failed_modules:
            print(f"\nFailed modules: {[m[0] for m in failed_modules]}")
        if failed_classes:
            print(f"Failed classes: {[c[0] for c in failed_classes]}")
    
    print("\n" + "="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
