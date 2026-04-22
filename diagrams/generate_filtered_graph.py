import collections
import os
import re

src_dir = "src/main/java/com/google/protobuf"
output_file = "/Users/blakeli/.gemini/jetski/brain/de0272b4-ed49-4fda-b7c3-b985dc171776/scratch/protobuf_filtered.dot"
threshold = 5

class_regex = re.compile(
    r"(?:public|protected|private)?\s*(?:abstract)?\s*(class|interface)\s+(\w+)(?:\s+extends\s+([^{]+))?(?:\s+implements\s+([^{]+))?\{"
)
class_to_file = {}
file_contents = {}
class_kinds = {}

# First pass: find all classes and their files
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".java"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Remove comments
                content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
                content = re.sub(r"//.*", "", content)

                file_contents[file] = content

                matches = class_regex.finditer(content)
                for match in matches:
                    kind, name, extends, implements = match.groups()
                    name = name.strip()
                    class_to_file[name] = file
                    class_kinds[name] = kind

print(f"Found {len(class_to_file)} classes.")

# Second pass: count references
counts = collections.defaultdict(int)

for name, defining_file in class_to_file.items():
    if name == "for":  # Skip known false positive
        continue
    for file, content in file_contents.items():
        if file == defining_file:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", content):
            counts[name] += 1

# Filter classes
filtered_classes = {name for name, count in counts.items() if count >= threshold}
print(f"Filtered to {len(filtered_classes)} classes with >= {threshold} references.")

def clean_name(name):
    if not name:
        return []
    name = re.sub(r"<.*?>", "", name)
    return [n.strip() for n in name.split(",") if n.strip()]

edges = set()

# Third pass: extract relationships between filtered classes
for file, content in file_contents.items():
    matches = class_regex.finditer(content)
    for match in matches:
        kind, name, extends, implements = match.groups()
        name = name.strip()

        if name not in filtered_classes:
            continue

        if extends:
            for ext in clean_name(extends):
                if ext in filtered_classes:
                    edges.add((name, ext, "extends"))
        if implements:
            for imp in clean_name(implements):
                if imp in filtered_classes:
                    edges.add((name, imp, "implements"))

# Generate DOT file
with open(output_file, "w") as f:
    f.write("digraph ProtobufFilteredRelationships {\n")
    f.write("  rankdir=BT;\n")
    f.write('  node [shape=box, style=filled, fillcolor=lightblue];\n')

    for name in filtered_classes:
        kind = class_kinds.get(name, "class")
        fillcolor = "lightblue" if kind == "class" else "lightgreen"
        f.write(f'  "{name}" [fillcolor={fillcolor}];\n')

    for src, dst, rel in edges:
        style = "solid" if rel == "extends" else "dashed"
        f.write(f'  "{src}" -> "{dst}" [style={style}];\n')

    f.write("}\n")

print(f"Generated {output_file}")
