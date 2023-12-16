import ast


class PythonFileAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.from_imports = []
        self.variables = {}
        self.classes = []
        self.comments = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.from_imports.append((node.module, alias.name))
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Assuming single target assignment for simplicity
        target = node.targets[0]
        if isinstance(target, ast.Name):
            self.variables[target.id] = ast.unparse(node.value)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        class_info = {
            "name": node.name,
            "bases": [ast.unparse(b) for b in node.bases],
            "body": "",
            "docstring": None,
        }

        # Extract docstring if present
        docstring = ast.get_docstring(node)
        if docstring:
            class_info["docstring"] = '"""' + docstring + '"""'

        # Handle the rest of the class body
        body_nodes = [n for n in node.body if not isinstance(n, ast.Expr)]
        class_info["body"] = "\n".join(ast.unparse(n) for n in body_nodes)

        self.classes.append(class_info)

    def visit_Module(self, node):
        self.comments = ast.get_docstring(node)
        self.generic_visit(node)

    def check_class_changed(self, other: "PythonFileAnalyzer") -> bool:
        """Compares the classes of this file with the classes of another file."""
        differences = {}
        self_classes = {c["name"]: c for c in self.classes}
        other_classes = {c["name"]: c for c in other.classes}

        all_class_names = set(self_classes.keys()) | set(other_classes.keys())

        for name in all_class_names:
            if name in self_classes and name in other_classes:
                # Compare attributes of classes with the same name
                class_diff = {
                    attr: (self_classes[name][attr], other_classes[name][attr])
                    for attr in self_classes[name]
                    if self_classes[name][attr] != other_classes[name][attr]
                }
                if class_diff:
                    return True
            else:
                return True

        return False
