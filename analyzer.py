import ast
import re

# Regex patterns for hardcoded secrets/keys and unsafe SQL operations
SECRET_PATTERNS = [
    r"(?i)(api_key|secret|password|access_key|token)\s*=\s*['\"][A-Za-z0-9_\-]{8,}['\"]",
    r"AKIA[0-9A-Z]{16}",  # AWS Access Key ID
]

SQLI_PATTERNS = [
    r"(?i)select\s+.*\s+from\s+.*%",
    r"(?i)select\s+.*\s+from\s+.*\.format\(",
    r"(?i)select\s+.*\s+from\s+.*f['\"]",
    r"(?i)(execute|cursor\.execute)\s*\(\s*f['\"]",
]

class ASTVisitor(ast.NodeVisitor):
    def __init__(self):
        self.issues = []

    def visit_For(self, node):
        self._check_loop_nesting(node)
        self.generic_visit(node)

    def visit_While(self, node):
        self._check_loop_nesting(node)
        self.generic_visit(node)

    def _check_loop_nesting(self, node):
        # Check if a loop contains another loop (O(n^2) complexity check)
        for child in ast.walk(node):
            if child is not node and isinstance(child, (ast.For, ast.While)):
                self.issues.append(f"⚠️ **Performance Issue:** Nested loop detected near line {node.lineno} (O(n²) time complexity).")
                break

    def visit_Call(self, node):
        # Detect dangerous execution functions like eval() and exec()
        if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
            self.issues.append(f"🚨 **Security Vulnerability:** Use of dangerous function `{node.func.id}()` near line {node.lineno}.")
        self.generic_visit(node)


def analyze_code(file_path: str, code_content: str) -> list:
    """
    Safely analyzes code content for security flaws and performance issues.
    Guarantees no unhandled exceptions will crash the main server.
    """
    issues = []

    # Edge Case 1: Ignore empty files or empty diff content
    if not code_content or not code_content.strip():
        return []

    # Edge Case 2: Ignore non-Python files (.md, .json, .yml, .txt, etc.)
    if not file_path.endswith(".py"):
        return []

    # 1. Regex Checks (Secrets & SQL Injection)
    for line_num, line in enumerate(code_content.splitlines(), start=1):
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line):
                issues.append(f"🚨 **Security Leak:** Potential hardcoded secret/API key on line {line_num}.")
                break
        for pattern in SQLI_PATTERNS:
            if re.search(pattern, line):
                issues.append(f"🚨 **Security Risk:** Potential SQL Injection pattern on line {line_num}.")
                break

    # 2. AST Parsing wrapped safely in try...except
    try:
        parsed_ast = ast.parse(code_content)
        visitor = ASTVisitor()
        visitor.visit(parsed_ast)
        issues.extend(visitor.issues)
    except SyntaxError as e:
        # Gracefully log syntax errors without throwing an unhandled exception
        issues.append(f"⚠️ **Syntax Warning:** Unable to parse AST due to syntax error on line {e.lineno}: `{e.msg}`.")
    except Exception as e:
        # Fallback catch-all to guarantee server stability
        issues.append(f"⚠️ **Analysis Warning:** AST analysis skipped on `{file_path}` ({str(e)}).")

    return issues