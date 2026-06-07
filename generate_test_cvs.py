from __future__ import annotations
import os
from fpdf import FPDF

OUTPUT_DIR = "test_cvs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

JOB_OFFER = (
    "We are looking for a Senior AI/ML Engineer with 5+ years of experience to join our product team. "
    "We seek someone with proven experience in Python, machine learning (scikit-learn, PyTorch or TensorFlow), "
    "data processing with Pandas and SQL, model deployment with Docker and REST APIs (FastAPI or Flask). "
    "Knowledge of MLOps (MLflow, Airflow), cloud deployment (AWS/GCP) and CI/CD pipelines is valued. "
    "Communication and teamwork skills are essential. Experience in NLP and LLMs is a plus."
)

profiles = [
    {
        "filename": "elena_martin_ml.pdf",
        "name": "Elena Martín Ruiz",
        "email": "elena.martin@email.com",
        "years": 7,
        "techs": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "FastAPI", "Docker", "AWS", "Pandas", "SQL", "MLflow"],
        "experience": [
            ("Senior ML Engineer", "AITech Solutions", "2022-2026",
             "Led development of NLP models for text classification using PyTorch and Transformers. Model deployment with FastAPI and Docker on AWS ECS. MLOps pipelines with MLflow and Airflow."),
            ("ML Engineer", "DataInnovate", "2020-2022",
             "Trained classification models with scikit-learn and XGBoost. Feature engineering with Pandas and SQL. Inference APIs with Flask."),
            ("Data Scientist", "StartupML", "2018-2020",
             "Exploratory data analysis. Regression and clustering models. Pipeline automation with Airflow."),
        ],
        "education": "MSc in Artificial Intelligence — Universidad Politécnica de Madrid",
        "certifications": ["AWS Machine Learning Specialty", "TensorFlow Developer Certificate"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "miguel_angel_dl.pdf",
        "name": "Miguel Ángel Torres",
        "email": "miguel.torres@email.com",
        "years": 6,
        "techs": ["Python", "PyTorch", "scikit-learn", "Pandas", "FastAPI", "Docker", "Kubernetes", "GCP", "SQL"],
        "experience": [
            ("AI Engineer", "CloudML Corp", "2021-2026",
             "Developed deep learning models for computer vision with PyTorch. Inference APIs with FastAPI. Deployment on GKE with Docker and Kubernetes."),
            ("Backend/ML Engineer", "TechFlow", "2019-2021",
             "Implemented Python microservices with FastAPI. Integrated ML models into production. PostgreSQL databases."),
        ],
        "education": "BSc in Computer Science — Universidad de Barcelona",
        "certifications": ["Google Cloud Professional ML Engineer", "PyTorch Scholarship"],
        "languages": ["Spanish (native)", "English C1", "Catalan (native)"],
    },
    {
        "filename": "lucia_garcia_ds.pdf",
        "name": "Lucía García Navarro",
        "email": "lucia.garcia@email.com",
        "years": 5,
        "techs": ["Python", "R", "scikit-learn", "Pandas", "NumPy", "SQL", "TensorFlow", "Tableau", "Airflow"],
        "experience": [
            ("Data Scientist", "FinAnalytics", "2022-2026",
             "Predictive models with scikit-learn and TensorFlow for fraud detection. ETL pipelines with Airflow. Dashboards with Tableau."),
            ("Junior Data Scientist", "DataLab", "2020-2022",
             "Data analysis with Pandas and SQL. Regression and classification models. Results visualization."),
        ],
        "education": "MSc in Data Science — Universidad Carlos III",
        "certifications": ["DataCamp ML Scientist Track"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "david_gomez_mlops.pdf",
        "name": "David Gómez López",
        "email": "david.gomez@email.com",
        "years": 5,
        "techs": ["Python", "MLflow", "Airflow", "Docker", "Kubernetes", "AWS", "Pandas", "SQL", "scikit-learn", "FastAPI"],
        "experience": [
            ("MLOps Engineer", "DataPlatform Inc", "2022-2026",
             "Implemented MLOps infrastructure with MLflow and Airflow. Automated training and deployment pipelines. Inference APIs with FastAPI."),
            ("Data Engineer", "BigDataCorp", "2020-2022",
             "Built ETL pipelines with Airflow and Spark. AWS infrastructure. SQL and NoSQL data modeling."),
        ],
        "education": "BSc in Systems Engineering — Universidad de Valencia",
        "certifications": ["AWS Certified Data Analytics", "Docker Certified Associate"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "alba_jimenez_python.pdf",
        "name": "Alba Jiménez Fernández",
        "email": "alba.jimenez@email.com",
        "years": 4,
        "techs": ["Python", "Django", "Flask", "PostgreSQL", "Docker", "Redis", "scikit-learn", "Pandas", "GitHub Actions"],
        "experience": [
            ("Python Developer", "BackendPro", "2022-2026",
             "Developed REST APIs with Django and Flask. Integrated basic ML models with scikit-learn. Deployment with Docker and CI/CD with GitHub Actions."),
            ("Junior Python Developer", "CodeFactory", "2020-2022",
             "Backend development with Django. PostgreSQL database maintenance. Task automation with Python scripts."),
        ],
        "education": "BSc in Computer Science — Universidad de Málaga",
        "certifications": ["Python Institute PCEP"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "jorge_romo_devops.pdf",
        "name": "Jorge Romo Sánchez",
        "email": "jorge.romo@email.com",
        "years": 8,
        "techs": ["Docker", "Kubernetes", "Terraform", "Ansible", "AWS", "Linux", "Bash", "Jenkins", "Prometheus", "Grafana"],
        "experience": [
            ("DevOps Engineer", "CloudHost", "2019-2026",
             "Managed Kubernetes clusters on AWS EKS. Infrastructure as code with Terraform. CI/CD pipelines with Jenkins."),
            ("DevOps Junior", "HostingSolutions", "2016-2019",
             "Linux server administration. Automation with Ansible. Monitoring with Prometheus and Grafana."),
        ],
        "education": "BSc in Systems Administration — Universidad de Salamanca",
        "certifications": ["AWS DevOps Engineer", "CKA"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "patricia_lara_frontend.pdf",
        "name": "Patricia Lara Ortega",
        "email": "patricia.lara@email.com",
        "years": 4,
        "techs": ["JavaScript", "TypeScript", "React", "Next.js", "Tailwind", "CSS", "Jest", "GraphQL"],
        "experience": [
            ("Frontend Developer", "WebStudio", "2022-2026",
             "Developed web applications with React and Next.js. Implemented responsive designs with Tailwind CSS. Testing with Jest."),
            ("Junior Frontend", "DigitalAgency", "2020-2022",
             "HTML/CSS web layout. React component development. REST API integration."),
        ],
        "education": "BSc in Web Development — Universidad de Alicante",
        "certifications": [],
        "languages": ["Spanish (native)", "English B1"],
    },
    {
        "filename": "ramon_ortiz_pm.pdf",
        "name": "Ramón Ortiz Castro",
        "email": "ramon.ortiz@email.com",
        "years": 10,
        "techs": ["Jira", "Confluence", "Scrum", "Agile", "Microsoft Project", "Excel", "Basic SQL"],
        "experience": [
            ("IT Project Manager", "GlobalTech", "2018-2026",
             "Managed development teams with Agile methodologies. Sprint planning with Jira. Stakeholder coordination."),
            ("Product Owner", "SaaSCorp", "2015-2018",
             "Product roadmap definition. Backlog management. Scrum ceremony facilitation."),
        ],
        "education": "MBA in Technology Management — IE Business School",
        "certifications": ["PMP", "PSM I", "ITIL Foundation"],
        "languages": ["Spanish (native)", "English C1"],
    },
    {
        "filename": "nuria_serrano_hr.pdf",
        "name": "Nuria Serrano Molina",
        "email": "nuria.serrano@email.com",
        "years": 6,
        "techs": ["LinkedIn Recruiter", "ATS (Greenhouse)", "Excel", "PowerPoint", "Basic Tableau", "Basic Python"],
        "experience": [
            ("Technical Recruiter", "PeopleFirst HR", "2020-2026",
             "Recruiting tech profiles. CV screening and interview coordination. ATS and LinkedIn Recruiter usage."),
            ("HR Generalist", "BusinessCorp", "2018-2020",
             "Payroll and hiring management. New employee onboarding. Excel reporting."),
        ],
        "education": "BSc in Labor Relations — Universidad de Granada",
        "certifications": ["LinkedIn Certified Recruiter"],
        "languages": ["Spanish (native)", "English B2"],
    },
    {
        "filename": "sergio_castro_cloud.pdf",
        "name": "Sergio Castro Vega",
        "email": "sergio.castro@email.com",
        "years": 7,
        "techs": ["Python", "AWS", "GCP", "Docker", "Terraform", "PostgreSQL", "Pandas", "scikit-learn", "Airflow", "Bash"],
        "experience": [
            ("Cloud/Data Engineer", "CloudScale", "2021-2026",
             "Data architecture on AWS (S3, Redshift, EMR). Basic ML models with scikit-learn. ETL pipelines with Airflow on GCP."),
            ("Data Engineer", "BigAnalytics", "2019-2021",
             "Built data warehouses on AWS Redshift. Python scripts for data transformation. REST API integration."),
        ],
        "education": "BSc in Computer Science — Universidad de Zaragoza",
        "certifications": ["AWS Solutions Architect Associate", "GCP Data Engineer"],
        "languages": ["Spanish (native)", "English C1", "German B1"],
    },
]


def generate_pdf(profile: dict) -> bytes:
    pdf = FPDF()
    pdf.add_font("DejaVu", "", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", uni=True)
    pdf.add_page()

    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 14, profile["name"], new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, f"Email: {profile['email']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Years of experience: {profile['years']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Technical Profile", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, " | ".join(profile["techs"]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Professional Experience", new_x="LMARGIN", new_y="NEXT")
    for role, company, years, desc in profile["experience"]:
        pdf.set_font("DejaVu", "B", 11)
        pdf.cell(0, 7, f"{role} — {company} ({years})", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(2)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Education", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    pdf.cell(0, 6, profile["education"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    if profile["certifications"]:
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 10, "Certifications", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        for cert in profile["certifications"]:
            pdf.cell(0, 6, f"- {cert}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.set_font("DejaVu", "B", 13)
    pdf.cell(0, 10, "Languages", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 10)
    for lang in profile["languages"]:
        pdf.cell(0, 6, f"- {lang}", new_x="LMARGIN", new_y="NEXT")

    return pdf.output()


if __name__ == "__main__":
    print("=" * 72)
    print("JOB OFFER FOR TESTING")
    print("=" * 72)
    print()
    print(JOB_OFFER)
    print()
    print("=" * 72)
    print("GENERATING TEST CVs")
    print("=" * 72)
    print()

    for p in profiles:
        path = os.path.join(OUTPUT_DIR, p["filename"])
        content = generate_pdf(p)
        with open(path, "wb") as f:
            f.write(content)
        size_kb = len(content) / 1024
        print(f"  {p['filename']:35s}  {p['name']:25s}  {p['years']} years  {len(p['techs'])} techs  ({size_kb:.1f} KB)")

    print(f"\nGenerated {len(profiles)} PDFs in ./{OUTPUT_DIR}/")
    print()
    print("STEPS FOR TESTING:")
    print("  1. Start the server: python main.py")
    print("  2. Open http://localhost:8000")
    print("  3. Go to the 'Offers' tab")
    print("  4. Create a new offer with title 'Senior AI/ML Engineer'")
    print("  5. Paste the job offer text above into the description")
    print("  6. Upload the 10 generated CVs")
    print("  7. Wait for processing and review the ranking")
