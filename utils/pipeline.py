import os
import sys
import subprocess
import json
import yaml
import zipfile
from datetime import datetime

class SessionAnalysisPipeline:

    def __init__(self, session_log_dir="logs", session_id=None, benchmark_type="partjob_bench"):
        self.session_log_dir = session_log_dir
        self.benchmark_type = benchmark_type
        self.session_id = session_id

        self.session_path = os.path.join(
            self.session_log_dir,
        )

        if not os.path.exists(self.session_path):
            raise ValueError(f"Session路径不存在: {self.session_path}")

        print(f"初始化Pipeline完成:")
        print(f"  - 基础目录: {self.session_log_dir}")
        print(f"  - Session ID: {self.session_id}")
        print(f"  - Session路径: {self.session_path}")
        print(f"  - Benchmark类型: {benchmark_type}")

    def run_visualization(self, mode="day", show=False):
        print(f"\n{'='*50}")
        print("开始可视化分析")
        print(f"{'='*50}")

        visualize_dir = "visualize"

        vis_scripts = {
            "vending_bench": os.path.join(visualize_dir, "vis_vending.py"),
            "partjob_bench": os.path.join(visualize_dir, "vis_partjob.py"),
            "operation_bench": os.path.join(visualize_dir, "vis_operation.py")
        }

        if self.benchmark_type not in vis_scripts:
            raise ValueError(f"不支持的benchmark_type: {self.benchmark_type}")

        vis_script = vis_scripts[self.benchmark_type]

        if not os.path.exists(vis_script):
            print(f"⚠️ 警告: 可视化脚本不存在: {vis_script}")
            print(f"请确保脚本路径正确: {vis_script}")
            return False

        cmd_args = [
            sys.executable,
            vis_script,
            "--sessions", self.session_id,
            "--mode", mode,
            "--logs-dir", "logs",
        ]

        if show:
            cmd_args.append("--show")

        output_name = f"visualization_{self.session_id}.png"
        output_path = os.path.join(self.self.session_log_dir, output_name)
        cmd_args.extend(["--output", output_path])

        print(f"执行命令: {' '.join(cmd_args)}")

        try:
            result = subprocess.run(cmd_args, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ 可视化分析完成")
                print(f"输出文件: {output_path}")
            else:
                print(f"❌ 可视化脚本执行失败:")
                if result.stdout:
                    print(f"标准输出: {result.stdout}")
                if result.stderr:
                    print(f"错误输出: {result.stderr}")
                return False
        except FileNotFoundError:
            print(f"❌ 找不到可视化脚本: {vis_script}")
            return False
        except Exception as e:
            print(f"❌ 执行可视化脚本时出错: {e}")
            return False

        print(f"\n{'='*50}")
        print("开始工具频率分析")
        print(f"{'='*50}")

        tool_analysis_script = os.path.join(visualize_dir, "vis_tool_freq.py")

        if not os.path.exists(tool_analysis_script):
            print(f"⚠️ 警告: 工具频率分析脚本不存在: {tool_analysis_script}")
            return True

        tool_analysis_cmd = [
            sys.executable,
            tool_analysis_script,
            "--sessions", self.session_id,
            "--logs-dir", self.session_log_dir,
        ]

        if show:
            tool_analysis_cmd.append("--show")

        tool_output_name = f"tool_freq_{self.session_id}.png"
        tool_output_path = os.path.join(self.session_path, tool_output_name)
        tool_analysis_cmd.extend(["--output", tool_output_path])

        print(f"执行命令: {' '.join(tool_analysis_cmd)}")

        try:
            result = subprocess.run(tool_analysis_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ 工具频率分析完成")
                print(f"输出文件: {tool_output_path}")
                return True
            else:
                print(f"❌ 工具频率分析脚本执行失败:")
                if result.stdout:
                    print(f"标准输出: {result.stdout}")
                if result.stderr:
                    print(f"错误输出: {result.stderr}")
                return False
        except FileNotFoundError:
            print(f"❌ 找不到工具频率分析脚本: {tool_analysis_script}")
            return False
        except Exception as e:
            print(f"❌ 执行工具频率分析脚本时出错: {e}")
            return False

    def convert_json_to_yaml(self):
        print(f"\n{'='*50}")
        print("开始JSON转YAML转换")
        print(f"{'='*50}")

        json_files = []

        for root, dirs, files in os.walk(self.session_path):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))

        if not json_files:
            print("⚠️ 未找到JSON文件")
            return False

        print(f"找到 {len(json_files)} 个JSON文件:")
        for json_file in json_files:
            print(f"  - {os.path.basename(json_file)}")

        converted_count = 0

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                yaml_file = json_file.replace('.json', '.yaml')

                with open(yaml_file, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)

                print(f"✅ 转换完成: {os.path.basename(json_file)} -> {os.path.basename(yaml_file)}")
                converted_count += 1

            except json.JSONDecodeError as e:
                print(f"❌ JSON解析失败 {os.path.basename(json_file)}: {e}")
            except Exception as e:
                print(f"❌ 转换失败 {os.path.basename(json_file)}: {e}")

        print(f"\n✅ JSON转YAML完成，共转换 {converted_count}/{len(json_files)} 个文件")
        return converted_count > 0

    def create_zip_archive(self, include_yaml=True):
        print(f"\n{'='*50}")
        print("开始创建ZIP压缩包")
        print(f"{'='*50}")


        zip_filename = f"{self.session_id}.zip"
        zip_path = os.path.join("logs", zip_filename)

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.session_path):
                    for file in files:
                        file_path = os.path.join(root, file)

                        if not include_yaml and file.endswith('.yaml'):
                            continue

                        arcname = os.path.join(
                            self.session_id,
                            os.path.relpath(file_path, self.session_path)
                        )

                        zipf.write(file_path, arcname)
                        print(f"📦 添加: {arcname}")


            print(f"\n✅ ZIP压缩包创建完成: {zip_path}")
            print(f"   - 文件大小: {os.path.getsize(zip_path) / 1024:.2f} KB")

            return zip_path

        except Exception as e:
            print(f"❌ 创建ZIP压缩包失败: {e}")
            return None

    def run_full_pipeline(self, mode="day", show=False, include_yaml=True):
        print(f"\n{'='*60}")
        print(f"开始执行完整流水线 - Session: {self.session_id}")
        print(f"{'='*60}")

        results = {
            "session_id": self.session_id,
            "session_path": self.session_path,
            "benchmark_type": self.benchmark_type,
            "timestamp": datetime.now().isoformat()
        }

        try:
            print("\n" + "="*60)
            print("步骤1: 运行可视化分析")
            print("="*60)
            vis_success = self.run_visualization(mode=mode, show=show)
            results["visualization_success"] = vis_success

            print("\n" + "="*60)
            print("步骤2: JSON转YAML转换")
            print("="*60)
            yaml_success = self.convert_json_to_yaml()
            results["yaml_conversion_success"] = yaml_success

            print("\n" + "="*60)
            print("步骤3: 创建ZIP压缩包")
            print("="*60)
            zip_path = self.create_zip_archive(include_yaml=include_yaml)
            results["zip_archive_path"] = zip_path
            results["zip_creation_success"] = zip_path is not None

            print("\n" + "="*60)
            print("流水线执行完成!")
            print("="*60)
            print(f"Session ID: {self.session_id}")
            print(f"可视化分析: {'✅ 成功' if vis_success else '❌ 失败'}")
            print(f"YAML转换: {'✅ 成功' if yaml_success else '❌ 失败'}")
            print(f"ZIP压缩包: {'✅ 成功' if zip_path else '❌ 失败'}")

            if zip_path:
                print(f"压缩包路径: {zip_path}")

            return results

        except Exception as e:
            print(f"❌ 流水线执行失败: {e}")
            results["error"] = str(e)
            return results
