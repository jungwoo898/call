#!/usr/bin/env python3
"""
Python 3.8 오디오 서비스들만 호환성 검증 스크립트
audio-processor, speaker-diarizer, speech-recognizer 서비스만 검사
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

class Python38AudioCompatibilityChecker:
    """Python 3.8 오디오 서비스 호환성 검사기"""
    
    def __init__(self):
        self.issues = []
        self.python38_incompatible_patterns = [
            # Python 3.10+ 패턴 매칭
            "match",
            "case",
            # Python 3.9+ union types
            "str | None",
            "int | float",
            "List | Dict",
            # Python 3.10+ parenthesized context managers
            "with (",
        ]
    
    def check_file(self, file_path: str) -> List[Dict[str, Any]]:
        """파일의 Python 3.8 호환성 검사"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # AST 파싱으로 문법 검사
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                issues.append({
                    'type': 'syntax_error',
                    'line': e.lineno,
                    'message': f"Syntax error: {e.msg}",
                    'severity': 'error'
                })
                return issues
            
            # 패턴 매칭 검사
            for i, line in enumerate(content.split('\n'), 1):
                for pattern in self.python38_incompatible_patterns:
                    if pattern in line:
                        issues.append({
                            'type': 'incompatible_pattern',
                            'line': i,
                            'pattern': pattern,
                            'message': f"Python 3.8 호환되지 않는 패턴: {pattern}",
                            'severity': 'warning'
                        })
            
            # AST 노드 검사
            for node in ast.walk(tree):
                if isinstance(node, ast.Match):
                    issues.append({
                        'type': 'match_statement',
                        'line': node.lineno,
                        'message': "Python 3.8에서는 match 문이 지원되지 않습니다",
                        'severity': 'error'
                    })
                
                # Union type annotations 검사
                if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                    if hasattr(node, 'lineno'):
                        issues.append({
                            'type': 'union_type',
                            'line': node.lineno,
                            'message': "Python 3.8에서는 | 연산자를 타입 어노테이션에 사용할 수 없습니다. Optional 또는 Union을 사용하세요",
                            'severity': 'error'
                        })
        
        except Exception as e:
            issues.append({
                'type': 'file_error',
                'line': 0,
                'message': f"파일 읽기 오류: {str(e)}",
                'severity': 'error'
            })
        
        return issues
    
    def check_audio_services(self) -> Dict[str, Any]:
        """오디오 서비스들만 검사"""
        results = {
            'total_files': 0,
            'files_with_issues': 0,
            'total_issues': 0,
            'errors': 0,
            'warnings': 0,
            'file_issues': {}
        }
        
        # Python 3.8 오디오 서비스들만 검사
        audio_directories = [
            'src/audio'  # audio-processor, speaker-diarizer, speech-recognizer가 사용하는 공통 모듈
        ]
        
        for directory in audio_directories:
            if os.path.exists(directory):
                print(f"🔍 {directory} 검사 중...")
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            results['total_files'] += 1
                            
                            issues = self.check_file(file_path)
                            if issues:
                                results['files_with_issues'] += 1
                                results['file_issues'][file_path] = issues
                                
                                for issue in issues:
                                    results['total_issues'] += 1
                                    if issue['severity'] == 'error':
                                        results['errors'] += 1
                                    else:
                                        results['warnings'] += 1
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """검사 결과 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("Python 3.8 오디오 서비스 호환성 검사 결과")
        report.append("=" * 60)
        report.append(f"총 파일 수: {results['total_files']}")
        report.append(f"문제가 있는 파일 수: {results['files_with_issues']}")
        report.append(f"총 문제 수: {results['total_issues']}")
        report.append(f"오류: {results['errors']}")
        report.append(f"경고: {results['warnings']}")
        report.append("")
        
        if results['file_issues']:
            report.append("문제가 있는 파일들:")
            report.append("-" * 40)
            
            for file_path, issues in results['file_issues'].items():
                report.append(f"\n📁 {file_path}")
                for issue in issues:
                    severity_icon = "❌" if issue['severity'] == 'error' else "⚠️"
                    report.append(f"  {severity_icon} 라인 {issue['line']}: {issue['message']}")
        else:
            report.append("✅ 모든 오디오 서비스 파일이 Python 3.8과 호환됩니다!")
        
        return "\n".join(report)

def main():
    """메인 함수"""
    print("🔍 Python 3.8 오디오 서비스 호환성 검사 시작...")
    print("🎵 audio-processor, speaker-diarizer, speech-recognizer 서비스만 검사")
    
    checker = Python38AudioCompatibilityChecker()
    results = checker.check_audio_services()
    
    # 리포트 생성
    report = checker.generate_report(results)
    print("\n" + report)
    
    # 결과 저장
    with open('python38_audio_compatibility_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 상세 리포트가 python38_audio_compatibility_report.txt에 저장되었습니다.")
    
    # 종료 코드
    if results['errors'] > 0:
        print("❌ Python 3.8 오디오 서비스 호환성 오류가 발견되었습니다.")
        sys.exit(1)
    else:
        print("✅ Python 3.8 오디오 서비스 호환성 검사 완료!")

if __name__ == "__main__":
    main() 