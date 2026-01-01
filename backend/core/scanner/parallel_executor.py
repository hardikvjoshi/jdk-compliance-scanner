"""
Parallel executor for scanning multiple targets
Works with any scanner type (scanner-agnostic)
"""
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional
from enum import Enum

from core.scanner.base import BaseScanner, ScanResult


class ScanStrategy(Enum):
    """Scan execution strategies"""
    PARALLEL = "Parallel"
    SEQUENTIAL = "Sequential"
    ROUND_ROBIN = "Round-robin"


class ParallelExecutor:
    """
    Executes scans in parallel using thread pool
    Scanner-agnostic - works with any BaseScanner implementation
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize parallel executor
        
        Args:
            max_workers: Maximum number of worker threads (default: 5)
        """
        self.max_workers = max_workers
        self.executor: Optional[ThreadPoolExecutor] = None
    
    def execute_scans(
        self,
        scanner_factory: Callable[[Dict[str, Any]], BaseScanner],
        targets: List[Dict[str, Any]],
        strategy: ScanStrategy = ScanStrategy.PARALLEL
    ) -> Dict[str, ScanResult]:
        """
        Execute scans for multiple targets
        
        Args:
            scanner_factory: Factory function that creates a scanner instance for each target
            targets: List of target configurations
            strategy: Scan execution strategy
            
        Returns:
            Dictionary mapping target identifier to ScanResult
        """
        if strategy == ScanStrategy.SEQUENTIAL:
            return self._execute_sequential(scanner_factory, targets)
        elif strategy == ScanStrategy.ROUND_ROBIN:
            return self._execute_round_robin(scanner_factory, targets)
        else:  # PARALLEL
            return self._execute_parallel(scanner_factory, targets)
    
    def _execute_parallel(
        self,
        scanner_factory: Callable[[Dict[str, Any]], BaseScanner],
        targets: List[Dict[str, Any]]
    ) -> Dict[str, ScanResult]:
        """Execute scans in parallel using thread pool"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_target = {}
            
            for target in targets:
                scanner = scanner_factory(target)
                future = executor.submit(self._scan_target, scanner, target)
                future_to_target[future] = target
            
            for future in as_completed(future_to_target):
                target = future_to_target[future]
                try:
                    result = future.result()
                    target_id = self._get_target_id(target)
                    results[target_id] = result
                except Exception as e:
                    target_id = self._get_target_id(target)
                    results[target_id] = ScanResult(
                        success=False,
                        error_message=str(e)
                    )
        
        return results
    
    def _execute_sequential(
        self,
        scanner_factory: Callable[[Dict[str, Any]], BaseScanner],
        targets: List[Dict[str, Any]]
    ) -> Dict[str, ScanResult]:
        """Execute scans sequentially (one at a time)"""
        results = {}
        
        for target in targets:
            scanner = scanner_factory(target)
            result = self._scan_target(scanner, target)
            target_id = self._get_target_id(target)
            results[target_id] = result
        
        return results
    
    def _execute_round_robin(
        self,
        scanner_factory: Callable[[Dict[str, Any]], BaseScanner],
        targets: List[Dict[str, Any]]
    ) -> Dict[str, ScanResult]:
        """
        Execute scans in round-robin fashion
        Cycles through targets, scanning one per iteration
        """
        # For simplicity, round-robin is similar to sequential
        # In a more advanced implementation, this could interleave targets
        return self._execute_sequential(scanner_factory, targets)
    
    def _scan_target(self, scanner: BaseScanner, target: Dict[str, Any]) -> ScanResult:
        """
        Scan a single target using the provided scanner
        
        Args:
            scanner: Scanner instance
            target: Target configuration
            
        Returns:
            ScanResult
        """
        try:
            result = scanner.scan(target)
            return result
        except Exception as e:
            return ScanResult(
                success=False,
                error_message=str(e)
            )
        finally:
            # Clean up scanner connection
            try:
                scanner.disconnect()
            except Exception:
                pass
    
    def _get_target_id(self, target: Dict[str, Any]) -> str:
        """
        Get unique identifier for a target
        
        Args:
            target: Target configuration
            
        Returns:
            Target identifier string
        """
        # Try common identifier fields
        for key in ['pod_name', 'hostname', 'id', 'name']:
            if key in target:
                return str(target[key])
        
        # Fallback to string representation
        return str(target)

