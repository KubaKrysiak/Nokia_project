import sys
import os

# Dodanie ścieżki do modułów
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


import file_scanner

def main():

    if len(sys.argv) < 2:
        print("Użycie: python main.py <plik_do_skanowania>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    
    # Wzorce do wyszukania
    patterns = [
        r'hello',
        r'world',
        r'test',
        r'python',
        r'\d{3}-\d{3}-\d{4}',  # numer telefonu
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # email
        r"ERROR", 
        r"WARNING", 
        r"TODO",
    ]
    
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