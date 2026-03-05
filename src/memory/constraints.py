"""
约束规则 - 安全与行为检查
"""

import re
import logging
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheck:
    """安全检查项"""
    passed: bool
    level: str      # info, warning, danger
    message: str
    details: List[str] = None


class ConstraintChecker:
    """
    约束检查器
    
    检查输入和输出是否符合安全与行为规则
    """
    
    # 敏感信息模式
    SENSITIVE_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API Key"),
        (r'ghp_[a-zA-Z0-9]{36,}', "GitHub Personal Token"),
        (r'AK[0-9A-Z]{16,}', "阿里云 AccessKey"),
        (r'password\s*[=:]\s*\S+', "密码"),
        (r'secret\s*[=:]\s*\S+', "密钥"),
        (r'token\s*[=:]\s*\S+', "Token"),
        (r'private_key', "私钥"),
    ]
    
    # 危险命令模式
    DANGEROUS_COMMANDS = [
        (r'rm\s+-rf\s+/', "删除系统文件"),
        (r'dd\s+if=.*of=/dev/', "直接写入设备"),
        (r'mkfs', "格式化文件系统"),
        (r':\(\)\{.*\|.*\}&', "Fork 炸弹"),
        (r'chmod\s+-R\s+777\s*/', "危险权限修改"),
    ]
    
    def __init__(self):
        self.violations: List[str] = []
    
    def check_sensitive_info(self, text: str) -> SafetyCheck:
        """检查是否包含敏感信息"""
        found = []
        
        for pattern, name in self.SENSITIVE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found.append(f"发现 {name}: {match.group()[:20]}...")
        
        if found:
            return SafetyCheck(
                passed=False,
                level="danger",
                message="⚠️  检测到敏感信息",
                details=found
            )
        
        return SafetyCheck(
            passed=True,
            level="info",
            message="✅ 无敏感信息"
        )
    
    def check_dangerous_command(self, text: str) -> SafetyCheck:
        """检查是否包含危险命令"""
        found = []
        
        for pattern, desc in self.DANGEROUS_COMMANDS:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(f"危险操作: {desc}")
        
        if found:
            return SafetyCheck(
                passed=False,
                level="danger",
                message="🚫 检测到危险命令",
                details=found
            )
        
        return SafetyCheck(
            passed=True,
            level="info",
            message="✅ 无危险命令"
        )
    
    def check_output_completeness(self, output: str, expected_type: str) -> SafetyCheck:
        """检查输出完整性"""
        issues = []
        
        # 检查代码是否完整
        if expected_type == "code":
            # 检查括号匹配
            brackets = {'(': ')', '[': ']', '{': '}'}
            stack = []
            for char in output:
                if char in brackets:
                    stack.append(char)
                elif char in brackets.values():
                    if not stack:
                        issues.append("括号不匹配")
                        break
                    if brackets[stack.pop()] != char:
                        issues.append("括号不匹配")
                        break
            
            # 检查是否有未完成的 TODO
            if "TODO" in output or "FIXME" in output:
                issues.append("包含未完成的 TODO/FIXME")
        
        if issues:
            return SafetyCheck(
                passed=False,
                level="warning",
                message="⚠️  输出可能不完整",
                details=issues
            )
        
        return SafetyCheck(
            passed=True,
            level="info",
            message="✅ 输出完整"
        )
    
    def validate(self, content: str, content_type: str = "text") -> Tuple[bool, List[SafetyCheck]]:
        """
        执行完整验证
        
        Args:
            content: 待检查内容
            content_type: 内容类型 (text, code, command)
        
        Returns:
            (是否通过, 检查项列表)
        """
        checks = []
        
        # 检查敏感信息
        checks.append(self.check_sensitive_info(content))
        
        # 检查危险命令
        if content_type in ["code", "command"]:
            checks.append(self.check_dangerous_command(content))
        
        # 检查完整性
        checks.append(self.check_output_completeness(content, content_type))
        
        # 判断整体是否通过
        passed = all(c.passed for c in checks)
        
        if not passed:
            self.violations.extend([
                c.message for c in checks if not c.passed
            ])
        
        return passed, checks
    
    def get_violations(self) -> List[str]:
        """获取所有违规记录"""
        return self.violations.copy()
    
    def clear_violations(self):
        """清空违规记录"""
        self.violations.clear()


class BehaviorGuidelines:
    """
    行为准则
    
    定义助手的行为规范
    """
    
    RULES = {
        "honesty": {
            "description": "保持诚实",
            "rules": [
                "不知道就说不知道",
                "不确定时表达不确定性",
                "不编造事实或数据"
            ]
        },
        "conciseness": {
            "description": "保持简洁",
            "rules": [
                "默认简洁回答",
                "用户要求详细再展开",
                "避免冗余信息"
            ]
        },
        "politeness": {
            "description": "保持礼貌",
            "rules": [
                "尊重用户",
                "接受批评并改进",
                "不强行推销观点"
            ]
        },
        "safety": {
            "description": "保持安全",
            "rules": [
                "不执行危险操作",
                "敏感信息不外泄",
                "重要决策先确认"
            ]
        }
    }
    
    @classmethod
    def get_system_prompt(cls) -> str:
        """获取系统提示中的行为准则部分"""
        lines = ["\n### 行为准则"]
        
        for key, value in cls.RULES.items():
            lines.append(f"\n**{value['description']}**:")
            for rule in value['rules']:
                lines.append(f"  - {rule}")
        
        return "\n".join(lines)
    
    @classmethod
    def check_compliance(cls, response: str) -> Dict[str, Any]:
        """
        检查回复是否符合行为准则
        
        TODO: 实现更智能的检查
        """
        # 简单启发式检查
        issues = []
        
        # 检查是否过于冗长
        if len(response) > 2000 and "详细" not in response.lower():
            issues.append("回复可能过于冗长，建议询问用户是否需要详细说明")
        
        # 检查是否包含免责声明（不确定时应该有）
        uncertainty_words = ["可能", "或许", "不确定", "应该"]
        has_uncertainty = any(w in response for w in uncertainty_words)
        has_disclaimer = any(w in response for w in ["仅供参考", "建议确认"])
        
        if has_uncertainty and not has_disclaimer:
            issues.append("表达不确定性时建议添加免责声明")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues
        }