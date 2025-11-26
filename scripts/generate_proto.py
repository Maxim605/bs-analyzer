"""
Скрипт для генерации Python-кода из proto-файлов.
"""

import subprocess
import sys
from pathlib import Path

def generate_proto():
    """Генерирует Python-код из proto-файлов."""
    project_root = Path(__file__).parent.parent
    proto_dir = project_root / "proto"
    output_dir = project_root / "proto"
    
    proto_file = proto_dir / "arango.proto"
    
    if not proto_file.exists():
        print(f"Ошибка: файл {proto_file} не найден")
        sys.exit(1)
    
    # Команда для генерации
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        str(proto_file)
    ]
    
    print(f"Генерация кода из {proto_file}...")
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Генерация успешно завершена!")
        print(f"Сгенерированные файлы в {output_dir}:")
        print(f"  - arango_pb2.py")
        print(f"  - arango_pb2_grpc.py")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при генерации: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    generate_proto()




