import subprocess

print("🔁 正在执行知识聚类合并...")
subprocess.run(["python", "src/knowledge_manager/cluster_merger.py"])

print("🧹 正在清理已合并的原始条目...")
subprocess.run(["python", "src/knowledge_manager/delete_old_points.py"])

print("✅ 知识库每周合并与清理完成")
