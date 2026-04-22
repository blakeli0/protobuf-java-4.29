import collections
import os
import re

src_dir = "src/main/java/com/google/protobuf"
output_file = "/Users/blakeli/.gemini/jetski/brain/de0272b4-ed49-4fda-b7c3-b985dc171776/scratch/protobuf_dependencies.dot"
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

# Second pass: count references to filter
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

edges = set()

# Third pass: extract dependencies between filtered classes
for name in filtered_classes:
    defining_file = class_to_file.get(name)
    if not defining_file:
        continue
    content = file_contents.get(defining_file, "")

    for other_name in filtered_classes:
        if other_name == name:
            continue
        # Check if name's file references other_name
        if re.search(r"\b" + re.escape(other_name) + r"\b", content):
            edges.add((name, other_name))

# Generate DOT file
with open(output_file, "w") as f:
    f.write("digraph ProtobufDependencies {\n")
    f.write("  rankdir=BT;\n") # Bottom to top or Left to Right? Let's stick to BT or LR. LR is often better for dependencies.
    f.write('  node [shape=box, style=filled, fillcolor=lightblue];\n')

    for name in filtered_classes:
        kind = class_kinds.get(name, "class")
        fillcolor = "lightblue" if kind == "class" else "lightgreen"
        f.write(f'  "{name}" [fillcolor={fillcolor}];\n')

    for src, dst in edges:
        f.write(f'  "{src}" -> "{dst}";\n')

    f.write("}\n")

print(f"Generated {output_file} with {len(filtered_classes)} nodes and {len(edges)} edges.")
