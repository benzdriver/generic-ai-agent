# src/scripts/load_and_index.py

import sys
import os
from knowledge_ingestion.doc_parser import parse_ircc_html, parse_ircc_text
from vector_engine.vector_indexer import upsert_documents


def main():
    if len(sys.argv) < 2:
        print("用法: python load_and_index.py <file_path> [html|txt]")
        return

    file_path = sys.argv[1]
    file_type = sys.argv[2] if len(sys.argv) > 2 else "txt"

    if file_type == "html":
        chunks = parse_ircc_html(file_path)
    else:
        chunks = parse_ircc_text(file_path)

    print(f"🧩 提取 {len(chunks)} 个段落，开始写入向量数据库...")
    metadata = {
        "source": os.path.basename(file_path),
        "domain": "canada_immigration"
    }
    upsert_documents(chunks, metadata)
    print("✅ 写入完成！")


if __name__ == '__main__':
    main()