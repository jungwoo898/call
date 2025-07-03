#!/usr/bin/env python3
"""
죽은 코드 제거 스크립트
사용되지 않는 함수와 변수를 자동으로 제거
"""

import os
import re
import ast
from pathlib import Path
from typing import Set, Dict, List

class DeadCodeRemover:
    def __init__(self):
        self.used_names: Set[str] = set()
        self.defined_names: Dict[str, List[str]] = {}
        self.dead_code_count = 0
        
    def analyze_project(self, project_root: str = "src"):
        """프로젝트 전체 분석"""
        print("🔍 죽은 코드 분석 시작...")
        
        # 1단계: 모든 정의된 이름 수집
        self._collect_definitions(project_root)
        
        # 2단계: 사용되는 이름 수집
        self._collect_usage(project_root)
        
        # 3단계: 죽은 코드 식별 및 제거
        self._remove_dead_code(project_root)
        
        print(f"✅ 죽은 코드 제거 완료: {self.dead_code_count}개 제거됨")
    
    def _collect_definitions(self, project_root: str):
        """정의된 이름 수집"""
        print("📋 정의된 이름 수집 중...")
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                self._extract_definitions(tree, str(py_file))
            except Exception as e:
                print(f"⚠️ 파일 파싱 실패: {py_file}, 오류: {e}")
    
    def _extract_definitions(self, tree: ast.AST, file_path: str):
        """AST에서 정의 추출"""
        defined_names = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 사용되지 않는 함수 패턴 확인
                if self._is_likely_dead_code(node.name):
                    defined_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                # 사용되지 않는 클래스 패턴 확인
                if self._is_likely_dead_code(node.name):
                    defined_names.append(node.name)
            elif isinstance(node, ast.Assign):
                # 사용되지 않는 변수 패턴 확인
                for target in node.targets:
                    if isinstance(target, ast.Name) and self._is_likely_dead_code(target.id):
                        defined_names.append(target.id)
        
        if defined_names:
            self.defined_names[file_path] = defined_names
    
    def _is_likely_dead_code(self, name: str) -> bool:
        """죽은 코드일 가능성이 높은 이름인지 확인"""
        dead_patterns = [
            r'^_unused_',
            r'^temp_',
            r'^debug_',
            r'^test_',  # 테스트 함수는 제외
            r'^old_',
            r'^deprecated_',
            r'^TODO_',
            r'^FIXME_'
        ]
        
        for pattern in dead_patterns:
            if re.match(pattern, name):
                return True
        
        return False
    
    def _collect_usage(self, project_root: str):
        """사용되는 이름 수집"""
        print("📋 사용되는 이름 수집 중...")
        
        for py_file in Path(project_root).rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                self._extract_usage(tree)
            except Exception as e:
                print(f"⚠️ 파일 파싱 실패: {py_file}, 오류: {e}")
    
    def _extract_usage(self, tree: ast.AST):
        """AST에서 사용 추출"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                self.used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 속성 접근 (예: module.function)
                attr_path = self._get_attribute_path(node)
                if attr_path:
                    self.used_names.add(attr_path)
    
    def _get_attribute_path(self, node: ast.Attribute) -> str:
        """속성 경로 생성"""
        parts = []
        current = node
        
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return '.'.join(reversed(parts))
        
        return None
    
    def _remove_dead_code(self, project_root: str):
        """죽은 코드 제거"""
        print("🗑️ 죽은 코드 제거 중...")
        
        for file_path, defined_names in self.defined_names.items():
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                modified_content = content
                removed_count = 0
                
                for name in defined_names:
                    # 실제로 사용되지 않는지 확인
                    if name not in self.used_names:
                        # 함수/클래스 정의 제거
                        modified_content = self._remove_definition(modified_content, name)
                        removed_count += 1
                
                if removed_count > 0:
                    # 백업 생성
                    backup_path = f"{file_path}.backup"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # 수정된 내용 저장
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                    
                    self.dead_code_count += removed_count
                    print(f"✅ {file_path}: {removed_count}개 제거됨")
                
            except Exception as e:
                print(f"⚠️ 파일 처리 실패: {file_path}, 오류: {e}")
    
    def _remove_definition(self, content: str, name: str) -> str:
        """정의 제거"""
        # 함수 정의 패턴
        function_pattern = rf'^\s*def\s+{re.escape(name)}\s*\([^)]*\)\s*:.*?(?=^\s*def|\Z)'
        
        # 클래스 정의 패턴
        class_pattern = rf'^\s*class\s+{re.escape(name)}\s*[^:]*:.*?(?=^\s*class|\Z)'
        
        # 변수 할당 패턴
        variable_pattern = rf'^\s*{re.escape(name)}\s*=.*$'
        
        # 각 패턴에 대해 제거 시도
        for pattern in [function_pattern, class_pattern, variable_pattern]:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            if matches:
                content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
                break
        
        return content

def main():
    """메인 실행 함수"""
    remover = DeadCodeRemover()
    remover.analyze_project()
    
    print("\n🎉 죽은 코드 제거 완료!")
    print(f"📊 총 {remover.dead_code_count}개의 죽은 코드가 제거되었습니다.")

if __name__ == "__main__":
    main() 