import sys
import os
from file_regex.file_regex import FileRegex
# Dodanie ścieżki do modułów
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


import file_scanner

def main():

    if len(sys.argv) < 2:
        print("Użycie: python main.py <plik_do_skanowania>")
        sys.exit(1)
    
    filename = sys.argv[1]
    fr = FileRegex()
    
    # Wzorce do wyszukania
    patterns = fr.elements()
    
    # Inicjalizacja skanera - użyj pełnej ścieżki
    scanner = file_scanner.FileScanner()
    scanner.compile_patterns(patterns)
    
    print(f"Skanowanie pliku: {filename}")
    print(f"Wzorce: {patterns}")
    print("-" * 50)
    
    # Skanowanie pliku w trybie strumieniowym (Hyperscan STREAM mode)
    results = scanner.scan_file(filename, chunk_size=4096)
    cataloge = scanner.scan_tree("/home/igris/Desktop/test")
    print("-" * 50)
    print(f"Znaleziono {len(results)} dopasowań")
    print(f"Znaleziono {len(cataloge)} dopasowań w drzewie katalogów:")
    for match in cataloge:
        print(match)
    
    return results

if __name__ == "__main__":
    main()