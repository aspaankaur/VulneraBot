import re
import ast

def check_secrets(diff_text: str) -> list:
    """Regex scanning for exposed secrets and private keys."""
    issues = []
    secret_patterns = [
        (r'(?i)(api[_\-]?key|secret|password|passwd|private[_\-]?key)\s*[:=]\s*["\'][A-Za-z0-9_\-]{8,}["\']', "Exposed Secret / API Key"),
        (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key Leak"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID Leak")
    ]
    
    for pattern, description in secret_patterns:
        if re.search(pattern, diff_text):
            issues.append(f"🚨 **Security Risk**: Detected {description} in diff.")
            
    return issues


def check_sql_injection(diff_text: str) -> list:
    """Detect unsafe dynamic SQL construction."""
    issues = []
    sql_patterns = [
        r'(?i)SELECT\s+.*FROM\s+.*(%s|\+\s*|\{\}|f["\'])',
        r'(?i)INSERT\s+INTO\s+.*VALUES\s*\(.*(%s|\+\s*|\{\}|f["\'])',
        r'(?i)UPDATE\s+.*SET\s+.*(%s|\+\s*|\{\}|f["\'])'
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, diff_text):
            issues.append("⚠️ **Security Risk**: Unsafe string formatting detected in SQL query (Potential SQL Injection).")
            break
            
    return issues


class LoopNestingVisitor(ast.NodeVisitor):
    """AST Parser to count loop nesting depth."""
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0

    def visit_For(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_While(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1


def check_nested_loops(diff_text: str) -> list:
    """Parses valid Python snippets in diff text using AST to find O(n^2) complexity."""
    issues = []
    added_lines = [line[1:] for line in diff_text.split('\n') if line.startswith('+') and not line.startswith('+++')]
    python_code = "\n".join(added_lines)

    try:
        tree = ast.parse(python_code)
        visitor = LoopNestingVisitor()
        visitor.visit(tree)
        if visitor.max_depth >= 2:
            issues.append(f"🐢 **Performance Warning**: Detected nested loop structure (Depth: {visitor.max_depth}). Verify time complexity.")
    except Exception:
        loop_count = len(re.findall(r'^\+\s*(for|while)\s+', diff_text, re.MULTILINE))
        if loop_count >= 2:
            issues.append("🐢 **Performance Warning**: Multiple added loops detected in close proximity. Potential O(n^2) complexity.")

    return issues


def run_static_analysis(diff_text: str) -> list:
    """Main execution entry point for all static checks."""
    all_issues = []
    all_issues.extend(check_secrets(diff_text))
    all_issues.extend(check_sql_injection(diff_text))
    all_issues.extend(check_nested_loops(diff_text))
    return all_issues