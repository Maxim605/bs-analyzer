from __future__ import annotations
from dataclasses import dataclass
import logging
import time
from typing import Any, Optional, List
from io import BytesIO
import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

from src.domain.clusterizer.entities.graph import Graph, GraphNode, GraphLink
from src.domain.analysis.services.graph_analysis_service import GraphAnalysisService
from src.domain.clusterizer.services.clustering_strategy import ClusteringStrategy
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager
from src.application.analysis.dto.analysis_dto import (
    AnalysisRequestDTO, 
    AdjacencyMatrixDTO,
    LaplacianMatrixDTO,
    EigenvaluesDTO,
    ChromaticNumberDTO,
    GraphStatsDTO,
    OptimalClusterRequestDTO,
    OptimalClusterResponseDTO,
    EpochStatsDTO,
    LibraryOptimalClusterResponseDTO,
    LibraryMetricDTO
)
from src.application.analysis.dto.laplacian_analysis_dto import (
    LaplacianAnalysisParamsDTO,
    LaplacianAnalysisResponseDTO
)
from src.application.analysis.services.laplacian_analyzer import LaplacianAnalyzer
from src.application.clusterizer.dto.graph_dto import NodeDTO, LinkDTO

logger = logging.getLogger(__name__)

@dataclass
class AnalyzeGraphHandler:
    """
    CQRS Query Handler: Обрабатывает запросы на анализ графа.
    """
    analysis_service: GraphAnalysisService
    redis_manager: RedisTaskManager
    clustering_strategy: Optional[ClusteringStrategy] = None

    def _create_graph(self, dto: AnalysisRequestDTO) -> Graph:
        nodes = [GraphNode(node_id=n.id, name=n.name, index=n.index) for n in dto.graph.nodes]
        links = [GraphLink(source=l.source, target=l.target) for l in dto.graph.links]
        return Graph(nodes=nodes, links=links)

    def _handle_async(self, dto: AnalysisRequestDTO, analysis_type: str) -> str:
        task_data = dto.model_dump()
        task_data['analysis_type'] = analysis_type
        task_id = self.redis_manager.enqueue_clustering_task(task_data) # Используем ту же очередь для простоты
        logger.info(f"Analysis task ({analysis_type}) enqueued: {task_id}")
        return task_id

    def find_optimal_clusters(self, dto: OptimalClusterRequestDTO) -> OptimalClusterResponseDTO | str:
        if dto.async_mode:
            # Для async режима: выполняем задачу синхронно и сохраняем результат
            # В реальном приложении это делал бы воркер
            task_id = self._handle_async(dto, 'optimal_clusters')
            # Выполняем задачу и сохраняем результат
            result = self._find_optimal_clusters_sync(dto)
            # Сохраняем результат в Redis
            self.redis_manager.save_task_result(task_id, result.model_dump())
            return task_id
        
        return self._find_optimal_clusters_sync(dto)

    def _find_optimal_clusters_sync(self, dto: OptimalClusterRequestDTO) -> OptimalClusterResponseDTO:
        """Синхронное выполнение поиска оптимальных кластеров."""
        start_time = time.time()
        
        if not self.clustering_strategy:
            raise ValueError("Clustering strategy is not configured in AnalyzeGraphHandler")

        graph = self._create_graph(dto)
        epoch_stats = []
        
        best_k = dto.min_k
        best_modularity = -1.0
        best_nodes = None
        best_links = None
        best_stats = {}

        # Если граф очень маленький, корректируем max_k
        max_k = min(dto.max_k, len(graph.nodes))
        min_k = min(dto.min_k, max_k)
        
        total_iterations = max_k - min_k + 1
        logger.info(f"Starting optimal clusters search: min_k={min_k}, max_k={max_k}, total_iterations={total_iterations}, nodes={len(graph.nodes)}, edges={len(graph.links)}")

        for iteration, k in enumerate(range(min_k, max_k + 1), start=1):
            iteration_start = time.time()
            
            # Клонируем граф или сбрасываем кластеры, но здесь assign_clusters перезапишет
            labels = self.clustering_strategy.clusterize(graph, n_clusters=k)
            graph.assign_clusters(labels)
            
            modularity = self.analysis_service.get_modularity(graph)
            stats = self.analysis_service.get_basic_stats(graph)
            
            epoch_stats.append(EpochStatsDTO(
                k=k,
                modularity=modularity,
                stats=stats
            ))
            
            # Вычисляем процент выполнения
            progress_percent = (iteration / total_iterations) * 100
            iteration_time = time.time() - iteration_start
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Progress: {progress_percent:.1f}% | "
                f"Iteration {iteration}/{total_iterations} (k={k}) | "
                f"Modularity: {modularity:.4f} | "
                f"Iteration time: {iteration_time:.2f}s | "
                f"Total elapsed: {elapsed_time:.2f}s"
            )
            
            if modularity > best_modularity:
                best_modularity = modularity
                best_k = k
                best_stats = stats
                
                # Создаем snapshot графа для лучшего результата
                best_nodes = [
                    NodeDTO(
                        id=n.node_id,
                        name=n.name,
                        index=n.index,
                        cluster=n.cluster.value if n.cluster else None
                    ) for n in graph.nodes
                ]
                best_links = [LinkDTO(source=l.source, target=l.target) for l in graph.links]
                logger.info(f"New best result found: k={best_k}, modularity={best_modularity:.4f}")

        if best_nodes is None or best_links is None:
             # Fallback если цикл не выполнился или что-то пошло не так
             best_nodes = []
             best_links = []

        total_time = time.time() - start_time
        logger.info(
            f"Optimal clusters search completed | "
            f"Optimal k: {best_k} | "
            f"Best modularity: {best_modularity:.4f} | "
            f"Total processing time: {total_time:.2f}s"
        )

        return OptimalClusterResponseDTO(
            optimal_k=best_k,
            best_stats=best_stats,
            nodes=best_nodes,
            links=best_links,
            epoch_stats=epoch_stats
        )

    def find_optimal_clusters_library(self, dto: OptimalClusterRequestDTO) -> LibraryOptimalClusterResponseDTO | str:
        """
        Находит оптимальное количество кластеров используя библиотечные метрики:
        - Silhouette Score (чем выше, тем лучше)
        - Calinski-Harabasz Index (чем выше, тем лучше)
        - Davies-Bouldin Index (чем ниже, тем лучше)
        """
        if dto.async_mode:
            return self._handle_async(dto, 'optimal_clusters_library')
        
        if not self.clustering_strategy:
            raise ValueError("Clustering strategy is not configured in AnalyzeGraphHandler")

        start_time = time.time()
        graph = self._create_graph(dto)
        
        # Получаем матрицу смежности для вычисления метрик
        node_ids, edges = graph.to_adjacency_matrix_data()
        import networkx as nx
        from scipy import sparse
        
        nx_graph = nx.Graph()
        nx_graph.add_nodes_from(node_ids)
        nx_graph.add_edges_from(edges)
        adj_matrix = nx.to_scipy_sparse_array(nx_graph, nodelist=node_ids, format='csr')
        
        # Преобразуем в плотную матрицу для метрик (если граф не слишком большой)
        # Для больших графов используем разреженную матрицу
        if len(node_ids) > 10000:
            # Для больших графов используем только silhouette с разреженной матрицей
            use_sparse = True
        else:
            use_sparse = False
            adj_matrix_dense = adj_matrix.toarray()
        
        metrics_list = []
        best_silhouette = -1.0
        best_calinski = -1.0
        best_davies = float('inf')
        best_k_silhouette = dto.min_k
        best_k_calinski = dto.min_k
        best_k_davies = dto.min_k
        best_labels = None
        best_k = dto.min_k

        max_k = min(dto.max_k, len(graph.nodes))
        min_k = min(dto.min_k, max_k)
        
        total_iterations = max_k - min_k + 1
        logger.info(f"Starting library-based optimal clusters search: min_k={min_k}, max_k={max_k}, total_iterations={total_iterations}, nodes={len(graph.nodes)}")

        for iteration, k in enumerate(range(min_k, max_k + 1), start=1):
            iteration_start = time.time()
            
            # Выполняем кластеризацию
            labels = self.clustering_strategy.clusterize(graph, n_clusters=k)
            graph.assign_clusters(labels)
            
            # Преобразуем labels в массив для метрик
            labels_array = np.array([labels[node_id] for node_id in node_ids])
            
            # Вычисляем метрики
            try:
                if use_sparse:
                    # Для больших графов используем только silhouette
                    silhouette = silhouette_score(adj_matrix, labels_array, metric='precomputed')
                    calinski = 0.0  # Не вычисляем для больших графов
                    davies = float('inf')  # Не вычисляем для больших графов
                else:
                    silhouette = silhouette_score(adj_matrix_dense, labels_array, metric='precomputed')
                    calinski = calinski_harabasz_score(adj_matrix_dense, labels_array)
                    davies = davies_bouldin_score(adj_matrix_dense, labels_array)
                
                metrics_list.append(LibraryMetricDTO(
                    k=k,
                    silhouette_score=silhouette,
                    calinski_harabasz_score=calinski,
                    davies_bouldin_score=davies
                ))
                
                # Обновляем лучшие результаты
                if silhouette > best_silhouette:
                    best_silhouette = silhouette
                    best_k_silhouette = k
                    # По умолчанию используем silhouette как основной метод
                    best_k = k
                    best_labels = labels.copy()
                
                if calinski > best_calinski:
                    best_calinski = calinski
                    best_k_calinski = k
                
                if davies < best_davies:
                    best_davies = davies
                    best_k_davies = k
                
            except Exception as e:
                logger.warning(f"Error computing metrics for k={k}: {e}")
                # Добавляем нулевые метрики при ошибке
                metrics_list.append(LibraryMetricDTO(
                    k=k,
                    silhouette_score=0.0,
                    calinski_harabasz_score=0.0,
                    davies_bouldin_score=float('inf')
                ))
            
            # Логирование прогресса
            progress_percent = (iteration / total_iterations) * 100
            iteration_time = time.time() - iteration_start
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Progress: {progress_percent:.1f}% | "
                f"Iteration {iteration}/{total_iterations} (k={k}) | "
                f"Silhouette: {metrics_list[-1].silhouette_score:.4f} | "
                f"Iteration time: {iteration_time:.2f}s | "
                f"Total elapsed: {elapsed_time:.2f}s"
            )
        
        # Определяем оптимальный k на основе silhouette (основной метод)
        optimal_k = best_k_silhouette
        optimal_score = best_silhouette
        method = "silhouette"
        
        # Создаем кластеризованный граф для лучшего результата
        if best_labels:
            graph.assign_clusters(best_labels)
            response_nodes = [
                NodeDTO(
                    id=n.node_id,
                    name=n.name,
                    index=n.index,
                    cluster=n.cluster.value if n.cluster else None
                ) for n in graph.nodes
            ]
            response_links = [LinkDTO(source=l.source, target=l.target) for l in graph.links]
            clustered_graph = {
                'nodes': [n.model_dump() for n in response_nodes],
                'links': [l.model_dump() for l in response_links]
            }
        else:
            clustered_graph = {'nodes': [], 'links': []}
        
        total_time = time.time() - start_time
        logger.info(
            f"Library-based optimal clusters search completed | "
            f"Optimal k (silhouette): {best_k_silhouette} (score: {best_silhouette:.4f}) | "
            f"Optimal k (calinski): {best_k_calinski} (score: {best_calinski:.4f}) | "
            f"Optimal k (davies): {best_k_davies} (score: {best_davies:.4f}) | "
            f"Total processing time: {total_time:.2f}s"
        )
        
        return LibraryOptimalClusterResponseDTO(
            optimal_k=optimal_k,
            method=method,
            optimal_score=optimal_score,
            clustered_graph=clustered_graph,
            metrics=metrics_list
        )

    def get_optimal_clusters_result(self, task_id: str) -> OptimalClusterResponseDTO | None:
        """
        Получает результат задачи поиска оптимальных кластеров по task_id.
        """
        result = self.redis_manager.get_task_result(task_id)
        if result is None:
            return None
        
        # Преобразуем словарь обратно в DTO
        try:
            return OptimalClusterResponseDTO(**result)
        except Exception as e:
            logger.error(f"Error parsing task result for {task_id}: {e}")
            return None

    def get_adjacency_matrix(self, dto: AnalysisRequestDTO) -> AdjacencyMatrixDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'adjacency_matrix')
        
        graph = self._create_graph(dto)
        matrix = self.analysis_service.get_adjacency_matrix(graph)
        return AdjacencyMatrixDTO(matrix=matrix)

    def get_laplacian_matrix(self, dto: AnalysisRequestDTO) -> str | bytes:
        """
        Получает матрицу Лапласа и возвращает Excel файл.
        Если async_mode=True, возвращает task_id (str).
        Иначе возвращает Excel файл в виде bytes.
        """
        if dto.async_mode:
            return self._handle_async(dto, 'laplacian_matrix')

        graph = self._create_graph(dto)
        matrix = self.analysis_service.get_laplacian_matrix(graph)
        
        # Получаем id вершин в том же порядке, что и матрица
        node_ids, _ = graph.to_adjacency_matrix_data()
        
        # Создаем Excel файл в памяти
        wb = Workbook()
        ws = wb.active
        ws.title = "Laplacian Matrix"
        
        # Стили для заголовков
        header_font = Font(bold=True)
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        # Заполняем первую ячейку (пустая для угла)
        ws.cell(row=1, column=1, value="")
        
        # Заполняем заголовки строк (id вершин в первом столбце)
        for i, node_id in enumerate(node_ids, start=2):
            cell = ws.cell(row=i, column=1, value=node_id)
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Заполняем заголовки столбцов (id вершин в первой строке)
        for j, node_id in enumerate(node_ids, start=2):
            cell = ws.cell(row=1, column=j, value=node_id)
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Заполняем матрицу
        for i, row in enumerate(matrix, start=2):
            for j, value in enumerate(row, start=2):
                ws.cell(row=i, column=j, value=value)
        
        # Автоматически подгоняем ширину столбцов
        ws.column_dimensions['A'].width = max(len(str(node_id)) for node_id in node_ids) + 2
        for j, node_id in enumerate(node_ids, start=2):
            col_letter = ws.cell(row=1, column=j).column_letter
            ws.column_dimensions[col_letter].width = max(len(str(node_id)), 10)
        
        # Сохраняем в BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer.getvalue()

    def _parse_laplacian_matrix_from_excel(self, excel_bytes: bytes) -> tuple[List[List[float]], List[str]]:
        """
        Парсит Excel файл с матрицей Лапласа.
        Возвращает матрицу и список id вершин.
        Формат Excel: первая строка и первый столбец содержат id вершин, матрица начинается с B2.
        """
        wb = load_workbook(filename=BytesIO(excel_bytes), data_only=True)
        ws = wb.active
        
        # Читаем id вершин из первой строки (начиная с B1, пропуская A1)
        node_ids = []
        col = 2
        while True:
            cell_value = ws.cell(row=1, column=col).value
            if cell_value is None or cell_value == "":
                break
            node_ids.append(str(cell_value))
            col += 1
        
        if not node_ids:
            raise ValueError("Не удалось прочитать id вершин из Excel файла")
        
        # Проверяем, что количество строк соответствует количеству столбцов
        # (первая строка - заголовки, остальные - данные)
        expected_rows = len(node_ids) + 1  # +1 для заголовка
        actual_rows = ws.max_row
        
        if actual_rows < expected_rows:
            raise ValueError(f"Недостаточно строк в Excel файле. Ожидается {expected_rows}, найдено {actual_rows}")
        
        # Читаем матрицу (начиная с B2)
        matrix = []
        for row_idx in range(2, len(node_ids) + 2):
            row = []
            for col_idx in range(2, len(node_ids) + 2):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if cell_value is None:
                    cell_value = 0
                try:
                    row.append(float(cell_value))
                except (ValueError, TypeError):
                    raise ValueError(f"Некорректное значение в ячейке ({row_idx}, {col_idx}): {cell_value}")
            matrix.append(row)
        
        # Проверяем, что матрица квадратная
        if len(matrix) != len(node_ids):
            raise ValueError(f"Матрица не является квадратной. Размер: {len(matrix)}x{len(matrix[0]) if matrix else 0}, ожидается {len(node_ids)}x{len(node_ids)}")
        
        for i, row in enumerate(matrix):
            if len(row) != len(node_ids):
                raise ValueError(f"Строка {i+2} имеет неправильную длину: {len(row)}, ожидается {len(node_ids)}")
        
        return matrix, node_ids
    
    def _validate_laplacian_matrix(self, matrix: List[List[float]]) -> None:
        """
        Проверяет, что матрица является корректной матрицей Лапласа:
        - Симметричная
        - Сумма всех элементов равна 0
        """
        import numpy as np
        np_matrix = np.array(matrix)
        
        # Проверка симметричности
        if not np.allclose(np_matrix, np_matrix.T, rtol=1e-5):
            raise ValueError("Матрица не является симметричной")
        
        # Проверка суммы элементов
        total_sum = np.sum(np_matrix)
        if not np.isclose(total_sum, 0.0, rtol=1e-5):
            raise ValueError(f"Сумма всех элементов матрицы должна быть равна 0, получено: {total_sum}")

    def get_eigenvalues(self, dto: AnalysisRequestDTO) -> EigenvaluesDTO | str | bytes:
        """
        Получает собственные числа из матрицы Лапласа в Excel файле.
        Если async_mode=True, возвращает task_id (str).
        Иначе возвращает Excel файл в виде bytes.
        """
        if dto.async_mode:
            return self._handle_async(dto, 'eigenvalues')

        # Если передан граф (старый способ), используем его
        if hasattr(dto, 'graph') and dto.graph:
            graph = self._create_graph(dto)
            values = self.analysis_service.get_eigenvalues(graph)
            return EigenvaluesDTO(values=values)
        
        # Новый способ: парсим Excel файл
        # Это будет обработано в контроллере, здесь возвращаем ошибку
        raise ValueError("Для вычисления собственных чисел требуется Excel файл с матрицей Лапласа")
    
    def get_eigenvalues_from_excel(self, excel_bytes: bytes, sort: str = "-") -> bytes:
        """
        Вычисляет собственные числа из Excel файла с матрицей Лапласа.
        
        Параметры:
        - sort: режим сортировки ("-" для убывания, "+" для возрастания). По умолчанию "-".
        """
        # Парсим Excel файл
        matrix, node_ids = self._parse_laplacian_matrix_from_excel(excel_bytes)
        
        # Проверяем матрицу
        self._validate_laplacian_matrix(matrix)
        
        # Вычисляем собственные числа
        import numpy as np
        np_matrix = np.array(matrix, dtype=float)
        
        # Вычисляем все собственные числа
        eigenvalues = np.linalg.eigvalsh(np_matrix)
        eigenvalues = eigenvalues.tolist()
        
        # Сортируем в зависимости от параметра sort
        if sort == "-":
            # По убыванию
            eigenvalues = sorted(eigenvalues, reverse=True)
        elif sort == "+":
            # По возрастанию
            eigenvalues = sorted(eigenvalues, reverse=False)
        else:
            # По умолчанию по убыванию
            eigenvalues = sorted(eigenvalues, reverse=True)
        
        # Создаем Excel файл с результатами
        wb = Workbook()
        ws = wb.active
        ws.title = "Eigenvalues"
        
        # Стили для заголовков
        header_font = Font(bold=True)
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        # Заголовки
        ws.cell(row=1, column=1, value="Index").font = header_font
        ws.cell(row=1, column=1).alignment = header_alignment
        ws.cell(row=1, column=2, value="Eigenvalue").font = header_font
        ws.cell(row=1, column=2).alignment = header_alignment
        
        # Заполняем собственные числа
        for i, value in enumerate(eigenvalues, start=2):
            ws.cell(row=i, column=1, value=i - 1)  # Index (начиная с 1)
            ws.cell(row=i, column=2, value=value)
        
        # Автоматически подгоняем ширину столбцов
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 15
        
        # Сохраняем в BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer.getvalue()

    def get_chromatic_number(self, dto: AnalysisRequestDTO) -> ChromaticNumberDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'chromatic_number')

        graph = self._create_graph(dto)
        number = self.analysis_service.get_chromatic_number(graph)
        return ChromaticNumberDTO(chromatic_number=number)

    def get_basic_stats(self, dto: AnalysisRequestDTO) -> GraphStatsDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'basic_stats')

        graph = self._create_graph(dto)
        stats = self.analysis_service.get_basic_stats(graph)
        return GraphStatsDTO(stats=stats)

    def analyze_laplacian_from_excel(
        self,
        excel_bytes: bytes,
        params: LaplacianAnalysisParamsDTO
    ) -> LaplacianAnalysisResponseDTO:
        """
        Выполняет полный анализ матрицы Лапласа из Excel файла.
        
        Параметры:
        - excel_bytes: содержимое Excel файла с матрицей Лапласа
        - params: параметры анализа (пороги, коэффициенты)
        
        Возвращает полный отчёт анализа.
        """
        # Парсим Excel файл
        matrix, node_ids = self._parse_laplacian_matrix_from_excel(excel_bytes)
        
        # Конвертируем в numpy array
        np_matrix = np.array(matrix, dtype=float)
        
        # Создаём анализатор и выполняем анализ
        analyzer = LaplacianAnalyzer(params)
        result = analyzer.analyze(np_matrix)
        
        return result

