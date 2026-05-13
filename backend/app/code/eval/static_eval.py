"""
Static Code Evaluator - Syntax, lint, and risk analysis.

Tier A evaluation that runs without execution.
"""

import ast
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Diagnostic severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    """A single diagnostic message."""
    severity: Severity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    code: Optional[str] = None  # Error code like "E001"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "code": self.code,
        }


@dataclass
class StaticEvalResult:
    """Result of static evaluation."""
    passed: bool
    syntax_valid: bool
    error_count: int
    warning_count: int
    info_count: int
    diagnostics: List[Diagnostic] = field(default_factory=list)
    risks: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "syntax_valid": self.syntax_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "risks": self.risks,
        }


# Dangerous patterns to detect
RISK_PATTERNS = {
    "python": [
        (r"\bos\.system\s*\(", "os.system call - potential command injection"),
        (r"\bsubprocess\.(run|call|Popen)\s*\(", "subprocess call - potential command injection"),
        (r"\beval\s*\(", "eval() call - potential code injection"),
        (r"\bexec\s*\(", "exec() call - potential code injection"),
        (r"\b__import__\s*\(", "dynamic import - potential security risk"),
        (r"\bopen\s*\([^)]*['\"]w['\"]", "file write operation"),
        (r"\bshutil\.rmtree\s*\(", "recursive directory deletion"),
        (r"\bos\.remove\s*\(", "file deletion"),
        (r"\bos\.unlink\s*\(", "file deletion"),
        (r"\brequests\.(get|post|put|delete)\s*\(", "HTTP request - network access"),
        (r"\burllib", "URL library - network access"),
        (r"\bsocket\.", "socket operations - network access"),
        (r"\bpickle\.load", "pickle load - potential code execution"),
    ],
    "typescript": [
        (r"\beval\s*\(", "eval() call - potential code injection"),
        (r"\bFunction\s*\(", "Function constructor - potential code injection"),
        (r"\bchild_process", "child_process - potential command injection"),
        (r"\bfs\.writeFile", "file write operation"),
        (r"\bfs\.unlink", "file deletion"),
        (r"\bfs\.rmdir", "directory deletion"),
        (r"\bfetch\s*\(", "fetch call - network access"),
        (r"\baxios\.", "axios - network access"),
        (r"\brequire\s*\(['\"]child_process", "child_process require"),
    ],
}


