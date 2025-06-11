#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Report Generator
Generates formatted reports and annotations from AI analysis results
"""

import json
import os
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import html


@dataclass
class ReportSection:
    """A section within the analysis report"""
    title: str
    content: str
    priority: int
    section_type: str


class ReportGenerator:
    """Generates formatted reports from AI analysis results"""
    
    def __init__(self):
        self.confidence_thresholds = {
            "high": 80,
            "medium": 50,
            "low": 0
        }
        
        self.severity_colors = {
            "high": "#e74c3c",      # Red
            "medium": "#f39c12",    # Orange
            "low": "#3498db"        # Blue
        }
        
        self.confidence_colors = {
            "high": "#27ae60",      # Green
            "medium": "#f39c12",    # Orange  
            "low": "#e74c3c"        # Red
        }
    
    def generate_html_report(self, analysis_result: Dict[str, Any], 
                           context: Dict[str, Any], 
                           include_confidence: bool = True) -> str:
        """Generate HTML report for Buildkite annotation"""
        
        try:
            analysis = analysis_result.get("analysis", {})
            metadata = analysis_result.get("metadata", {})
            provider = analysis_result.get("provider", "unknown")
            model = analysis_result.get("model", "unknown")
            
            # Build report sections
            sections = []
            
            # Header section
            sections.append(self._create_header_section(analysis, metadata, provider, model))
            
            # Root cause section
            if analysis.get("root_cause"):
                sections.append(self._create_root_cause_section(analysis["root_cause"]))
            
            # Suggested fixes section
            if analysis.get("suggested_fixes"):
                sections.append(self._create_fixes_section(analysis["suggested_fixes"]))
            
            # Confidence and severity section
            if include_confidence:
                sections.append(self._create_confidence_section(analysis, metadata))
            
            # Error details section
            sections.append(self._create_error_details_section(context))
            
            # Build context section (collapsible)
            sections.append(self._create_build_context_section(context))
            
            # Combine sections into final HTML
            html_content = self._combine_sections(sections)
            
            return html_content
            
        except Exception as e:
            return self._create_error_report(f"Failed to generate report: {str(e)}")
    
    def generate_json_report(self, analysis_result: Dict[str, Any], 
                           context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON report"""
        
        try:
            analysis = analysis_result.get("analysis", {})
            metadata = analysis_result.get("metadata", {})
            
            report = {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "generator_version": "1.0.0",
                    "report_type": "ai_error_analysis"
                },
                "ai_analysis": {
                    "provider": analysis_result.get("provider", "unknown"),
                    "model": analysis_result.get("model", "unknown"),
                    "root_cause": analysis.get("root_cause", ""),
                    "suggested_fixes": analysis.get("suggested_fixes", []),
                    "confidence": analysis.get("confidence", 0),
                    "severity": analysis.get("severity", "unknown"),
                    "error_type": analysis.get("error_type", "unknown")
                },
                "build_context": {
                    "build_id": context.get("build_info", {}).get("build_id", "unknown"),
                    "pipeline": context.get("pipeline_info", {}).get("pipeline", "unknown"),
                    "branch": context.get("git_info", {}).get("branch", "unknown"),
                    "exit_code": context.get("error_info", {}).get("exit_code", 1),
                    "error_category": context.get("error_info", {}).get("error_category", "unknown")
                },
                "performance_metrics": {
                    "analysis_time": metadata.get("analysis_time", "unknown"),
                    "tokens_used": metadata.get("tokens_used", 0),
                    "cached": metadata.get("cached", False)
                },
                "recommendations": self._generate_recommendations(analysis, context),
                "next_steps": self._generate_next_steps(analysis, context)
            }
            
            return report
            
        except Exception as e:
            return {
                "error": f"Failed to generate JSON report: {str(e)}",
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "error": True
                }
            }
    
    def generate_markdown_report(self, analysis_result: Dict[str, Any], 
                               context: Dict[str, Any]) -> str:
        """Generate Markdown report"""
        
        try:
            analysis = analysis_result.get("analysis", {})
            metadata = analysis_result.get("metadata", {})
            provider = analysis_result.get("provider", "unknown")
            model = analysis_result.get("model", "unknown")
            
            md_lines = []
            
            # Header
            md_lines.extend([
                "# 🤖 AI Error Analysis Report",
                "",
                f"**Provider:** {provider} ({model})",
                f"**Analysis Time:** {metadata.get('analysis_time', 'unknown')}",
                f"**Confidence:** {analysis.get('confidence', 0)}%",
                f"**Severity:** {analysis.get('severity', 'unknown').title()}",
                ""
            ])
            
            # Root Cause
            if analysis.get("root_cause"):
                md_lines.extend([
                    "## 🔍 Root Cause Analysis",
                    "",
                    analysis["root_cause"],
                    ""
                ])
            
            # Suggested Fixes
            if analysis.get("suggested_fixes"):
                md_lines.extend([
                    "## 💡 Suggested Fixes",
                    ""
                ])
                
                for i, fix in enumerate(analysis["suggested_fixes"], 1):
                    md_lines.append(f"{i}. {fix}")
                
                md_lines.append("")
            
            # Error Details
            error_info = context.get("error_info", {})
            md_lines.extend([
                "## 📋 Error Details",
                "",
                f"- **Exit Code:** {error_info.get('exit_code', 'unknown')}",
                f"- **Command:** `{error_info.get('command', 'unknown')}`",
                f"- **Category:** {error_info.get('error_category', 'unknown')}",
                ""
            ])
            
            # Build Context
            build_info = context.get("build_info", {})
            git_info = context.get("git_info", {})
            
            md_lines.extend([
                "## 🏗️ Build Context",
                "",
                f"- **Pipeline:** {build_info.get('pipeline_name', 'unknown')}",
                f"- **Branch:** {git_info.get('branch', 'unknown')}",
                f"- **Commit:** {git_info.get('commit', 'unknown')[:8]}",
                f"- **Build:** #{build_info.get('build_number', 'unknown')}",
                ""
            ])
            
            # Performance Metrics
            md_lines.extend([
                "## 📊 Analysis Metrics",
                "",
                f"- **Tokens Used:** {metadata.get('tokens_used', 0)}",
                f"- **Cached Result:** {'Yes' if metadata.get('cached') else 'No'}",
                f"- **Analysis Duration:** {metadata.get('analysis_time', 'unknown')}",
                ""
            ])
            
            return "\n".join(md_lines)
            
        except Exception as e:
            return f"# Error\n\nFailed to generate Markdown report: {str(e)}"
    
    def _create_header_section(self, analysis: Dict[str, Any], metadata: Dict[str, Any], 
                             provider: str, model: str) -> ReportSection:
        """Create the header section of the report"""
        
        confidence = analysis.get("confidence", 0)
        severity = analysis.get("severity", "unknown")
        
        confidence_level = self._get_confidence_level(confidence)
        confidence_color = self.confidence_colors[confidence_level]
        severity_color = self.severity_colors.get(severity, "#95a5a6")
        
        header_html = f"""
        <div style="border-left: 4px solid {severity_color}; padding-left: 12px; margin-bottom: 16px;">
            <h3 style="margin: 0; color: #2c3e50;">🤖 AI Error Analysis</h3>
            <div style="margin-top: 8px; font-size: 14px; color: #7f8c8d;">
                <span style="background: #ecf0f1; padding: 2px 6px; border-radius: 3px; margin-right: 8px;">
                    {provider} • {model}
                </span>
                <span style="background: {confidence_color}; color: white; padding: 2px 6px; border-radius: 3px; margin-right: 8px;">
                    {confidence}% confidence
                </span>
                <span style="background: {severity_color}; color: white; padding: 2px 6px; border-radius: 3px;">
                    {severity.title()} severity
                </span>
            </div>
        </div>
        """
        
        return ReportSection("header", header_html, 1, "header")
    
    def _create_root_cause_section(self, root_cause: str) -> ReportSection:
        """Create the root cause analysis section"""
        
        # Escape HTML and format the root cause
        escaped_cause = html.escape(root_cause)
        formatted_cause = self._format_text_with_emphasis(escaped_cause)
        
        section_html = f"""
        <div style="margin-bottom: 16px;">
            <h4 style="margin: 0 0 8px 0; color: #c0392b;">🔍 Root Cause</h4>
            <div style="background: #fdf2f2; border: 1px solid #f5c6cb; border-radius: 4px; padding: 12px; color: #721c24;">
                {formatted_cause}
            </div>
        </div>
        """
        
        return ReportSection("root_cause", section_html, 2, "analysis")
    
    def _create_fixes_section(self, suggested_fixes: List[str]) -> ReportSection:
        """Create the suggested fixes section"""
        
        fixes_html = []
        for i, fix in enumerate(suggested_fixes[:5], 1):  # Limit to 5 fixes
            escaped_fix = html.escape(fix)
            formatted_fix = self._format_text_with_emphasis(escaped_fix)
            
            fixes_html.append(f"""
                <div style="display: flex; margin-bottom: 8px;">
                    <span style="background: #3498db; color: white; border-radius: 50%; width: 20px; height: 20px; 
                                 display: flex; align-items: center; justify-content: center; font-size: 12px; 
                                 margin-right: 10px; flex-shrink: 0;">{i}</span>
                    <div style="flex: 1;">{formatted_fix}</div>
                </div>
            """)
        
        section_html = f"""
        <div style="margin-bottom: 16px;">
            <h4 style="margin: 0 0 12px 0; color: #27ae60;">💡 Suggested Fixes</h4>
            <div style="background: #f0f9f0; border: 1px solid #c3e6cb; border-radius: 4px; padding: 12px;">
                {''.join(fixes_html)}
            </div>
        </div>
        """
        
        return ReportSection("fixes", section_html, 3, "solutions")
    
    def _create_confidence_section(self, analysis: Dict[str, Any], metadata: Dict[str, Any]) -> ReportSection:
        """Create confidence and performance metrics section"""
        
        confidence = analysis.get("confidence", 0)
        tokens_used = metadata.get("tokens_used", 0)
        analysis_time = metadata.get("analysis_time", "unknown")
        cached = metadata.get("cached", False)
        
        confidence_level = self._get_confidence_level(confidence)
        confidence_bar_color = self.confidence_colors[confidence_level]
        
        section_html = f"""
        <div style="margin-bottom: 16px;">
            <h4 style="margin: 0 0 12px 0; color: #8e44ad;">📊 Analysis Metrics</h4>
            <div style="background: #faf9fb; border: 1px solid #e1d8e8; border-radius: 4px; padding: 12px;">
                <div style="margin-bottom: 8px;">
                    <strong>Confidence Level:</strong>
                    <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin: 4px 0; overflow: hidden;">
                        <div style="background: {confidence_bar_color}; height: 100%; width: {confidence}%; transition: width 0.3s;"></div>
                    </div>
                    <span style="font-size: 12px; color: #6c757d;">{confidence}% ({confidence_level} confidence)</span>
                </div>
                <div style="display: flex; gap: 16px; font-size: 14px; margin-top: 8px;">
                    <span><strong>Tokens:</strong> {tokens_used}</span>
                    <span><strong>Time:</strong> {analysis_time}</span>
                    <span><strong>Cached:</strong> {'Yes' if cached else 'No'}</span>
                </div>
            </div>
        </div>
        """
        
        return ReportSection("confidence", section_html, 4, "metrics")
    
    def _create_error_details_section(self, context: Dict[str, Any]) -> ReportSection:
        """Create error details section"""
        
        error_info = context.get("error_info", {})
        exit_code = error_info.get("exit_code", "unknown")
        command = error_info.get("command", "unknown")
        error_category = error_info.get("error_category", "unknown")
        
        # Format command for display (truncate if too long)
        display_command = command
        if len(command) > 100:
            display_command = command[:97] + "..."
        
        section_html = f"""
        <div style="margin-bottom: 16px;">
            <h4 style="margin: 0 0 12px 0; color: #e67e22;">📋 Error Details</h4>
            <div style="background: #fef8f1; border: 1px solid #fdeaa7; border-radius: 4px; padding: 12px;">
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: 14px;">
                    <strong>Exit Code:</strong>
                    <span style="background: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; font-family: monospace;">
                        {exit_code}
                    </span>
                    
                    <strong>Category:</strong>
                    <span style="background: #3498db; color: white; padding: 2px 6px; border-radius: 3px;">
                        {error_category}
                    </span>
                    
                    <strong>Command:</strong>
                    <code style="background: #f8f9fa; padding: 4px 6px; border-radius: 3px; font-size: 12px; word-break: break-all;">
                        {html.escape(display_command)}
                    </code>
                </div>
            </div>
        </div>
        """
        
        return ReportSection("error_details", section_html, 5, "details")
    
    def _create_build_context_section(self, context: Dict[str, Any]) -> ReportSection:
        """Create collapsible build context section"""
        
        build_info = context.get("build_info", {})
        git_info = context.get("git_info", {})
        pipeline_info = context.get("pipeline_info", {})
        
        context_id = f"build-context-{int(datetime.now().timestamp())}"
        
        section_html = f"""
        <div style="margin-bottom: 16px;">
            <details style="border: 1px solid #dee2e6; border-radius: 4px; background: #f8f9fa;">
                <summary style="padding: 12px; cursor: pointer; font-weight: bold; color: #495057;">
                    🏗️ Build Context
                </summary>
                <div style="padding: 12px; border-top: 1px solid #dee2e6; background: white;">
                    <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 16px; font-size: 14px;">
                        <strong>Pipeline:</strong>
                        <span>{html.escape(str(pipeline_info.get('pipeline_name', 'unknown')))}</span>
                        
                        <strong>Build:</strong>
                        <span>#{build_info.get('build_number', 'unknown')}</span>
                        
                        <strong>Branch:</strong>
                        <span>{html.escape(str(git_info.get('branch', 'unknown')))}</span>
                        
                        <strong>Commit:</strong>
                        <span style="font-family: monospace;">{html.escape(str(git_info.get('commit', 'unknown'))[:12])}</span>
                        
                        <strong>Author:</strong>
                        <span>{html.escape(str(git_info.get('author', 'unknown')))}</span>
                        
                        <strong>Step:</strong>
                        <span>{html.escape(str(build_info.get('step_key', 'unknown')))}</span>
                    </div>
                </div>
            </details>
        </div>
        """
        
        return ReportSection("build_context", section_html, 6, "context")
    
    def _combine_sections(self, sections: List[ReportSection]) -> str:
        """Combine all sections into final HTML"""
        
        # Sort sections by priority
        sections.sort(key=lambda x: x.priority)
        
        # Combine section content
        combined_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5;">
            {''.join(section.content for section in sections)}
            <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; text-align: center;">
                Generated by AI Error Analysis Plugin • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
            </div>
        </div>
        """
        
        return combined_html
    
    def _create_error_report(self, error_message: str) -> str:
        """Create an error report when report generation fails"""
        
        return f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="border-left: 4px solid #e74c3c; padding-left: 12px; background: #fdf2f2; padding: 12px; border-radius: 4px;">
                <h3 style="margin: 0; color: #c0392b;">❌ Report Generation Failed</h3>
                <p style="margin: 8px 0 0 0; color: #721c24;">
                    {html.escape(error_message)}
                </p>
                <p style="margin: 8px 0 0 0; font-size: 14px; color: #6c757d;">
                    Please review the error logs manually or contact your DevOps team.
                </p>
            </div>
        </div>
        """
    
    def _get_confidence_level(self, confidence: int) -> str:
        """Determine confidence level from confidence score"""
        if confidence >= self.confidence_thresholds["high"]:
            return "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            return "medium"
        else:
            return "low"
    
    def _format_text_with_emphasis(self, text: str) -> str:
        """Format text with basic emphasis (bold, code, etc.)"""
        # Simple formatting - could be enhanced
        
        # Bold text: **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
        
        # Inline code: `code`
        text = re.sub(r'`([^`]+)`', r'<code style="background: #f1f2f6; padding: 1px 4px; border-radius: 2px;">\1</code>', text)
        
        # Line breaks
        text = text.replace('\n', '<br>')
        
        return text
    
    def _generate_recommendations(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate additional recommendations based on analysis"""
        
        recommendations = []
        error_category = context.get("error_info", {}).get("error_category", "unknown")
        confidence = analysis.get("confidence", 0)
        
        # Category-specific recommendations
        if error_category == "compilation":
            recommendations.append("Consider setting up pre-commit hooks to catch compilation errors earlier")
            recommendations.append("Review code style and linting rules to prevent syntax errors")
        
        elif error_category == "test_failure":
            recommendations.append("Implement test-driven development practices")
            recommendations.append("Consider adding more comprehensive test coverage")
        
        elif error_category == "dependency":
            recommendations.append("Pin dependency versions to avoid unexpected updates")
            recommendations.append("Use dependency scanning tools to identify vulnerabilities")
        
        elif error_category == "network":
            recommendations.append("Implement retry logic for network operations")
            recommendations.append("Add network connectivity checks in your build process")
        
        # Confidence-based recommendations
        if confidence < 50:
            recommendations.append("Consider providing more detailed error logs for better analysis")
            recommendations.append("Review the error manually for additional context")
        
        return recommendations
    
    def _generate_next_steps(self, analysis: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """Generate suggested next steps"""
        
        next_steps = []
        severity = analysis.get("severity", "medium")
        
        if severity == "high":
            next_steps.extend([
                "Address this issue immediately as it's blocking the build",
                "Consider reverting recent changes if the fix is not immediately obvious",
                "Escalate to senior team members if needed"
            ])
        
        elif severity == "medium":
            next_steps.extend([
                "Investigate and fix within the current development cycle",
                "Review related code changes for potential side effects",
                "Update documentation if configuration changes are needed"
            ])
        
        else:  # low severity
            next_steps.extend([
                "Schedule fix in upcoming sprint or maintenance window",
                "Consider if this is an acceptable known issue",
                "Document the issue for future reference"
            ])
        
        # Always include these general steps
        next_steps.extend([
            "Review the suggested fixes above",
            "Test the fix in a development environment first",
            "Consider adding tests to prevent regression"
        ])
        
        return next_steps


def main():
    """Main entry point for report generator"""
    
    if len(sys.argv) < 3:
        print("Usage: report_generator.py <analysis_result_file> <context_file> [html|json|markdown] [include_confidence]", file=sys.stderr)
        sys.exit(1)
    
    analysis_file = sys.argv[1]
    context_file = sys.argv[2]
    output_format = sys.argv[3] if len(sys.argv) > 3 else "html"
    include_confidence = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else True
    
    try:
        # Load analysis result
        with open(analysis_file, 'r') as f:
            analysis_result = json.load(f)
        
        # Load context
        with open(context_file, 'r') as f:
            context = json.load(f)
        
        # Generate report
        generator = ReportGenerator()
        
        if output_format == "html":
            report = generator.generate_html_report(analysis_result, context, include_confidence)
        elif output_format == "json":
            report = generator.generate_json_report(analysis_result, context)
            report = json.dumps(report, indent=2, default=str)
        elif output_format == "markdown":
            report = generator.generate_markdown_report(analysis_result, context)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        print(report)
        
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        
        # Generate error report
        generator = ReportGenerator()
        error_report = generator._create_error_report(f"Report generation failed: {str(e)}")
        
        if output_format == "json":
            error_data = {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
            print(json.dumps(error_data, indent=2))
        else:
            print(error_report)
        
        sys.exit(1)


if __name__ == "__main__":
    main()