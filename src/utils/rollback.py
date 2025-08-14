#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回滚机制 当构建失败时，自动恢复到之前的状态.
"""

import json
import shutil
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperationType(Enum):
    """
    操作类型枚举.
    """

    CREATE_FILE = "create_file"
    CREATE_DIR = "create_dir"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    MOVE_FILE = "move_file"
    COPY_FILE = "copy_file"


@dataclass
class RollbackOperation:
    """
    回滚操作记录.
    """

    operation_type: OperationType
    target_path: str
    backup_path: Optional[str] = None
    original_content: Optional[str] = None
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class RollbackManager:
    """
    回滚管理器.
    """

    def __init__(self, project_dir: Path, progress_manager=None):
        """初始化回滚管理器.

        Args:
            project_dir: 项目根目录
            progress_manager: 进度管理器
        """
        self.project_dir = project_dir
        self.progress = progress_manager
        self.rollback_dir = project_dir / ".unifypy_rollback"
        self.operations: List[RollbackOperation] = []
        self.session_id = str(int(time.time()))

        # 创建回滚目录
        self.rollback_dir.mkdir(exist_ok=True)

        # 备份目录
        self.backup_dir = self.rollback_dir / f"backup_{self.session_id}"
        self.backup_dir.mkdir(exist_ok=True)

        # 操作日志文件
        self.log_file = self.rollback_dir / f"operations_{self.session_id}.json"

    def __enter__(self):
        """
        进入上下文管理器.
        """
        self._log_info("开始跟踪文件操作...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器.
        """
        if exc_type is not None:
            # 发生异常，执行回滚
            self._log_info("检测到异常，开始自动回滚...")
            self.rollback()
        else:
            # 正常完成，清理回滚数据
            self._log_info("构建成功完成，清理回滚数据...")
            self.cleanup()

    def track_file_creation(self, file_path: Path) -> None:
        """
        跟踪文件创建.
        """
        operation = RollbackOperation(
            operation_type=OperationType.CREATE_FILE, target_path=str(file_path)
        )
        self.operations.append(operation)
        self._save_operations()
        self._log_debug(f"跟踪文件创建: {file_path}")

    def track_dir_creation(self, dir_path: Path) -> None:
        """
        跟踪目录创建.
        """
        operation = RollbackOperation(
            operation_type=OperationType.CREATE_DIR, target_path=str(dir_path)
        )
        self.operations.append(operation)
        self._save_operations()
        self._log_debug(f"跟踪目录创建: {dir_path}")

    def track_file_modification(self, file_path: Path) -> None:
        """
        跟踪文件修改.
        """
        if not file_path.exists():
            return

        # 创建备份
        backup_filename = f"{file_path.name}_{len(self.operations)}"
        backup_path = self.backup_dir / backup_filename

        try:
            shutil.copy2(file_path, backup_path)

            operation = RollbackOperation(
                operation_type=OperationType.MODIFY_FILE,
                target_path=str(file_path),
                backup_path=str(backup_path),
            )
            self.operations.append(operation)
            self._save_operations()
            self._log_debug(f"跟踪文件修改: {file_path}")

        except Exception as e:
            self._log_warning(f"备份文件失败: {file_path}, 错误: {e}")

    def track_file_deletion(self, file_path: Path) -> None:
        """
        跟踪文件删除.
        """
        if not file_path.exists():
            return

        # 创建备份
        backup_filename = f"{file_path.name}_{len(self.operations)}_deleted"
        backup_path = self.backup_dir / backup_filename

        try:
            shutil.copy2(file_path, backup_path)

            operation = RollbackOperation(
                operation_type=OperationType.DELETE_FILE,
                target_path=str(file_path),
                backup_path=str(backup_path),
            )
            self.operations.append(operation)
            self._save_operations()
            self._log_debug(f"跟踪文件删除: {file_path}")

        except Exception as e:
            self._log_warning(f"备份待删除文件失败: {file_path}, 错误: {e}")

    def track_file_move(self, src_path: Path, dst_path: Path) -> None:
        """
        跟踪文件移动.
        """
        operation = RollbackOperation(
            operation_type=OperationType.MOVE_FILE,
            target_path=str(dst_path),
            backup_path=str(src_path),  # 原始位置作为备份信息
        )
        self.operations.append(operation)
        self._save_operations()
        self._log_debug(f"跟踪文件移动: {src_path} -> {dst_path}")

    def safe_create_file(self, file_path: Path, content: str = "") -> None:
        """
        安全创建文件（带回滚跟踪）
        """
        self.track_file_creation(file_path)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self._log_error(f"创建文件失败: {file_path}, 错误: {e}")
            raise

    def safe_create_dir(self, dir_path: Path) -> None:
        """
        安全创建目录（带回滚跟踪）
        """
        if dir_path.exists():
            return

        self.track_dir_creation(dir_path)

        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self._log_error(f"创建目录失败: {dir_path}, 错误: {e}")
            raise

    def safe_modify_file(self, file_path: Path, content: str) -> None:
        """
        安全修改文件（带回滚跟踪）
        """
        self.track_file_modification(file_path)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self._log_error(f"修改文件失败: {file_path}, 错误: {e}")
            raise

    def safe_delete_file(self, file_path: Path) -> None:
        """
        安全删除文件（带回滚跟踪）
        """
        if not file_path.exists():
            return

        self.track_file_deletion(file_path)

        try:
            file_path.unlink()
        except Exception as e:
            self._log_error(f"删除文件失败: {file_path}, 错误: {e}")
            raise

    def safe_move_file(self, src_path: Path, dst_path: Path) -> None:
        """
        安全移动文件（带回滚跟踪）
        """
        if not src_path.exists():
            raise FileNotFoundError(f"源文件不存在: {src_path}")

        self.track_file_move(src_path, dst_path)

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
        except Exception as e:
            self._log_error(f"移动文件失败: {src_path} -> {dst_path}, 错误: {e}")
            raise

    def rollback(self) -> bool:
        """
        执行回滚操作.
        """
        if not self.operations:
            self._log_info("没有需要回滚的操作")
            return True

        self._log_info(f"开始回滚 {len(self.operations)} 个操作...")
        success_count = 0

        # 按时间倒序回滚
        for operation in reversed(self.operations):
            try:
                success = self._rollback_single_operation(operation)
                if success:
                    success_count += 1
                else:
                    self._log_warning(f"回滚操作失败: {operation.operation_type.value}")

            except Exception as e:
                self._log_error(
                    f"回滚操作时发生异常: {operation.operation_type.value}, 错误: {e}"
                )

        self._log_info(f"回滚完成: {success_count}/{len(self.operations)} 个操作成功")
        return success_count == len(self.operations)

    def _rollback_single_operation(self, operation: RollbackOperation) -> bool:
        """
        回滚单个操作.
        """
        target_path = Path(operation.target_path)

        try:
            if operation.operation_type == OperationType.CREATE_FILE:
                # 删除创建的文件
                if target_path.exists():
                    target_path.unlink()
                    self._log_debug(f"回滚: 删除文件 {target_path}")
                return True

            elif operation.operation_type == OperationType.CREATE_DIR:
                # 删除创建的目录（仅当为空时）
                if target_path.exists() and target_path.is_dir():
                    try:
                        target_path.rmdir()  # 只删除空目录
                        self._log_debug(f"回滚: 删除目录 {target_path}")
                    except OSError:
                        # 目录不为空，不强制删除
                        self._log_debug(f"目录不为空，跳过删除: {target_path}")
                return True

            elif operation.operation_type == OperationType.MODIFY_FILE:
                # 恢复文件内容
                if operation.backup_path and Path(operation.backup_path).exists():
                    shutil.copy2(operation.backup_path, target_path)
                    self._log_debug(f"回滚: 恢复文件 {target_path}")
                return True

            elif operation.operation_type == OperationType.DELETE_FILE:
                # 恢复删除的文件
                if operation.backup_path and Path(operation.backup_path).exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(operation.backup_path, target_path)
                    self._log_debug(f"回滚: 恢复删除的文件 {target_path}")
                return True

            elif operation.operation_type == OperationType.MOVE_FILE:
                # 移回原位置
                if target_path.exists() and operation.backup_path:
                    src_path = Path(operation.backup_path)
                    src_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(target_path), str(src_path))
                    self._log_debug(f"回滚: 移动文件 {target_path} -> {src_path}")
                return True

        except Exception as e:
            self._log_error(
                f"执行回滚操作失败: {operation.operation_type.value}, 错误: {e}"
            )
            return False

        return False

    def cleanup(self) -> None:
        """
        清理回滚数据.
        """
        try:
            # 删除备份目录
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)

            # 删除操作日志
            if self.log_file.exists():
                self.log_file.unlink()

            self._log_debug("回滚数据清理完成")

        except Exception as e:
            self._log_warning(f"清理回滚数据失败: {e}")

    def _save_operations(self) -> None:
        """
        保存操作记录到文件.
        """
        try:
            operations_data = [asdict(op) for op in self.operations]
            # 将枚举转换为字符串
            for op_data in operations_data:
                op_data["operation_type"] = op_data["operation_type"].value

            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(operations_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self._log_warning(f"保存操作记录失败: {e}")

    def load_operations(self, session_id: str) -> bool:
        """
        从文件加载操作记录.
        """
        log_file = self.rollback_dir / f"operations_{session_id}.json"

        if not log_file.exists():
            return False

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                operations_data = json.load(f)

            self.operations = []
            for op_data in operations_data:
                # 将字符串转换回枚举
                op_data["operation_type"] = OperationType(op_data["operation_type"])
                operation = RollbackOperation(**op_data)
                self.operations.append(operation)

            self.session_id = session_id
            self.backup_dir = self.rollback_dir / f"backup_{session_id}"
            self.log_file = log_file

            return True

        except Exception as e:
            self._log_error(f"加载操作记录失败: {e}")
            return False

    def list_rollback_sessions(self) -> List[str]:
        """
        列出可用的回滚会话.
        """
        sessions = []

        if not self.rollback_dir.exists():
            return sessions

        for file_path in self.rollback_dir.glob("operations_*.json"):
            session_id = file_path.stem.replace("operations_", "")
            sessions.append(session_id)

        return sorted(sessions, reverse=True)  # 按时间倒序

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话信息.
        """
        if not self.load_operations(session_id):
            return None

        if not self.operations:
            return None

        return {
            "session_id": session_id,
            "operation_count": len(self.operations),
            "start_time": min(op.timestamp for op in self.operations),
            "end_time": max(op.timestamp for op in self.operations),
            "operations": [
                {
                    "type": op.operation_type.value,
                    "target": op.target_path,
                    "timestamp": op.timestamp,
                }
                for op in self.operations
            ],
        }

    def _log_info(self, message: str):
        """
        记录信息日志.
        """
        if self.progress:
            self.progress.info(f"[回滚] {message}")
        else:
            print(f"[INFO] [回滚] {message}")

    def _log_warning(self, message: str):
        """
        记录警告日志.
        """
        if self.progress:
            self.progress.warning(f"[回滚] {message}")
        else:
            print(f"[WARNING] [回滚] {message}")

    def _log_error(self, message: str):
        """
        记录错误日志.
        """
        if self.progress:
            self.progress.on_error(Exception(message), "回滚系统")
        else:
            print(f"[ERROR] [回滚] {message}")

    def _log_debug(self, message: str):
        """
        记录调试日志.
        """
        if self.progress and hasattr(self.progress, "debug"):
            self.progress.debug(f"[回滚] {message}")
        # 在非详细模式下不输出调试信息
