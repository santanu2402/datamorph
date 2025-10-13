"""
Shared logging utility for DataMorph.
Formats log entries consistently and provides helper functions.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class LogType(Enum):
    """Log entry types."""
    STATUS = "status"
    CODE = "code"
    INFO = "info"
    START = "start"
    END = "end"
    RESULT = "result"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PROGRESS = "progress"
    
    # Completion types for specific components
    SPECS_GENERATED = "specs_generated"
    GLUE_CODE_GENERATED = "glue_code_generated"
    GLUE_EXECUTION_COMPLETED = "glue_execution_completed"
    TEST_CASES_GENERATED = "test_cases_generated"
    QUERY_GENERATED = "query_generated"
    QUERY_EXECUTED = "query_executed"
    TEST_CASES_EXECUTED = "test_cases_executed"
    VALIDATION_PHASE_COMPLETED = "validation_phase_completed"
    REMEDIATION_COMPLETED = "remediation_completed"


def create_log_entry(
    log_type: LogType,
    title: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a formatted log entry.
    
    Args:
        log_type: Type of log entry
        title: Log title
        description: Log description
        metadata: Optional additional metadata
        
    Returns:
        Formatted log entry dictionary
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": log_type.value if isinstance(log_type, LogType) else log_type,
        "title": title,
        "description": description
    }
    
    if metadata:
        entry["metadata"] = metadata
    
    return entry


def format_error_log(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Format an error as a log entry.
    
    Args:
        error: Exception object
        context: Additional context about where error occurred
        
    Returns:
        Formatted error log entry
    """
    return create_log_entry(
        LogType.ERROR,
        f"Error: {type(error).__name__}",
        f"{context}: {str(error)}" if context else str(error),
        metadata={
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
    )


def format_status_log(status: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a status update as a log entry.
    
    Args:
        status: Status value
        message: Status message
        metadata: Optional additional metadata
        
    Returns:
        Formatted status log entry
    """
    return create_log_entry(
        LogType.STATUS,
        f"Status: {status}",
        message,
        metadata=metadata
    )


def format_start_log(component: str, details: str = "") -> Dict[str, Any]:
    """
    Format a component start log entry.
    
    Args:
        component: Component name
        details: Additional details
        
    Returns:
        Formatted start log entry
    """
    return create_log_entry(
        LogType.START,
        f"Starting {component}",
        details or f"{component} execution started"
    )


def format_end_log(component: str, details: str = "", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a component end log entry.
    
    Args:
        component: Component name
        details: Additional details
        metadata: Optional additional metadata
        
    Returns:
        Formatted end log entry
    """
    return create_log_entry(
        LogType.END,
        f"Completed {component}",
        details or f"{component} execution completed",
        metadata=metadata
    )


def format_specs_generated_log(specs: Dict[str, Any], s3_path: str) -> Dict[str, Any]:
    """
    Format a specs generation completion log.
    
    Args:
        specs: Generated specifications
        s3_path: S3 path where specs are stored
        
    Returns:
        Formatted log entry
    """
    return create_log_entry(
        LogType.SPECS_GENERATED,
        "Specifications Generated Successfully",
        f"ETL specifications have been generated and stored at {s3_path}",
        metadata={
            "generated_item": specs,
            "path": s3_path,
            "source_tables": specs.get("source_tables", []),
            "target_table": specs.get("target_table", ""),
            "transformation_count": len(specs.get("transformations", []))
        }
    )


def format_glue_code_generated_log(glue_code: str, s3_path: str, specs_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a Glue code generation completion log.
    
    Args:
        glue_code: Generated Glue code
        s3_path: S3 path where code is stored
        specs_summary: Optional summary of specs used
        
    Returns:
        Formatted log entry
    """
    metadata = {
        "generated_item": glue_code,
        "path": s3_path,
        "code_length": len(glue_code),
        "lines_of_code": len(glue_code.split('\n'))
    }
    
    if specs_summary:
        metadata.update(specs_summary)
    
    return create_log_entry(
        LogType.GLUE_CODE_GENERATED,
        "Glue Code Generated Successfully",
        f"PySpark transformation code has been generated and stored at {s3_path}",
        metadata=metadata
    )


def format_glue_execution_completed_log(job_name: str, job_run_id: str, status: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
    """
    Format a Glue job execution completion log.
    
    Args:
        job_name: Glue job name
        job_run_id: Glue job run ID
        status: Execution status
        duration_seconds: Optional execution duration
        
    Returns:
        Formatted log entry
    """
    metadata = {
        "job_name": job_name,
        "job_run_id": job_run_id,
        "status": status
    }
    
    if duration_seconds:
        metadata["duration_seconds"] = duration_seconds
        metadata["duration_formatted"] = f"{duration_seconds // 60}m {duration_seconds % 60}s"
    
    return create_log_entry(
        LogType.GLUE_EXECUTION_COMPLETED,
        "Glue Job Execution Completed",
        f"Glue job '{job_name}' completed with status: {status}",
        metadata=metadata
    )


def format_test_cases_generated_log(test_cases: Dict[str, Any], phase: str, s3_path: str) -> Dict[str, Any]:
    """
    Format a test cases generation completion log.
    
    Args:
        test_cases: Generated test cases
        phase: Validation phase (phase1, phase2, etc.)
        s3_path: S3 path where test cases are stored
        
    Returns:
        Formatted log entry
    """
    return create_log_entry(
        LogType.TEST_CASES_GENERATED,
        f"Test Cases Generated Successfully ({phase})",
        f"Validation test cases for {phase} have been generated and stored at {s3_path}",
        metadata={
            "generated_item": test_cases,
            "path": s3_path,
            "phase": phase,
            "test_count": len(test_cases.get("tests", [])) if isinstance(test_cases, dict) else 0
        }
    )


def format_query_generated_log(query: str, test_name: str, query_type: str = "validation") -> Dict[str, Any]:
    """
    Format a SQL query generation completion log.
    
    Args:
        query: Generated SQL query
        test_name: Name of the test
        query_type: Type of query (validation, remediation, etc.)
        
    Returns:
        Formatted log entry
    """
    return create_log_entry(
        LogType.QUERY_GENERATED,
        f"SQL Query Generated Successfully",
        f"{query_type.capitalize()} query generated for test: {test_name}",
        metadata={
            "generated_item": query,
            "test_name": test_name,
            "query_type": query_type,
            "query_length": len(query)
        }
    )


def format_query_executed_log(query: str, result: Any, test_name: str, passed: bool) -> Dict[str, Any]:
    """
    Format a SQL query execution completion log.
    
    Args:
        query: Executed SQL query
        result: Query result
        test_name: Name of the test
        passed: Whether the test passed
        
    Returns:
        Formatted log entry
    """
    return create_log_entry(
        LogType.QUERY_EXECUTED,
        f"Query Executed Successfully",
        f"Query for test '{test_name}' executed - Result: {'PASS' if passed else 'FAIL'}",
        metadata={
            "query": query,
            "result": result,
            "test_name": test_name,
            "passed": passed
        }
    )


def format_test_cases_executed_log(results: Dict[str, Any], phase: str, passed_count: int, failed_count: int) -> Dict[str, Any]:
    """
    Format a test cases execution completion log.
    
    Args:
        results: Test execution results
        phase: Validation phase
        passed_count: Number of passed tests
        failed_count: Number of failed tests
        
    Returns:
        Formatted log entry
    """
    total = passed_count + failed_count
    pass_rate = (passed_count / total * 100) if total > 0 else 0
    
    return create_log_entry(
        LogType.TEST_CASES_EXECUTED,
        f"Test Cases Executed Successfully ({phase})",
        f"Executed {total} tests - {passed_count} passed, {failed_count} failed ({pass_rate:.1f}% pass rate)",
        metadata={
            "phase": phase,
            "total_tests": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": round(pass_rate, 2),
            "results": results
        }
    )


def format_validation_phase_completed_log(phase: str, status: str, results_path: str, summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a validation phase completion log.
    
    Args:
        phase: Validation phase name
        status: Phase status (pass/fail)
        results_path: S3 path to results
        summary: Summary of validation results
        
    Returns:
        Formatted log entry
    """
    return create_log_entry(
        LogType.VALIDATION_PHASE_COMPLETED,
        f"Validation {phase} Completed",
        f"Validation {phase} completed with status: {status.upper()}",
        metadata={
            "phase": phase,
            "status": status,
            "results_path": results_path,
            **summary
        }
    )


def format_remediation_completed_log(iteration: int, status: str, changes_made: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a remediation completion log.
    
    Args:
        iteration: Remediation iteration number
        status: Remediation status
        changes_made: Optional details of changes made
        
    Returns:
        Formatted log entry
    """
    metadata = {
        "iteration": iteration,
        "status": status
    }
    
    if changes_made:
        metadata["changes_made"] = changes_made
    
    return create_log_entry(
        LogType.REMEDIATION_COMPLETED,
        f"Remediation Iteration {iteration} Completed",
        f"Remediation iteration {iteration} completed with status: {status}",
        metadata=metadata
    )
