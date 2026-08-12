"""
DataVista+ Report Engine
PDF, Excel, and CSV report generation for business intelligence
"""
import os
import io
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

import pandas as pd
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportEngine:
    """Generate professional reports in PDF, Excel, and CSV formats."""

    def __init__(self):
        self.reports_dir = settings.REPORTS_DIR
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_pdf(
        self,
        title: str,
        sections: List[Dict[str, Any]],
        report_id: int,
    ) -> str:
        """
        Generate a PDF report using ReportLab.
        sections: [{"heading": str, "content": str, "data": list}]
        Returns the file path.
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer,
                Table, TableStyle, HRFlowable, PageBreak
            )

            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(self.reports_dir, filename)

            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=1 * inch,
                bottomMargin=1 * inch,
            )

            styles = getSampleStyleSheet()
            # Custom styles
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=24,
                textColor=colors.HexColor("#6C63FF"),
                spaceAfter=12,
            )
            heading_style = ParagraphStyle(
                "CustomHeading",
                parent=styles["Heading2"],
                fontSize=14,
                textColor=colors.HexColor("#2D3748"),
                spaceBefore=16,
                spaceAfter=8,
            )
            body_style = ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#4A5568"),
                spaceAfter=6,
            )

            story = []

            # Header
            story.append(Paragraph("DataVista+", ParagraphStyle(
                "Brand", parent=styles["Normal"], fontSize=10,
                textColor=colors.HexColor("#A0AEC0")
            )))
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(
                f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                ParagraphStyle("Date", parent=styles["Normal"], fontSize=9, textColor=colors.gray)
            ))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#6C63FF")))
            story.append(Spacer(1, 0.2 * inch))

            # Sections
            for section in sections:
                story.append(Paragraph(section.get("heading", ""), heading_style))

                if section.get("content"):
                    story.append(Paragraph(section["content"], body_style))
                    story.append(Spacer(1, 0.1 * inch))

                if section.get("data") and isinstance(section["data"], list) and len(section["data"]) > 0:
                    df_data = section["data"]
                    if isinstance(df_data[0], dict):
                        headers = list(df_data[0].keys())
                        table_data = [headers] + [[str(row.get(h, "")) for h in headers] for row in df_data[:20]]

                        col_widths = [6 * inch / len(headers)] * len(headers)
                        t = Table(table_data, colWidths=col_widths, repeatRows=1)
                        t.setStyle(TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6C63FF")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F7FF")]),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("ROWHEIGHT", (0, 0), (-1, -1), 18),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 0.15 * inch))

            # Footer
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
            story.append(Paragraph(
                "Confidential — Generated by DataVista+ AI Decision Intelligence Platform",
                ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.gray, alignment=1)
            ))

            doc.build(story)
            logger.info(f"PDF report generated: {filepath}")
            return filepath

        except ImportError:
            logger.warning("ReportLab not installed. Falling back to text report.")
            return self._generate_text_report(title, sections, report_id)
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise

    def generate_excel(
        self,
        title: str,
        sheets: List[Dict[str, Any]],
        report_id: int,
    ) -> str:
        """
        Generate an Excel report with multiple sheets.
        sheets: [{"name": str, "data": list_of_dicts, "summary": str}]
        Returns the file path.
        """
        filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(self.reports_dir, filename)

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            for sheet in sheets:
                sheet_name = sheet.get("name", "Sheet1")[:31]  # Excel sheet name limit
                data = sheet.get("data", [])

                if data and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                else:
                    df = pd.DataFrame({"Summary": [sheet.get("summary", "No data")]})

                df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=2)

                # Style the sheet
                worksheet = writer.sheets[sheet_name]
                worksheet["A1"] = title
                worksheet["A1"].font = __import__("openpyxl").styles.Font(bold=True, size=14, color="6C63FF")
                worksheet["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                # Auto-fit columns
                for col in worksheet.columns:
                    max_len = max((len(str(cell.value)) for cell in col if cell.value), default=12)
                    worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        logger.info(f"Excel report generated: {filepath}")
        return filepath

    def generate_csv(
        self,
        data: List[Dict],
        report_id: int,
        filename_prefix: str = "export",
    ) -> str:
        """Generate a CSV export."""
        filename = f"{filename_prefix}_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.reports_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.info(f"CSV export generated: {filepath}")
        return filepath

    def generate_business_summary(
        self,
        kpis: List[Dict],
        insights: List[Dict],
        recommendations: List[Dict],
        report_id: int,
    ) -> str:
        """Generate a complete business summary PDF."""
        sections = [
            {
                "heading": "Executive Summary",
                "content": (
                    f"This report summarizes key business performance indicators and AI-generated insights. "
                    f"A total of {len(insights)} insights and {len(recommendations)} recommendations have been identified. "
                    f"The analysis covers {len(kpis)} key performance indicators."
                ),
            },
            {
                "heading": "Key Performance Indicators",
                "data": kpis,
            },
            {
                "heading": "AI-Generated Business Insights",
                "data": [
                    {
                        "Title": ins.get("title", ""),
                        "Type": ins.get("type", "").title(),
                        "Impact": ins.get("impact_level", "").title(),
                        "Confidence": f"{int(ins.get('confidence_score', 0) * 100)}%",
                    }
                    for ins in insights[:10]
                ],
            },
            {
                "heading": "Recommendations",
                "data": [
                    {
                        "Priority": rec.get("priority", ""),
                        "Title": rec.get("title", ""),
                        "Expected Impact": rec.get("expected_impact", ""),
                    }
                    for rec in recommendations[:5]
                ],
            },
        ]

        return self.generate_pdf("Business Intelligence Summary Report", sections, report_id)

    def _generate_text_report(self, title: str, sections: List[Dict], report_id: int) -> str:
        """Fallback plain-text report when ReportLab is unavailable."""
        filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(self.reports_dir, filename)
        lines = [
            "=" * 60,
            f"  {title}",
            f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60, "",
        ]
        for section in sections:
            lines.append(f"\n{'─' * 40}")
            lines.append(f"  {section.get('heading', '')}")
            lines.append(f"{'─' * 40}")
            if section.get("content"):
                lines.append(section["content"])
        lines.append("\n" + "=" * 60)
        lines.append("  Confidential — DataVista+ Platform")
        lines.append("=" * 60)
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        return filepath
