#!/usr/bin/env python3
"""
네임스페이스 상태 분석 스크립트
현재 함수명들의 네임스페이스 상태를 정확히 파악
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple

class NamespaceAnalyzer:
    def __init__(self):
        self.function_stats = {}
        self.namespace_issues = []
        
    def analyze_project(self, project_root: str = "src"):
        print("🔍 네임스페이스 상태 분석 시작...")
        self._analyze_all_modules(project_root)
        self._print_analysis_results()
    
    def _analyze_all_modules(self, project_root: str):
        print("📋 모든 모듈 분석 중...")
        for py_file in Path(project_root).rglob("*.py"):
            if py_file.name.endswith('.backup'):
                continue
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
                if node.name not in ["__init__", "main", "health_check", "get_metrics", "lifespan"]:
                    functions.append(node.name)
        
        if functions:
            self.function_stats[file_path] = functions
    
    def _print_analysis_results(self):
        print("\n" + "="*60)
        print("📊 네임스페이스 분석 결과")
        print("="*60)
        
        # 모듈별 함수 통계
        module_stats = {}
        total_functions = 0
        
        for file_path, functions in self.function_stats.items():
            norm_path = file_path.replace('\\', '/').lower()
            
            # 모듈 타입 결정
            if '/audio/' in norm_path:
                module_type = 'audio'
                expected_prefix = 'audio_'
            elif '/text/' in norm_path:
                module_type = 'text'
                expected_prefix = 'text_'
            elif '/db/' in norm_path:
                module_type = 'db'
                expected_prefix = 'db_'
            elif '/utils/' in norm_path:
                module_type = 'utils'
                expected_prefix = 'util_'
            elif '/gateway/' in norm_path:
                module_type = 'gateway'
                expected_prefix = 'gateway_'
            elif '/auth/' in norm_path:
                module_type = 'auth'
                expected_prefix = 'auth_'
            elif '/upload/' in norm_path:
                module_type = 'upload'
                expected_prefix = 'upload_'
            else:
                module_type = 'other'
                expected_prefix = ''
            
            if module_type not in module_stats:
                module_stats[module_type] = {'total': 0, 'correct': 0, 'incorrect': 0, 'functions': []}
            
            module_stats[module_type]['total'] += len(functions)
            total_functions += len(functions)
            
            for func_name in functions:
                module_stats[module_type]['functions'].append(func_name)
                
                if expected_prefix:
                    if func_name.startswith(expected_prefix):
                        module_stats[module_type]['correct'] += 1
                    else:
                        module_stats[module_type]['incorrect'] += 1
                        self.namespace_issues.append({
                            'file': file_path,
                            'function': func_name,
                            'module': module_type,
                            'expected_prefix': expected_prefix,
                            'suggested_name': f"{expected_prefix}{func_name}"
                        })
                else:
                    module_stats[module_type]['correct'] += 1
        
        # 결과 출력
        for module_type, stats in module_stats.items():
            if stats['total'] > 0:
                correct_rate = (stats['correct'] / stats['total']) * 100
                print(f"\n📁 {module_type.upper()} 모듈:")
                print(f"   총 함수: {stats['total']}개")
                print(f"   올바른 네임스페이스: {stats['correct']}개 ({correct_rate:.1f}%)")
                print(f"   잘못된 네임스페이스: {stats['incorrect']}개")
                
                if stats['incorrect'] > 0:
                    print("   잘못된 함수들:")
                    for func in stats['functions']:
                        if module_type in ['audio', 'text', 'db', 'utils', 'gateway', 'auth', 'upload']:
                            expected_prefix = f"{module_type}_"
                            if not func.startswith(expected_prefix):
                                print(f"     - {func} → {expected_prefix}{func}")
        
        # 전체 통계
        total_correct = sum(stats['correct'] for stats in module_stats.values())
        total_incorrect = sum(stats['incorrect'] for stats in module_stats.values())
        
        print(f"\n" + "="*60)
        print(f"📊 전체 통계:")
        print(f"   총 함수: {total_functions}개")
        print(f"   올바른 네임스페이스: {total_correct}개")
        print(f"   잘못된 네임스페이스: {total_incorrect}개")
        print(f"   정확도: {(total_correct/total_functions)*100:.1f}%" if total_functions > 0 else "   정확도: 0%")
        
        if self.namespace_issues:
            print(f"\n🔧 수정이 필요한 함수들 (상위 10개):")
            for i, issue in enumerate(self.namespace_issues[:10]):
                print(f"   {i+1}. {issue['file']}: {issue['function']} → {issue['suggested_name']}")

def main():
    analyzer = NamespaceAnalyzer()
    analyzer.analyze_project()
    print("\n🎉 네임스페이스 분석 완료!")

if __name__ == "__main__":
    main() 