#!/usr/bin/env python3
"""
코드 품질 분석 및 리팩터링 스크립트
중복 정의, 타입 불일치, 죽은 코드를 탐지하고 일관된 네임스페이스로 리팩터링합니다.
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeQualityAnalyzer:
    def __init__(self):
        self.duplicate_definitions = []
        self.type_mismatches = []
        self.dead_code = []
        self.namespace_inconsistencies = []
        self.import_issues = []
        self.function_signatures = {}
        self.class_definitions = {}
        self.variable_usage = defaultdict(list)
        
    def analyze_project(self, project_root: str = "."):
        """전체 프로젝트 분석"""
        print("🔍 코드 품질 분석 시작...")
        
        python_files = list(Path(project_root).rglob("*.py"))
        print(f"📁 발견된 Python 파일: {len(python_files)}개")
        
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue
                
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.warning(f"파일 분석 실패: {file_path}, 오류: {e}")
        
        self._detect_duplicates()
        self._detect_type_mismatches()
        self._detect_dead_code()
        self._analyze_namespace_consistency()
        self._generate_refactoring_plan()
        
    def _should_skip_file(self, file_path: Path) -> bool:
        """분석에서 제외할 파일 판단"""
        skip_patterns = [
            "__pycache__",
            ".git",
            "venv",
            ".venv",
            "node_modules",
            ".pytest_cache",
            "build",
            "dist"
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _analyze_file(self, file_path: Path):
        """단일 파일 분석"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            analyzer = FileAnalyzer(file_path, tree, content)
            analyzer.analyze()
            
            # 결과 수집
            self.function_signatures[file_path] = analyzer.function_signatures
            self.class_definitions[file_path] = analyzer.class_definitions
            self.variable_usage[file_path] = analyzer.variable_usage
            
        except SyntaxError as e:
            logger.warning(f"구문 오류: {file_path}, 라인 {e.lineno}: {e.text}")
    
    def _detect_duplicates(self):
        """중복 정의 탐지"""
        print("🔍 중복 정의 탐지 중...")
        
        # 함수 중복 탐지
        all_functions = {}
        for file_path, functions in self.function_signatures.items():
            for func_name, func_info in functions.items():
                if func_name in all_functions:
                    self.duplicate_definitions.append({
                        'type': 'function',
                        'name': func_name,
                        'locations': [
                            {'file': str(all_functions[func_name]['file']), 'line': all_functions[func_name]['line']},
                            {'file': str(file_path), 'line': func_info['line']}
                        ]
                    })
                else:
                    all_functions[func_name] = {'file': file_path, 'line': func_info['line']}
        
        # 클래스 중복 탐지
        all_classes = {}
        for file_path, classes in self.class_definitions.items():
            for class_name, class_info in classes.items():
                if class_name in all_classes:
                    self.duplicate_definitions.append({
                        'type': 'class',
                        'name': class_name,
                        'locations': [
                            {'file': str(all_classes[class_name]['file']), 'line': all_classes[class_name]['line']},
                            {'file': str(file_path), 'line': class_info['line']}
                        ]
                    })
                else:
                    all_classes[class_name] = {'file': file_path, 'line': class_info['line']}
    
    def _detect_type_mismatches(self):
        """타입 불일치 탐지"""
        print("🔍 타입 불일치 탐지 중...")
        
        # 함수 시그니처 타입 불일치 탐지
        function_signatures = defaultdict(list)
        for file_path, functions in self.function_signatures.items():
            for func_name, func_info in functions.items():
                function_signatures[func_name].append({
                    'file': file_path,
                    'signature': func_info['signature'],
                    'line': func_info['line']
                })
        
        for func_name, signatures in function_signatures.items():
            if len(signatures) > 1:
                # 시그니처 비교
                unique_signatures = set(sig['signature'] for sig in signatures)
                if len(unique_signatures) > 1:
                    self.type_mismatches.append({
                        'type': 'function_signature',
                        'name': func_name,
                        'signatures': signatures
                    })
    
    def _detect_dead_code(self):
        """죽은 코드 탐지"""
        print("🔍 죽은 코드 탐지 중...")
        
        # 사용되지 않는 함수 탐지
        all_functions = set()
        used_functions = set()
        
        for file_path, functions in self.function_signatures.items():
            for func_name in functions.keys():
                all_functions.add(func_name)
        
        # 함수 사용 분석
        for file_path, usage in self.variable_usage.items():
            for var_name in usage:
                if var_name in all_functions:
                    used_functions.add(var_name)
        
        # 사용되지 않는 함수 찾기
        unused_functions = all_functions - used_functions
        for func_name in unused_functions:
            for file_path, functions in self.function_signatures.items():
                if func_name in functions:
                    self.dead_code.append({
                        'type': 'unused_function',
                        'name': func_name,
                        'file': str(file_path),
                        'line': functions[func_name]['line']
                    })
    
    def _analyze_namespace_consistency(self):
        """네임스페이스 일관성 분석"""
        print("🔍 네임스페이스 일관성 분석 중...")
        
        # 파일별 네임스페이스 패턴 분석
        namespace_patterns = {}
        
        for file_path in self.function_signatures.keys():
            module_name = file_path.stem
            namespace_patterns[file_path] = {
                'module': module_name,
                'functions': list(self.function_signatures[file_path].keys()),
                'classes': list(self.class_definitions.get(file_path, {}).keys())
            }
        
        # 네임스페이스 일관성 검사
        for file_path, patterns in namespace_patterns.items():
            module_name = patterns['module']
            
            # 함수명이 모듈명과 일치하지 않는 경우
            for func_name in patterns['functions']:
                if not func_name.startswith(module_name.lower()) and not func_name.startswith('_'):
                    self.namespace_inconsistencies.append({
                        'type': 'function_naming',
                        'file': str(file_path),
                        'function': func_name,
                        'module': module_name,
                        'suggestion': f"{module_name.lower()}_{func_name}"
                    })
    
    def _generate_refactoring_plan(self):
        """리팩터링 계획 생성"""
        print("📋 리팩터링 계획 생성 중...")
        
        # WindowsPath를 문자열로 변환
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {k: convert_paths(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(item) for item in obj]
            elif hasattr(obj, '__str__') and 'WindowsPath' in str(type(obj)):
                return str(obj)
            else:
                return obj
        
        refactoring_plan = {
            'duplicate_definitions': convert_paths(self.duplicate_definitions),
            'type_mismatches': convert_paths(self.type_mismatches),
            'dead_code': convert_paths(self.dead_code),
            'namespace_inconsistencies': convert_paths(self.namespace_inconsistencies),
            'recommendations': []
        }
        
        # 리팩터링 권장사항 생성
        if self.duplicate_definitions:
            refactoring_plan['recommendations'].append({
                'type': 'consolidate_duplicates',
                'description': '중복 정의된 함수/클래스를 통합하거나 이름을 변경하세요.',
                'count': len(self.duplicate_definitions)
            })
        
        if self.type_mismatches:
            refactoring_plan['recommendations'].append({
                'type': 'fix_type_mismatches',
                'description': '함수 시그니처 타입 불일치를 수정하세요.',
                'count': len(self.type_mismatches)
            })
        
        if self.dead_code:
            refactoring_plan['recommendations'].append({
                'type': 'remove_dead_code',
                'description': '사용되지 않는 함수를 제거하거나 문서화하세요.',
                'count': len(self.dead_code)
            })
        
        if self.namespace_inconsistencies:
            refactoring_plan['recommendations'].append({
                'type': 'standardize_namespaces',
                'description': '함수명을 모듈 네임스페이스에 맞게 표준화하세요.',
                'count': len(self.namespace_inconsistencies)
            })
        
        # 결과 저장
        with open('code_quality_report.json', 'w', encoding='utf-8') as f:
            json.dump(refactoring_plan, f, indent=2, ensure_ascii=False)
        
        self._print_summary(refactoring_plan)
    
    def _print_summary(self, plan: Dict):
        """분석 결과 요약 출력"""
        print("\n" + "="*60)
        print("📊 코드 품질 분석 결과")
        print("="*60)
        
        print(f"🔍 중복 정의: {len(plan['duplicate_definitions'])}개")
        for dup in plan['duplicate_definitions'][:5]:  # 상위 5개만 표시
            print(f"   - {dup['type']}: {dup['name']}")
        
        print(f"🔍 타입 불일치: {len(plan['type_mismatches'])}개")
        for mismatch in plan['type_mismatches'][:5]:
            print(f"   - 함수: {mismatch['name']}")
        
        print(f"🔍 죽은 코드: {len(plan['dead_code'])}개")
        for dead in plan['dead_code'][:5]:
            print(f"   - {dead['type']}: {dead['name']} ({dead['file']})")
        
        print(f"🔍 네임스페이스 불일치: {len(plan['namespace_inconsistencies'])}개")
        for ns in plan['namespace_inconsistencies'][:5]:
            print(f"   - {ns['function']} → {ns['suggestion']}")
        
        print(f"\n📋 상세 보고서: code_quality_report.json")
        print("="*60)

class FileAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path: Path, tree: ast.AST, content: str):
        self.file_path = file_path
        self.tree = tree
        self.content = content
        self.function_signatures = {}
        self.class_definitions = {}
        self.variable_usage = []
        
    def analyze(self):
        """파일 분석 실행"""
        self.visit(self.tree)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """함수 정의 방문"""
        # 함수 시그니처 생성
        args = []
        for arg in node.args.args:
            if arg.annotation:
                args.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
            else:
                args.append(arg.arg)
        
        signature = f"({', '.join(args)})"
        
        self.function_signatures[node.name] = {
            'signature': signature,
            'line': node.lineno,
            'args': [arg.arg for arg in node.args.args]
        }
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """클래스 정의 방문"""
        self.class_definitions[node.name] = {
            'line': node.lineno,
            'bases': [ast.unparse(base) for base in node.bases]
        }
        
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """변수명 방문"""
        if isinstance(node.ctx, ast.Load):  # 읽기 전용 사용
            self.variable_usage.append(node.id)
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        """속성 접근 방문"""
        if isinstance(node.ctx, ast.Load):
            # 전체 경로 생성 (예: module.function)
            path = self._get_attribute_path(node)
            if path:
                self.variable_usage.append(path)
        
        self.generic_visit(node)
    
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

def main():
    """메인 실행 함수"""
    analyzer = CodeQualityAnalyzer()
    analyzer.analyze_project()
    
    print("\n🎉 코드 품질 분석 완료!")
    print("📋 리팩터링 계획을 확인하세요: code_quality_report.json")

if __name__ == "__main__":
    main() 