class StaticEvaluator:
    """
    Static code evaluator.
    
    Performs:
    - Syntax validation
    - Risk pattern detection
    - Basic lint checks
    """
    
    def __init__(self):
        self.risk_patterns = RISK_PATTERNS
    
    def _check_python_syntax(self, code: str, filename: str = "<code>") -> List[Diagnostic]:
        """Check Python syntax using ast.parse."""
        diagnostics = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR,
                message=f"Syntax error: {e.msg}",
                file=filename,
                line=e.lineno,
                code="E001",
            ))
        except Exception as e:
            diagnostics.append(Diagnostic(
                severity=Severity.ERROR,
                message=f"Parse error: {str(e)}",
                file=filename,
                code="E002",
            ))
        
        return diagnostics
    
    def _check_typescript_syntax(self, code: str, filename: str = "<code>") -> List[Diagnostic]:
        """Basic TypeScript/JavaScript syntax check."""
        diagnostics = []
        
        # Basic bracket matching
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        for i, char in enumerate(code):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    diagnostics.append(Diagnostic(
                        severity=Severity.ERROR,
                        message=f"Unmatched closing bracket '{char}'",
                        file=filename,
                        line=code[:i].count('\n') + 1,
                        code="E003",
                    ))
                else:
                    open_bracket, _ = stack.pop()
                    if brackets[open_bracket] != char:
                        diagnostics.append(Diagnostic(
                            severity=Severity.ERROR,
                            message=f"Mismatched brackets: expected '{brackets[open_bracket]}' but found '{char}'",
                            file=filename,
                            line=code[:i].count('\n') + 1,
                            code="E004",
                        ))
        
        if stack:
            for bracket, pos in stack:
                diagnostics.append(Diagnostic(
                    severity=Severity.ERROR,
                    message=f"Unclosed bracket '{bracket}'",
                    file=filename,
                    line=code[:pos].count('\n') + 1,
                    code="E005",
                ))
        
        return diagnostics
    
    def _detect_risks(self, code: str, language: str, filename: str = "<code>") -> List[Dict[str, Any]]:
        """Detect risky patterns in code."""
        risks = []
        patterns = self.risk_patterns.get(language, [])
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, start=1):
            for pattern, description in patterns:
                if re.search(pattern, line):
                    risks.append({
                        "pattern": pattern,
                        "description": description,
                        "file": filename,
                        "line": line_num,
                        "snippet": line.strip()[:100],
                    })
        
        return risks
    
    def _basic_lint(self, code: str, language: str, filename: str = "<code>") -> List[Diagnostic]:
        """Basic lint checks."""
        diagnostics = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            # Check line length
            if len(line) > 120:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=f"Line too long ({len(line)} > 120 characters)",
                    file=filename,
                    line=line_num,
                    code="W001",
                ))
            
            # Check trailing whitespace
            if line.rstrip() != line and line.strip():
                diagnostics.append(Diagnostic(
                    severity=Severity.INFO,
                    message="Trailing whitespace",
                    file=filename,
                    line=line_num,
                    code="I001",
                ))
            
            # Python-specific
            if language == "python":
                # Check for print statements (might be debug)
                if re.match(r'^\s*print\s*\(', line):
                    diagnostics.append(Diagnostic(
                        severity=Severity.INFO,
                        message="print() statement found (might be debug code)",
                        file=filename,
                        line=line_num,
                        code="I002",
                    ))
                
                # Check for TODO/FIXME
                if re.search(r'#\s*(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
                    diagnostics.append(Diagnostic(
                        severity=Severity.INFO,
                        message="TODO/FIXME comment found",
                        file=filename,
                        line=line_num,
                        code="I003",
                    ))
        
        return diagnostics
    
    def evaluate(
        self,
        code: str,
        language: str = "python",
        filename: str = "<code>",
        check_risks: bool = True,
        check_lint: bool = True,
    ) -> StaticEvalResult:
        """
        Evaluate code statically.
        
        Args:
            code: Source code to evaluate
            language: Programming language
            filename: Filename for diagnostics
            check_risks: Whether to check for risky patterns
            check_lint: Whether to run lint checks
            
        Returns:
            StaticEvalResult with diagnostics
        """
        diagnostics = []
        risks = []
        syntax_valid = True
        
        # Syntax check
        if language == "python":
            syntax_diags = self._check_python_syntax(code, filename)
        elif language in ("typescript", "javascript"):
            syntax_diags = self._check_typescript_syntax(code, filename)
        else:
            syntax_diags = []  # Skip syntax check for unknown languages
        
        diagnostics.extend(syntax_diags)
        syntax_valid = not any(d.severity == Severity.ERROR for d in syntax_diags)
        
        # Risk detection
        if check_risks:
            risks = self._detect_risks(code, language, filename)
            for risk in risks:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    message=f"Risk: {risk['description']}",
                    file=risk['file'],
                    line=risk['line'],
                    code="R001",
                ))
        
        # Lint checks
        if check_lint:
            lint_diags = self._basic_lint(code, language, filename)
            diagnostics.extend(lint_diags)
        
        # Count by severity
        error_count = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
        warning_count = sum(1 for d in diagnostics if d.severity == Severity.WARNING)
        info_count = sum(1 for d in diagnostics if d.severity == Severity.INFO)
        
        # Passed if no errors
        passed = error_count == 0
        
        return StaticEvalResult(
            passed=passed,
            syntax_valid=syntax_valid,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            diagnostics=diagnostics,
            risks=risks,
        )
    
    def evaluate_diff(
        self,
        diff: str,
        base_language: str = "python",
    ) -> StaticEvalResult:
        """
        Evaluate a unified diff.
        
        Extracts added lines and checks them.
        
        Args:
            diff: Unified diff string
            base_language: Language of the code
            
        Returns:
            StaticEvalResult for added code
        """
        # Extract added lines from diff
        added_lines = []
        current_file = None
        
        for line in diff.split('\n'):
            if line.startswith('+++'):
                current_file = line[4:].strip()
            elif line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
        
        if not added_lines:
            return StaticEvalResult(
                passed=True,
                syntax_valid=True,
                error_count=0,
                warning_count=0,
                info_count=0,
                diagnostics=[],
                risks=[],
            )
        
        # Evaluate added code
        added_code = '\n'.join(added_lines)
        return self.evaluate(added_code, base_language, current_file or "<diff>")
