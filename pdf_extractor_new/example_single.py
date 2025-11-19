# Example: Process a single PDF file

from processor import FileSystemProcessor

# Create processor
processor = FileSystemProcessor()

# Process single file
pdf_path = "input/sample.pdf"
output_path = processor.process_file(pdf_path)

print(f"✓ Extracted to: {output_path}")

# You can also specify custom output path
custom_output = processor.process_file(
    pdf_path="input/document.pdf",
    output_path="custom_location/result.txt"
)
print(f"✓ Saved to: {custom_output}")
