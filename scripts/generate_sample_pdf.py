"""
Script to generate a realistic 10-page HR Policy PDF document for AeroqAI tests & demos.
Uses reportlab to generate clean formatting.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_sample_hr_pdf(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=15
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=10
    )

    story = []

    pages_data = [
        {
            "title": "Global Tech Inc. — Corporate HR Policy Handbook",
            "section": "Section 1: General Provisions & Employment Categories",
            "text": """Welcome to Global Tech Inc. This Employee Handbook outlines the core policies, expectations, and benefits governing all full-time, part-time, and contract employees worldwide.
            
            1.1 Equal Employment Opportunity: Global Tech Inc. provides equal employment opportunities to all employees and applicants without regard to race, color, religion, sex, national origin, age, disability, or genetics.
            
            1.2 Employment Classifications:
            - Full-Time Employees: Regularly scheduled to work 40 hours per week. Eligible for full company benefit packages.
            - Part-Time Employees: Scheduled to work fewer than 30 hours per week. Benefits are prorated based on hours worked.
            - Contractors & Consultants: Independent personnel bound by specific service agreements; not eligible for internal corporate benefits."""
        },
        {
            "title": "Working Hours & Hybrid Remote Policy",
            "section": "Section 2: Work Schedules & Flexible Operations",
            "text": """Global Tech Inc. operates on a flexible hybrid work model designed to balance operational efficiency and employee wellness.
            
            2.1 Core Hours: Core operational hours are 10:00 AM to 4:00 PM EST. All full-time employees are expected to be available for synchronous communication during core hours.
            
            2.2 Hybrid Remote Work Guidelines:
            - Employees may work remotely up to 3 days per week with prior manager approval.
            - Team members must work from an approved office location or verified home workspace with secure internet.
            - High-speed internet (minimum 50 Mbps download speed) is mandatory for remote workers."""
        },
        {
            "title": "Paid Time Off (PTO) & Leave Rules",
            "section": "Section 3: Annual Leave, Sick Days & Holidays",
            "text": """We believe rest and recovery are critical for sustained productivity and personal health.
            
            3.1 Annual Leave Allowance:
            - Standard full-time employees receive 20 days of paid annual leave per calendar year.
            - Senior staff (5+ years tenure) receive 25 days of paid annual leave per calendar year.
            
            3.2 Sick & Personal Leave: Employees receive 10 paid sick/personal days annually. Unused sick leave does not roll over to subsequent calendar years.
            
            3.3 Parental Leave: Primary caregivers are eligible for 16 weeks of fully paid parental leave following the birth or adoption of a child. Secondary caregivers receive 6 weeks of paid leave."""
        },
        {
            "title": "Health Insurance & Medical Benefits",
            "section": "Section 4: Comprehensive Healthcare Coverage",
            "text": """Global Tech Inc. offers premium medical, dental, and vision insurance coverage to all full-time team members starting on their first day of employment.
            
            4.1 Health Insurance Plans:
            - Preferred Provider Organization (PPO): 90% company subsidized for employee, 70% for dependents.
            - High Deductible Health Plan (HDHP) with HSA: 100% company subsidized for employee with $1,500 annual HSA contribution.
            
            4.2 Dental & Vision: Full preventive dental cleanings twice per year and annual eye exams covered at 100% under standard company plans."""
        },
        {
            "title": "Equipment, Hardware & Remote Stipends",
            "section": "Section 5: Technology Allowances & Workstation Setup",
            "text": """To ensure high performance, Global Tech Inc. equips every employee with modern hardware and workstation stipends.
            
            5.1 Hardware Allocation: Upon joining, employees receive a high-performance laptop (MacBook Pro 16-inch or Dell XPS 15), 4K external monitor, and noise-canceling headset.
            
            5.2 Work-from-Home Setup Stipend: A one-time $1,000 net stipend is provided to newly hired remote employees for ergonomic desk, chair, or lighting purchases.
            
            5.3 Monthly Internet & Connectivity Allowance: A monthly stipend of $75 is credited directly to payroll to offset home high-speed broadband expenses."""
        },
        {
            "title": "Code of Conduct & Workplace Ethics",
            "section": "Section 6: Professional Standards & Harassment Prevention",
            "text": """Maintaining a safe, inclusive, and ethical work environment is the fundamental responsibility of every Global Tech team member.
            
            6.1 Zero-Tolerance Anti-Harassment Policy: Discrimination, harassment, or bullying of any kind based on protected attributes is strictly prohibited and subject to immediate termination.
            
            6.2 Whistleblower Protection: Employees who report compliance violations, fraud, or unethical behavior in good faith are fully protected from retaliation or adverse action.
            
            6.3 Social Media Guidelines: When representing the company online, employees must clearly disclose personal opinions and refrain from posting confidential client or corporate data."""
        },
        {
            "title": "Performance Reviews & Career Progression",
            "section": "Section 7: Performance Management & Salary Reviews",
            "text": """Fair evaluation and continuous feedback foster individual career growth and organizational success.
            
            7.1 Bi-Annual Performance Cadence: Formal performance evaluations occur twice per year: Mid-Year Review in July and End-of-Year Review in December.
            
            7.2 Annual Compensation Adjustment: Merit-based salary increases and annual bonus distributions are tied directly to End-of-Year performance ratings.
            
            7.3 Promotion Criteria: Promotions require at least 12 months in current role, consistent 'Exceeds Expectations' rating, and leadership approval."""
        },
        {
            "title": "Learning & Development Stipends",
            "section": "Section 8: Professional Growth & Tuition Reimbursement",
            "text": """Global Tech Inc. invests in continuous skill enhancement and education for all staff members.
            
            8.1 Annual Learning Stipend: Every full-time employee is allocated a $2,500 annual budget for attending technical conferences, purchasing books, or enrolling in certified online courses.
            
            8.2 Tuition Assistance Program: Up to $5,000 per year is available for approved degree programs related to the employee's current or future career track within Global Tech Inc."""
        },
        {
            "title": "Data Security & Confidentiality",
            "section": "Section 9: Information Security & Non-Disclosure",
            "text": """Protecting corporate assets, proprietary algorithms, and customer privacy is paramount.
            
            9.1 Non-Disclosure Obligations: All proprietary code, AI model weights, internal customer metrics, and evaluation datasets created during employment belong exclusively to Global Tech Inc.
            
            9.2 Security Hygiene: Passwords must be updated every 90 days. Multi-Factor Authentication (MFA) is compulsory across all corporate accounts and developer tools."""
        },
        {
            "title": "Separation, Resignation & Severance Guidelines",
            "section": "Section 10: Offboarding Procedures & Termination Notice",
            "text": """Fair and transparent procedures govern employment conclusion at Global Tech Inc.
            
            10.1 Notice Period: Employees initiating resignation must provide at least 2 weeks (14 days) written notice to their direct supervisor and HR representative.
            
            10.2 Return of Company Assets: All laptops, security keycards, monitors, and proprietary materials must be returned within 5 business days of the final active work date.
            
            10.3 Severance Eligibility: Eligible staff separated due to redundancy or corporate restructuring receive 2 weeks severance pay per completed year of service, up to a maximum of 26 weeks."""
        }
    ]

    for idx, page_info in enumerate(pages_data):
        story.append(Paragraph(page_info["title"], title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(page_info["section"], heading_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(page_info["text"], body_style))
        
        # Add PageBreak between pages (except last page)
        if idx < len(pages_data) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"[SUCCESS] Sample 10-page HR Policy PDF created at: '{output_path}'")


if __name__ == "__main__":
    pdf_file = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    create_sample_hr_pdf(pdf_file)
