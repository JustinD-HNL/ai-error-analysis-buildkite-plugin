#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Health Check
Performs comprehensive health checks for the plugin system
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import tempfile


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: str  # "pass", "fail", "warn"
    message: str
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None


@dataclass
class HealthReport:
    """Complete health check report"""
    overall_status: str
    timestamp: str
    checks: List[HealthCheckResult]
    summary: Dict[str, int]
    recommendations: List[str]


class HealthChecker:
    """Performs health checks for the AI Error Analysis plugin"""
    
    def __init__(self):
        self.plugin_dir = Path(os.environ.get('AI_ERROR_ANALYSIS_PLUGIN_DIR', '.'))
        self.checks = []
        
    def run_all_checks(self) -> HealthReport:
        """Run all health checks and return comprehensive report"""
        self.checks = []
        
        # Core system checks
        self._check_python_version()
        self._check_required_commands()
        self._check_plugin_files()
        self._check_permissions()
        
        # Configuration checks
        self._check_environment_variables()
        self._check_ai_provider_config()
        self._check_cache_configuration()
        
        # Network and API checks (if not in dry run mode)
        if not self._is_dry_run():
            self._check_api_connectivity()
        
        # Performance checks
        self._check_disk_space()
        self._check_memory_usage()
        
        # Generate report
        return self._generate_report()
    
    def _check_python_version(self):
        """Check Python version compatibility"""
        start_time = self._get_time_ms()
        
        try:
            import sys
            version = sys.version_info
            
            if version >= (3, 7):
                status = "pass"
                message = f"Python {version.major}.{version.minor}.{version.micro} is supported"
                details = {
                    "version": f"{version.major}.{version.minor}.{version.micro}",
                    "executable": sys.executable,
                    "platform": sys.platform
                }
            else:
                status = "fail"
                message = f"Python {version.major}.{version.minor} is too old. Minimum required: 3.7"
                details = {"version": f"{version.major}.{version.minor}.{version.micro}"}
                
        except Exception as e:
            status = "fail"
            message = f"Failed to check Python version: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("python_version", status, message, details, duration))
    
    def _check_required_commands(self):
        """Check availability of required external commands"""
        start_time = self._get_time_ms()
        
        required_commands = ["curl", "jq", "git"]
        missing_commands = []
        available_commands = []
        
        for cmd in required_commands:
            try:
                result = subprocess.run([cmd, "--version"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    available_commands.append(cmd)
                else:
                    missing_commands.append(cmd)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing_commands.append(cmd)
        
        if missing_commands:
            status = "fail"
            message = f"Missing required commands: {', '.join(missing_commands)}"
        else:
            status = "pass"
            message = "All required commands are available"
        
        details = {
            "available": available_commands,
            "missing": missing_commands,
            "required": required_commands
        }
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("required_commands", status, message, details, duration))
    
    def _check_plugin_files(self):
        """Check plugin file structure and integrity"""
        start_time = self._get_time_ms()
        
        required_files = [
            "plugin.yml",
            "hooks/environment",
            "hooks/post-command", 
            "hooks/pre-exit",
            "lib/error_detector.py",
            "lib/ai_providers.py",
            "lib/context_builder.py",
            "lib/log_sanitizer.py",
            "lib/report_generator.py"
        ]
        
        missing_files = []
        invalid_files = []
        valid_files = []
        
        for file_path in required_files:
            full_path = self.plugin_dir / file_path
            
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                invalid_files.append(f"{file_path} (not a file)")
            elif file_path.endswith('.py'):
                # Basic Python syntax check
                try:
                    with open(full_path, 'r') as f:
                        compile(f.read(), full_path, 'exec')
                    valid_files.append(file_path)
                except SyntaxError as e:
                    invalid_files.append(f"{file_path} (syntax error: {e})")
            else:
                valid_files.append(file_path)
        
        if missing_files or invalid_files:
            status = "fail"
            issues = []
            if missing_files:
                issues.append(f"missing: {', '.join(missing_files)}")
            if invalid_files:
                issues.append(f"invalid: {', '.join(invalid_files)}")
            message = f"Plugin file issues - {'; '.join(issues)}"
        else:
            status = "pass"
            message = f"All {len(required_files)} required files are present and valid"
        
        details = {
            "required": required_files,
            "valid": valid_files,
            "missing": missing_files,
            "invalid": invalid_files
        }
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("plugin_files", status, message, details, duration))
    
    def _check_permissions(self):
        """Check file permissions for plugin files"""
        start_time = self._get_time_ms()
        
        executable_files = [
            "hooks/environment",
            "hooks/post-command",
            "hooks/pre-exit"
        ]
        
        permission_issues = []
        valid_permissions = []
        
        for file_path in executable_files:
            full_path = self.plugin_dir / file_path
            
            if full_path.exists():
                if os.access(full_path, os.X_OK):
                    valid_permissions.append(file_path)
                else:
                    permission_issues.append(f"{file_path} (not executable)")
        
        if permission_issues:
            status = "fail"
            message = f"Permission issues: {', '.join(permission_issues)}"
        else:
            status = "pass"
            message = "All hook files have correct permissions"
        
        details = {
            "executable_files": executable_files,
            "valid_permissions": valid_permissions,
            "permission_issues": permission_issues
        }
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("file_permissions", status, message, details, duration))
    
    def _check_environment_variables(self):
        """Check required environment variables"""
        start_time = self._get_time_ms()
        
        buildkite_vars = [
            "BUILDKITE_ORGANIZATION_SLUG",
            "BUILDKITE_PIPELINE_SLUG", 
            "BUILDKITE_BUILD_ID",
            "BUILDKITE_JOB_ID"
        ]
        
        missing_vars = []
        present_vars = []
        
        for var in buildkite_vars:
            if os.environ.get(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        if missing_vars:
            status = "warn"
            message = f"Some Buildkite environment variables are missing: {', '.join(missing_vars)}"
        else:
            status = "pass"
            message = "All required Buildkite environment variables are present"
        
        details = {
            "required": buildkite_vars,
            "present": present_vars,
            "missing": missing_vars
        }
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("environment_variables", status, message, details, duration))
    
    def _check_ai_provider_config(self):
        """Check AI provider configuration"""
        start_time = self._get_time_ms()
        
        try:
            # Load AI provider configuration
            providers_config_str = os.environ.get(
                'BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_AI_PROVIDERS',
                '[{"name":"openai","model":"gpt-4o-mini"}]'
            )
            providers_config = json.loads(providers_config_str)
            
            if not isinstance(providers_config, list):
                providers_config = [providers_config]
            
            configured_providers = []
            missing_api_keys = []
            
            for provider in providers_config:
                provider_name = provider.get('name', 'unknown')
                configured_providers.append(provider_name)
                
                # Check API key
                api_key_env = provider.get('api_key_env', f'{provider_name.upper()}_API_KEY')
                if not os.environ.get(api_key_env):
                    missing_api_keys.append(f"{provider_name}: {api_key_env}")
            
            if missing_api_keys and not self._is_dry_run():
                status = "fail"
                message = f"Missing API keys: {', '.join(missing_api_keys)}"
            elif configured_providers:
                status = "pass"
                message = f"AI providers configured: {', '.join(configured_providers)}"
            else:
                status = "fail"
                message = "No AI providers configured"
            
            details = {
                "configured_providers": configured_providers,
                "missing_api_keys": missing_api_keys,
                "dry_run": self._is_dry_run()
            }
            
        except json.JSONDecodeError as e:
            status = "fail"
            message = f"Invalid AI provider configuration JSON: {str(e)}"
            details = {"error": str(e)}
        except Exception as e:
            status = "fail"
            message = f"Error checking AI provider config: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("ai_provider_config", status, message, details, duration))
    
    def _check_cache_configuration(self):
        """Check cache configuration and accessibility"""
        start_time = self._get_time_ms()
        
        try:
            cache_enabled = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_ENABLED', 'true').lower() == 'true'
            cache_dir = os.environ.get('AI_ERROR_ANALYSIS_CACHE_DIR', '/tmp/ai-error-analysis-cache')
            
            if not cache_enabled:
                status = "pass"
                message = "Caching is disabled"
                details = {"cache_enabled": False}
            else:
                cache_path = Path(cache_dir)
                
                # Test cache directory creation and access
                cache_path.mkdir(parents=True, exist_ok=True)
                
                # Test write permissions
                test_file = cache_path / 'health_check_test'
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    test_file.unlink()
                    
                    status = "pass"
                    message = f"Cache directory is accessible: {cache_dir}"
                    
                except PermissionError:
                    status = "fail"
                    message = f"No write permission to cache directory: {cache_dir}"
                
                details = {
                    "cache_enabled": True,
                    "cache_directory": cache_dir,
                    "directory_exists": cache_path.exists(),
                    "writable": status == "pass"
                }
                
        except Exception as e:
            status = "fail"
            message = f"Error checking cache configuration: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("cache_configuration", status, message, details, duration))
    
    def _check_api_connectivity(self):
        """Check API connectivity for configured providers"""
        start_time = self._get_time_ms()
        
        try:
            # Simple connectivity test (not a full API call)
            test_urls = {
                "openai": "https://api.openai.com",
                "claude": "https://api.anthropic.com", 
                "gemini": "https://generativelanguage.googleapis.com"
            }
            
            connectivity_results = {}
            
            for provider, url in test_urls.items():
                try:
                    request = urllib.request.Request(url, method='HEAD')
                    with urllib.request.urlopen(request, timeout=5) as response:
                        connectivity_results[provider] = "reachable"
                except urllib.error.HTTPError as e:
                    # HTTP errors (like 401) still mean the service is reachable
                    connectivity_results[provider] = "reachable"
                except (urllib.error.URLError, OSError) as e:
                    connectivity_results[provider] = f"unreachable: {str(e)}"
            
            reachable_count = sum(1 for result in connectivity_results.values() if result == "reachable")
            
            if reachable_count == len(test_urls):
                status = "pass"
                message = "All AI provider APIs are reachable"
            elif reachable_count > 0:
                status = "warn"
                message = f"{reachable_count}/{len(test_urls)} AI provider APIs are reachable"
            else:
                status = "fail"
                message = "No AI provider APIs are reachable"
            
            details = {
                "connectivity_results": connectivity_results,
                "reachable_count": reachable_count,
                "total_providers": len(test_urls)
            }
            
        except Exception as e:
            status = "warn"
            message = f"Could not test API connectivity: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("api_connectivity", status, message, details, duration))
    
    def _check_disk_space(self):
        """Check available disk space"""
        start_time = self._get_time_ms()
        
        try:
            # Check disk space in build directory
            build_path = os.environ.get('BUILDKITE_BUILD_PATH', '.')
            
            # Use df command to get disk space
            result = subprocess.run(['df', '-h', build_path], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # Parse df output
                    parts = lines[1].split()
                    if len(parts) >= 4:
                        available = parts[3]
                        used_percent = parts[4].rstrip('%')
                        
                        try:
                            used_pct = int(used_percent)
                            if used_pct >= 95:
                                status = "fail"
                                message = f"Disk space critically low: {used_percent}% used, {available} available"
                            elif used_pct >= 90:
                                status = "warn"
                                message = f"Disk space low: {used_percent}% used, {available} available"
                            else:
                                status = "pass"
                                message = f"Disk space OK: {used_percent}% used, {available} available"
                            
                            details = {
                                "used_percent": used_pct,
                                "available": available,
                                "path": build_path
                            }
                        except ValueError:
                            status = "warn"
                            message = "Could not parse disk usage percentage"
                            details = {"df_output": result.stdout}
                    else:
                        status = "warn"
                        message = "Unexpected df output format"
                        details = {"df_output": result.stdout}
                else:
                    status = "warn"
                    message = "No disk usage data returned"
                    details = {"df_output": result.stdout}
            else:
                status = "warn"
                message = "Failed to check disk space with df command"
                details = {"error": result.stderr}
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            status = "warn"
            message = f"Could not check disk space: {str(e)}"
            details = {"error": str(e)}
        except Exception as e:
            status = "warn"
            message = f"Error checking disk space: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("disk_space", status, message, details, duration))
    
    def _check_memory_usage(self):
        """Check memory usage"""
        start_time = self._get_time_ms()
        
        try:
            # Use free command to check memory
            result = subprocess.run(['free', '-h'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    # Parse memory info
                    mem_line = lines[1]  # Mem: line
                    parts = mem_line.split()
                    
                    if len(parts) >= 3:
                        total = parts[1]
                        used = parts[2]
                        
                        status = "pass"
                        message = f"Memory usage: {used} used of {total} total"
                        details = {
                            "total": total,
                            "used": used,
                            "free_output": result.stdout
                        }
                    else:
                        status = "warn"
                        message = "Could not parse memory usage"
                        details = {"free_output": result.stdout}
                else:
                    status = "warn"
                    message = "Unexpected free command output"
                    details = {"free_output": result.stdout}
            else:
                status = "warn"
                message = "Failed to check memory usage"
                details = {"error": result.stderr}
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            status = "warn"
            message = "free command not available"
            details = {"error": "free command not found"}
        except Exception as e:
            status = "warn"
            message = f"Error checking memory usage: {str(e)}"
            details = {"error": str(e)}
        
        duration = self._get_time_ms() - start_time
        self.checks.append(HealthCheckResult("memory_usage", status, message, details, duration))
    
    def _generate_report(self) -> HealthReport:
        """Generate comprehensive health report"""
        
        # Count check results
        summary = {"pass": 0, "warn": 0, "fail": 0}
        for check in self.checks:
            summary[check.status] += 1
        
        # Determine overall status
        if summary["fail"] > 0:
            overall_status = "fail"
        elif summary["warn"] > 0:
            overall_status = "warn"
        else:
            overall_status = "pass"
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return HealthReport(
            overall_status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            checks=self.checks,
            summary=summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for check in self.checks:
            if check.status == "fail":
                if check.name == "python_version":
                    recommendations.append("Upgrade Python to version 3.7 or later")
                elif check.name == "required_commands":
                    recommendations.append("Install missing system commands: " + 
                                         ", ".join(check.details.get("missing", [])))
                elif check.name == "plugin_files":
                    recommendations.append("Reinstall or repair the plugin files")
                elif check.name == "file_permissions":
                    recommendations.append("Fix file permissions with: chmod +x hooks/*")
                elif check.name == "ai_provider_config":
                    recommendations.append("Configure AI provider API keys in environment variables")
                elif check.name == "cache_configuration":
                    recommendations.append("Fix cache directory permissions or change cache location")
                elif check.name == "disk_space":
                    recommendations.append("Free up disk space or move to a location with more space")
            
            elif check.status == "warn":
                if check.name == "environment_variables":
                    recommendations.append("Ensure all Buildkite environment variables are properly set")
                elif check.name == "api_connectivity":
                    recommendations.append("Check network connectivity and firewall settings")
                elif check.name == "disk_space":
                    recommendations.append("Monitor disk space usage and clean up if necessary")
        
        # Add general recommendations
        if any(c.status == "fail" for c in self.checks):
            recommendations.append("Review the failed checks above and address critical issues")
        
        return recommendations
    
    def _is_dry_run(self) -> bool:
        """Check if running in dry run mode"""
        return os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN', 'false').lower() == 'true'
    
    def _get_time_ms(self) -> int:
        """Get current time in milliseconds"""
        return int(datetime.now().timestamp() * 1000)


def main():
    """Main entry point for health check"""
    try:
        checker = HealthChecker()
        report = checker.run_all_checks()
        
        # Output report as JSON
        print(json.dumps(asdict(report), indent=2, default=str))
        
        # Exit with appropriate code
        if report.overall_status == "fail":
            sys.exit(1)
        elif report.overall_status == "warn":
            sys.exit(2)  # Warning exit code
        else:
            sys.exit(0)
            
    except Exception as e:
        error_report = {
            "overall_status": "fail",
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Health check failed: {str(e)}",
            "checks": [],
            "summary": {"pass": 0, "warn": 0, "fail": 1},
            "recommendations": ["Fix health check system error", "Contact system administrator"]
        }
        
        print(json.dumps(error_report, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()