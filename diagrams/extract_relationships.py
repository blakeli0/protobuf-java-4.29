import os
import re

src_dir = "src/main/java/com/google/protobuf"
output_file = "/Users/blakeli/.gemini/jetski/brain/de0272b4-ed49-4fda-b7c3-b985dc171776/scratch/protobuf_relationships.dot"

# A slightly more robust regex to find class definitions
class_regex = re.compile(
    r"(?:public|protected|private)?\s*(?:abstract)?\s*(class|interface)\s+(\w+)(?:\s+extends\s+([^{]+))?(?:\s+implements\s+([^{]+))?\{"
)

def clean_name(name):
    if not name:
        return ""
    # Remove generics for simplicity
    name = re.sub(r"<.*?>", "", name)
    # Remove whitespace
    name = name.strip()
    # Handle multiple extends/implements separated by commas
    return [n.strip() for n in name.split(",") if n.strip()]

nodes = set()
edges = set()

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".java"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Remove comments to avoid false matches
                content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
                content = re.sub(r"//.*", "", content)

                matches = class_regex.finditer(content)
                for match in matches:
                    kind, name, extends, implements = match.groups()
                    name = name.strip()
                    nodes.add((name, kind))

                    if extends:
                        for ext in clean_name(extends):
                            edges.add((name, ext, "extends"))
                    if implements:
                        for imp in clean_name(implements):
                            edges.add((name, imp, "implements"))

with open(output_file, "w") as f:
    f.write("digraph ProtobufRelationships {\n")
    f.write("  rankdir=BT;\n") # Bottom to top usually looks better for inheritance
    f.write('  node [shape=box, style=filled, fillcolor=lightblue];\n')

    for name, kind in nodes:
        fillcolor = "lightblue" if kind == "class" else "lightgreen"
        f.write(f'  "{name}" [fillcolor={fillcolor}];\n')

    for src, dst, rel in edges:
        style = "solid" if rel == "extends" else "dashed"
        f.write(f'  "{src}" -> "{dst}" [style={style}];\n')

    f.write("}\n")

print(f"Generated {output_file} with {len(nodes)} nodes and {len(edges)} edges.")
