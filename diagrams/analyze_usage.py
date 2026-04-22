import collections
import os
import re

src_dir = "src/main/java/com/google/protobuf"

class_regex = re.compile(
    r"(?:public|protected|private)?\s*(?:abstract)?\s*(class|interface)\s+(\w+)"
)
class_to_file = {}
file_contents = {}

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

                matches = class_regex.findall(content)
                for match in matches:
                    kind, name = match
                    name = name.strip()
                    class_to_file[name] = file

print(f"Found {len(class_to_file)} classes.")

counts = collections.defaultdict(int)

for name, defining_file in class_to_file.items():
    for file, content in file_contents.items():
        if file == defining_file:
            continue
        if re.search(r"\b" + re.escape(name) + r"\b", content):
            counts[name] += 1

brackets = [0, 1, 3, 5, 10, 20, 50]

print("Reference distribution:")
for b in brackets:
    c = sum(1 for n, count in counts.items() if count >= b)
    print(f">= {b} references: {c} classes")

# Print list of top classes for context
top_classes = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:20]
print("\nTop 20 most referenced classes:")
for name, count in top_classes:
    print(f"  {name}: {count}")
