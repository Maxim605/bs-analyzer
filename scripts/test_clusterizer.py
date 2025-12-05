import json
import urllib.request
import urllib.error
import os
import sys

def test_json_clusterization():
    """
    Тест эндпоинта /spectral-clusterize (JSON в теле запроса).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    graph_file_path = os.path.join(project_root, 'graph.json')
    
    print("=" * 60)
    print("Test 1: JSON body endpoint (/spectral-clusterize)")
    print("=" * 60)
    
    if not os.path.exists(graph_file_path):
        print(f"Error: File {graph_file_path} not found.")
        return

    try:
        with open(graph_file_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
            print(f"Loaded graph with {len(graph_data.get('nodes', []))} nodes and {len(graph_data.get('links', []))} links.")
    except json.JSONDecodeError as e:
        print(f"Error decoding graph.json: {e}")
        return

    payload = {
        "graph": graph_data,
        "n_clusters": 5,
        "async_mode": False
    }

    json_payload = json.dumps(payload).encode('utf-8')
    url = "http://127.0.0.1:8000/clusterizer/spectral-clusterize"

    req = urllib.request.Request(
        url, 
        data=json_payload, 
        headers={'Content-Type': 'application/json'}
    )

    print(f"Sending POST request to {url}...")

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            response_body = response.read().decode('utf-8')
            
            print(f"Response Status: {status_code}")
            
            if status_code == 200:
                result = json.loads(response_body)
                if isinstance(result, dict):
                    clusters_count = result.get('clusters_found')
                    print(f"Success! Clusters found: {clusters_count}")
                    
                    nodes = result.get('nodes', [])
                    print("\nSample clustered nodes:")
                    for node in nodes[:5]:
                        print(f" - {node.get('name')} (ID: {node.get('id')}): Cluster {node.get('cluster')}")
                else:
                    print(f"Result: {result}")
            else:
                print("Unexpected status code.")
                print(response_body)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}:")
        print(e.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}")
        print("Make sure the FastAPI server is running (uvicorn src.main:app --reload)")
    except Exception as e:
        print(f"An error occurred: {e}")

def test_file_clusterization():
    """
    Тест эндпоинта /spectral-clusterize-file (файл + headers).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    graph_file_path = os.path.join(project_root, 'graph.json')
    
    print("\n" + "=" * 60)
    print("Test 2: File upload endpoint (/spectral-clusterize-file)")
    print("=" * 60)
    
    if not os.path.exists(graph_file_path):
        print(f"Error: File {graph_file_path} not found.")
        return

    url = "http://127.0.0.1:8000/clusterizer/spectral-clusterize-file"
    
    # Подготовка multipart/form-data запроса
    import mimetypes
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    with open(graph_file_path, 'rb') as f:
        file_content = f.read()
    
    # Формируем multipart body
    body_parts = []
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(f'Content-Disposition: form-data; name="file"; filename="graph.json"'.encode())
    body_parts.append(f'Content-Type: application/json'.encode())
    body_parts.append(b'')
    body_parts.append(file_content)
    body_parts.append(f'--{boundary}--'.encode())
    
    body = b'\r\n'.join(body_parts)
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'X-Cluster-Count': '5',
            'X-Async-Mode': 'false',
            'X-User-Id': 'test-user-123',
            'X-Request-Id': 'req-456'
        }
    )

    print(f"Sending POST request to {url} with file upload...")
    print("Headers: X-Cluster-Count=5, X-Async-Mode=false, X-User-Id=test-user-123, X-Request-Id=req-456")

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.status
            response_body = response.read().decode('utf-8')
            
            print(f"Response Status: {status_code}")
            
            if status_code == 200:
                result = json.loads(response_body)
                if isinstance(result, dict):
                    clusters_count = result.get('clusters_found')
                    print(f"Success! Clusters found: {clusters_count}")
                    
                    nodes = result.get('nodes', [])
                    print("\nSample clustered nodes:")
                    for node in nodes[:5]:
                        print(f" - {node.get('name')} (ID: {node.get('id')}): Cluster {node.get('cluster')}")
                else:
                    print(f"Result: {result}")
            else:
                print("Unexpected status code.")
                print(response_body)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}:")
        print(e.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Connection Error: {e.reason}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_json_clusterization()
    test_file_clusterization()

