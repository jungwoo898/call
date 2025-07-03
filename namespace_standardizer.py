#!/usr/bin/env python3
"""
네임스페이스 표준화 스크립트 (디렉토리명 기준, 안전 백업)
함수명을 모듈에 맞게 표준화하며, 함수 정의/호출/import/테스트 코드까지 일괄 치환
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple

class NamespaceStandardizer:
    def __init__(self):
        self.rename_mappings: Dict[str, List[Tuple[str, str]]] = {}
        self.renamed_count = 0
        self.change_log: List[str] = []
        
    def standardize_project(self, project_root: str = "src"):
        print("🔍 네임스페이스 표준화 시작...")
        self._analyze_modules(project_root)
        self._identify_namespace_issues(project_root)
        self._rename_functions(project_root)
        print(f"✅ 네임스페이스 표준화 완료: {self.renamed_count}개 변경됨")
        if self.change_log:
            print("\n[변경 로그]")
            for log in self.change_log:
                print(log)
    
    def _analyze_modules(self, project_root: str):
        print("📋 모듈 분석 중...")
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                self._extract_functions(tree, str(py_file))
            except Exception as e:
                print(f"⚠️ 파일 파싱 실패: {py_file}, 오류: {e}")
    
    def _extract_functions(self, tree: ast.AST, file_path: str):
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in ["__init__", "main", "health_check", "get_metrics"]:
                    functions.append(node.name)
        if functions:
            self.rename_mappings[file_path] = []
            for func_name in functions:
                self.rename_mappings[file_path].append((func_name, func_name))
    
    def _identify_namespace_issues(self, project_root: str):
        print("🔍 네임스페이스 불일치 식별 중...")
        for file_path, functions in self.rename_mappings.items():
            # 디렉토리명 기준 접두사
            norm_path = file_path.replace('\\', '/').lower()
            if '/audio/' in norm_path:
                prefix = 'audio_'
            elif '/text/' in norm_path:
                prefix = 'text_'
            elif '/db/' in norm_path:
                prefix = 'db_'
            elif '/utils/' in norm_path:
                prefix = 'util_'
            elif '/gateway/' in norm_path:
                prefix = 'gateway_'
            elif '/auth/' in norm_path:
                prefix = 'auth_'
            elif '/upload/' in norm_path:
                prefix = 'upload_'
            else:
                prefix = ''
            for i, (old_name, new_name) in enumerate(functions):
                if prefix and not old_name.startswith(prefix) and not old_name.startswith('_'):
                    suggested_name = f"{prefix}{old_name}"
                    self.rename_mappings[file_path][i] = (old_name, suggested_name)
    
    def _rename_functions(self, project_root: str):
        print("🔄 함수명/호출/import/테스트 코드 일괄 변경 중...")
        for file_path, rename_list in self.rename_mappings.items():
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                modified_content = content
                changed_count = 0
                for old_name, new_name in rename_list:
                    if old_name != new_name:
                        # 함수 정의 변경
                        modified_content, def_count = self._rename_function_definition(modified_content, old_name, new_name)
                        # 함수 호출 변경
                        modified_content, call_count = self._rename_function_calls(modified_content, old_name, new_name)
                        # import 변경
                        modified_content, import_count = self._rename_imports(modified_content, old_name, new_name)
                        # 테스트 코드 변경
                        modified_content, test_count = self._rename_test_functions(modified_content, old_name, new_name)
                        total = def_count + call_count + import_count + test_count
                        if total > 0:
                            self.change_log.append(f"{file_path}: {old_name} → {new_name} (정의:{def_count}, 호출:{call_count}, import:{import_count}, 테스트:{test_count})")
                        changed_count += total
                if changed_count > 0 and modified_content != content:
                    # 백업 생성
                    backup_path = f"{file_path}.backup"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    # 수정된 내용 저장
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    self.renamed_count += changed_count
            except Exception as e:
                print(f"⚠️ 파일 처리 실패: {file_path}, 오류: {e}")
    def _rename_function_definition(self, content: str, old_name: str, new_name: str):
        pattern = rf'(def\s+){re.escape(old_name)}(\s*\()'
        new_content, count = re.subn(pattern, rf'\1{new_name}\2', content)
        return new_content, count
    def _rename_function_calls(self, content: str, old_name: str, new_name: str):
        pattern = rf'(?<!def\s)(?<!class\s)\b{re.escape(old_name)}\s*\('
        new_content, count = re.subn(pattern, f'{new_name}(', content)
        return new_content, count
    def _rename_imports(self, content: str, old_name: str, new_name: str):
        pattern = rf'(from\s+\S+\s+import\s+.*)\b{re.escape(old_name)}\b'
        new_content, count = re.subn(pattern, lambda m: m.group(0).replace(old_name, new_name), content)
        return new_content, count
    def _rename_test_functions(self, content: str, old_name: str, new_name: str):
        pattern = rf'(def\s+test_)({re.escape(old_name)})(\s*\()'
        new_content, count = re.subn(pattern, rf'\1{new_name}\3', content)
        return new_content, count

def main():
    standardizer = NamespaceStandardizer()
    standardizer.standardize_project()
    print("\n🎉 네임스페이스 표준화 완료!")
    print(f"📊 총 {standardizer.renamed_count}개의 함수명이 변경되었습니다.")

if __name__ == "__main__":
    main() 