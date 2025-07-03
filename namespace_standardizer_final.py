#!/usr/bin/env python3
"""
네임스페이스 표준화 최종 스크립트 (전체 모듈 처리)
모든 폴더의 함수명을 디렉토리 기준으로 표준화
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple

class NamespaceStandardizerFinal:
    def __init__(self):
        self.rename_mappings: Dict[str, List[Tuple[str, str]]] = {}
        self.renamed_count = 0
        self.change_log: List[str] = []
        
    def standardize_project(self, project_root: str = "src"):
        print("🔍 네임스페이스 표준화 최종 시작...")
        self._analyze_all_modules(project_root)
        self._identify_all_namespace_issues(project_root)
        self._rename_all_functions(project_root)
        print(f"✅ 네임스페이스 표준화 완료: {self.renamed_count}개 변경됨")
        if self.change_log:
            print("\n[변경 로그]")
            for log in self.change_log:
                print(log)
    
    def _analyze_all_modules(self, project_root: str):
        print("📋 모든 모듈 분석 중...")
        for py_file in Path(project_root).rglob("*.py"):
            if py_file.name.endswith('.backup'):
                continue  # 백업 파일 제외
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content)
                self._extract_all_functions(tree, str(py_file))
            except Exception as e:
                print(f"⚠️ 파일 파싱 실패: {py_file}, 오류: {e}")
    
    def _extract_all_functions(self, tree: ast.AST, file_path: str):
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 공통 함수들 제외
                if node.name not in ["__init__", "main", "health_check", "get_metrics", "lifespan"]:
                    functions.append(node.name)
        if functions:
            self.rename_mappings[file_path] = []
            for func_name in functions:
                self.rename_mappings[file_path].append((func_name, func_name))
    
    def _identify_all_namespace_issues(self, project_root: str):
        print("🔍 모든 네임스페이스 불일치 식별 중...")
        for file_path, functions in self.rename_mappings.items():
            # 디렉토리명 기준 접두사 (더 포괄적으로)
            norm_path = file_path.replace('\\', '/').lower()
            
            # 각 디렉토리별 접두사 규칙
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
            elif '/tests/' in norm_path:
                prefix = 'test_'
            else:
                # 파일명 기준 접두사
                file_stem = Path(file_path).stem
                if file_stem in ['audio', 'text', 'db', 'utils', 'gateway', 'auth', 'upload']:
                    prefix = f'{file_stem}_'
                else:
                    prefix = ''
            
            # 함수명 변경 필요 여부 확인
            for i, (old_name, new_name) in enumerate(functions):
                if prefix and not old_name.startswith(prefix) and not old_name.startswith('_'):
                    suggested_name = f"{prefix}{old_name}"
                    self.rename_mappings[file_path][i] = (old_name, suggested_name)
    
    def _rename_all_functions(self, project_root: str):
        print("🔄 모든 함수명/호출/import/테스트 코드 일괄 변경 중...")
        for file_path, rename_list in self.rename_mappings.items():
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                modified_content = content
                changed_count = 0
                file_changes = []
                
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
                            file_changes.append(f"{old_name} → {new_name} (정의:{def_count}, 호출:{call_count}, import:{import_count}, 테스트:{test_count})")
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
                    self.change_log.append(f"{file_path}: {len(file_changes)}개 함수 변경")
                    for change in file_changes:
                        self.change_log.append(f"  - {change}")
                        
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
    standardizer = NamespaceStandardizerFinal()
    standardizer.standardize_project()
    print("\n🎉 네임스페이스 표준화 최종 완료!")
    print(f"📊 총 {standardizer.renamed_count}개의 함수명이 변경되었습니다.")

if __name__ == "__main__":
    main() 